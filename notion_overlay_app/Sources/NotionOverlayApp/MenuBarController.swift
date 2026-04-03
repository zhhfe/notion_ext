import AppKit

@MainActor
final class MenuBarController: NSObject {
    private var statusItem: NSStatusItem?
    private weak var appState: OverlayAppState?
    private let settings: SettingsStore

    init(appState: OverlayAppState, settings: SettingsStore) {
        self.appState = appState
        self.settings = settings
        super.init()
    }

    func applyVisibility() {
        if settings.keepMenuBarIcon {
            if statusItem == nil {
                let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
                item.button?.image = NSImage(systemSymbolName: "rectangle.stack.badge.person.crop", accessibilityDescription: "Notion Overlay")
                item.button?.imagePosition = .imageOnly
                statusItem = item
            }
            statusItem?.menu = buildMenu()
        } else if let statusItem {
            NSStatusBar.system.removeStatusItem(statusItem)
            self.statusItem = nil
        }
    }

    func refreshMenu() {
        statusItem?.menu = buildMenu()
    }

    private func buildMenu() -> NSMenu {
        let menu = NSMenu()

        let toggleTitle = (appState?.isWindowVisible ?? false) ? "隐藏窗口" : "显示窗口"
        menu.addItem(NSMenuItem(title: toggleTitle, action: #selector(toggleWindow), keyEquivalent: ""))

        let pinTitle = settings.showOnAllSpaces ? "关闭所有桌面置顶" : "开启所有桌面置顶"
        menu.addItem(NSMenuItem(title: pinTitle, action: #selector(togglePinning), keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "刷新内容", action: #selector(refreshContent), keyEquivalent: "r"))
        menu.addItem(NSMenuItem(title: "打开设置", action: #selector(openSettings), keyEquivalent: ","))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "退出", action: #selector(quitApp), keyEquivalent: "q"))

        for item in menu.items {
            item.target = self
        }

        return menu
    }

    @objc private func toggleWindow() {
        AppLogger.shared.log("Menu action: toggle window")
        appState?.toggleWindowVisibility()
    }

    @objc private func togglePinning() {
        AppLogger.shared.log("Menu action: toggle pinning")
        appState?.togglePinning()
    }

    @objc private func refreshContent() {
        AppLogger.shared.log("Menu action: refresh")
        appState?.refreshNow()
    }

    @objc private func openSettings() {
        AppLogger.shared.log("Menu action: open settings")
        appState?.openSettings()
    }

    @objc private func quitApp() {
        AppLogger.shared.log("Menu action: quit app")
        NSApplication.shared.terminate(nil)
    }
}
