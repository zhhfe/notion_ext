import EventKit
import Foundation

@MainActor
final class RemindersPermissionManager {
    private var hasRequested = false

    func requestIfNeeded() async {
        guard !hasRequested else { return }
        hasRequested = true

        let status = EKEventStore.authorizationStatus(for: .reminder)
        AppLogger.shared.log("Reminders auth status before request: \(status.rawValue)")

        guard status == .notDetermined else {
            return
        }

        let store = EKEventStore()
        do {
            let granted: Bool
            if #available(macOS 14.0, *) {
                granted = try await store.requestFullAccessToReminders()
            } else {
                granted = try await withCheckedThrowingContinuation { cont in
                    store.requestAccess(to: .reminder) { ok, error in
                        if let error {
                            cont.resume(throwing: error)
                        } else {
                            cont.resume(returning: ok)
                        }
                    }
                }
            }
            AppLogger.shared.log("Reminders permission request result: \(granted)")
        } catch {
            AppLogger.shared.log("Reminders permission request failed: \(error.localizedDescription)")
        }
    }
}
