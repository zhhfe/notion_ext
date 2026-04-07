import EventKit
import Foundation

/// 输出与旧版 JXA 脚本兼容的 JSON，供 Python `notion_ext.report.reminders` 解析。
@main
enum CLI {
    private static func currentAuthorizationStatus() -> EKAuthorizationStatus {
        EKEventStore.authorizationStatus(for: .reminder)
    }

    private static func hasAccess(_ status: EKAuthorizationStatus) -> Bool {
        if #available(macOS 14.0, *) {
            return status == .fullAccess
        }
        return status == .authorized
    }

    private static func requestAccess(store: EKEventStore) async -> Bool {
        if #available(macOS 14.0, *) {
            return await withCheckedContinuation { (cont: CheckedContinuation<Bool, Never>) in
                store.requestFullAccessToReminders { ok, _ in
                    cont.resume(returning: ok)
                }
            }
        }
        return await withCheckedContinuation { (cont: CheckedContinuation<Bool, Never>) in
            store.requestAccess(to: .reminder) { ok, _ in
                cont.resume(returning: ok)
            }
        }
    }

    private static func setReminderCompleted(by identifier: String, completed: Bool, store: EKEventStore) {
        guard let item = store.calendarItem(withIdentifier: identifier) as? EKReminder else {
            fputs("read_reminders_cli: 未找到 identifier=\(identifier) 的提醒事项\n", stderr)
            exit(2)
        }

        if item.isCompleted == completed {
            print("{\"ok\":true,\"no_change\":true}")
            return
        }

        item.isCompleted = completed
        item.completionDate = completed ? Date() : nil
        do {
            try store.save(item, commit: true)
            print("{\"ok\":true}")
        } catch {
            fputs("read_reminders_cli: 标记完成失败: \(error)\n", stderr)
            exit(1)
        }
    }

    static func main() async {
        let store = EKEventStore()
        let status = currentAuthorizationStatus()
        let granted: Bool
        if hasAccess(status) {
            granted = true
        } else if status == .notDetermined {
            granted = await requestAccess(store: store)
        } else {
            granted = false
        }

        guard granted else {
            fputs("read_reminders_cli: 未获得「提醒事项」访问权限\n", stderr)
            exit(1)
        }

        let args = CommandLine.arguments
        if args.count == 3, args[1] == "--complete" {
            setReminderCompleted(by: args[2], completed: true, store: store)
            return
        }
        if args.count == 4, args[1] == "--set-completed" {
            let raw = args[3].lowercased()
            let completed = raw == "true" || raw == "1" || raw == "yes"
            setReminderCompleted(by: args[2], completed: completed, store: store)
            return
        }

        let predicate = store.predicateForReminders(in: nil)
        let ekReminders = await withCheckedContinuation { (cont: CheckedContinuation<[EKReminder], Never>) in
            store.fetchReminders(matching: predicate) { list in
                cont.resume(returning: list ?? [])
            }
        }

        var buckets: [String: [ReminderJSON]] = [:]
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime]

        for r in ekReminders {
            let listName = r.calendar?.title ?? ""
            let title = r.title ?? ""
            let body = r.notes ?? ""
            var due: String?
            if let dc = r.dueDateComponents, let date = Calendar.current.date(from: dc) {
                due = iso.string(from: date)
            }
            let item = ReminderJSON(
                id: r.calendarItemIdentifier,
                name: title,
                body: body,
                dueDate: due,
                completed: r.isCompleted,
                priority: r.priority
            )
            buckets[listName, default: []].append(item)
        }

        let listNames = buckets.keys.sorted()
        let lists: [ListJSON] = listNames.map { name in
            ListJSON(name: name, reminders: buckets[name] ?? [])
        }

        let root = RootJSON(lists: lists)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

        do {
            let data = try encoder.encode(root)
            if let s = String(data: data, encoding: .utf8) {
                print(s)
            } else {
                fputs("read_reminders_cli: UTF-8 编码失败\n", stderr)
                exit(1)
            }
        } catch {
            fputs("read_reminders_cli: \(error)\n", stderr)
            exit(1)
        }
    }
}

private struct RootJSON: Encodable {
    let lists: [ListJSON]
}

private struct ListJSON: Encodable {
    let name: String
    let reminders: [ReminderJSON]
}

private struct ReminderJSON: Encodable {
    let id: String
    let name: String
    let body: String
    let dueDate: String?
    let completed: Bool
    let priority: Int
}
