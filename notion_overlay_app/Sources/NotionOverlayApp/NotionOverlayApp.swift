import AppKit
import SwiftUI

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let environment = OverlayEnvironment.shared
    private var didBootstrap = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        AppLogger.shared.log("Application did finish launching")
        NSApplication.shared.setActivationPolicy(.regular)
        environment.appState.menuBarController = MenuBarController(
            appState: environment.appState,
            settings: environment.settings
        )
        environment.appState.menuBarController?.applyVisibility()
        guard !didBootstrap else { return }
        didBootstrap = true
        environment.appState.bootstrap()
    }

    func applicationWillTerminate(_ notification: Notification) {
        AppLogger.shared.log("Application will terminate")
        environment.appState.shutdown()
    }
}

@main
@MainActor
struct NotionOverlayApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    private let environment = OverlayEnvironment.shared

    var body: some Scene {
        Settings {
            SettingsView()
                .environmentObject(environment.settings)
                .environmentObject(environment.appState)
        }
    }
}
