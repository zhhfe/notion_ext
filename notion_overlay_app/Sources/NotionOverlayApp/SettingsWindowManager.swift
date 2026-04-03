import AppKit
import SwiftUI

@MainActor
final class SettingsWindowManager {
    private var window: NSWindow?

    func show(settings: SettingsStore, appState: OverlayAppState) {
        if window == nil {
            AppLogger.shared.log("SettingsWindow create")
            let settingsView = AnyView(
                SettingsView()
                    .environmentObject(settings)
                    .environmentObject(appState)
            )

            let host = NSHostingView(rootView: settingsView)
            let win = NSWindow(
                contentRect: NSRect(x: 280, y: 220, width: 620, height: 700),
                styleMask: [.titled, .closable, .miniaturizable, .resizable],
                backing: .buffered,
                defer: false
            )
            win.title = "Notion Overlay 设置"
            win.isReleasedWhenClosed = false
            win.center()
            win.contentView = host
            window = win
        } else if let host = window?.contentView as? NSHostingView<AnyView> {
            host.rootView = AnyView(
                SettingsView()
                    .environmentObject(settings)
                    .environmentObject(appState)
            )
        }

        AppLogger.shared.log("SettingsWindow show")
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
    }
}
