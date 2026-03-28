import EventKit
import Foundation

/// 输出与旧版 JXA 脚本兼容的 JSON，供 Python `notion_ext.report.reminders` 解析。
@main
enum CLI {
    static func main() async {
        let store = EKEventStore()

        let granted: Bool
        if #available(macOS 14.0, *) {
            granted = await withCheckedContinuation { (cont: CheckedContinuation<Bool, Never>) in
                store.requestFullAccessToReminders { ok, _ in
                    cont.resume(returning: ok)
                }
            }
        } else {
            granted = await withCheckedContinuation { (cont: CheckedContinuation<Bool, Never>) in
                store.requestAccess(to: .reminder) { ok, _ in
                    cont.resume(returning: ok)
                }
            }
        }

        guard granted else {
            fputs("read_reminders_cli: 未获得「提醒事项」访问权限\n", stderr)
            exit(1)
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
    let name: String
    let body: String
    let dueDate: String?
    let completed: Bool
    let priority: Int
}
