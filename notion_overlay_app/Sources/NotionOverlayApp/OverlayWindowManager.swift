import AppKit
import SwiftUI

final class OverlayFloatingWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
}

@MainActor
final class OverlayWindowManager: NSObject, NSWindowDelegate {
    private enum FrameStore {
        static let autosaveName = "NotionOverlayWindowFrame"
    }

    private(set) var window: OverlayFloatingWindow?
    private let settings: SettingsStore

    init(settings: SettingsStore) {
        self.settings = settings
        super.init()
    }

    func configure(with rootView: AnyView) {
        if window == nil {
            AppLogger.shared.log("OverlayWindow configure: creating window")
            let overlayWindow = OverlayFloatingWindow(
                contentRect: NSRect(x: 240, y: 240, width: 360, height: 520),
                styleMask: [.titled, .closable, .resizable],
                backing: .buffered,
                defer: false
            )
            overlayWindow.isOpaque = false
            overlayWindow.backgroundColor = .clear
            overlayWindow.titleVisibility = .hidden
            overlayWindow.titlebarAppearsTransparent = true
            overlayWindow.isMovableByWindowBackground = true
            overlayWindow.hidesOnDeactivate = false
            overlayWindow.delegate = self
            overlayWindow.hasShadow = true
            overlayWindow.isReleasedWhenClosed = false
            overlayWindow.standardWindowButton(.zoomButton)?.isHidden = true
            overlayWindow.standardWindowButton(.miniaturizeButton)?.isHidden = true
            overlayWindow.standardWindowButton(.closeButton)?.isHidden = true
            overlayWindow.minSize = NSSize(width: 300, height: 320)

            if settings.rememberWindowFrame {
                overlayWindow.setFrameUsingName(FrameStore.autosaveName)
            }

            ensureWindowIsVisible(overlayWindow)

            overlayWindow.contentView = NSHostingView(rootView: rootView)
            window = overlayWindow
        } else if let hostingView = window?.contentView as? NSHostingView<AnyView> {
            hostingView.rootView = rootView
        } else {
            window?.contentView = NSHostingView(rootView: rootView)
        }

        applySettings()
    }

    func show() {
        guard let window else { return }
        AppLogger.shared.log("OverlayWindow show requested")
        ensureWindowIsVisible(window)
        NSApp.activate(ignoringOtherApps: settings.showOnAllSpaces)
        if settings.showOnAllSpaces {
            window.orderFrontRegardless()
        } else {
            window.orderFront(nil)
        }
        window.makeKeyAndOrderFront(nil)
    }

    func hide() {
        AppLogger.shared.log("OverlayWindow hide requested")
        window?.orderOut(nil)
    }

    func toggleVisibility() {
        guard let window else { return }
        AppLogger.shared.log("OverlayWindow toggle visibility. currentlyVisible=\(window.isVisible)")
        if window.isVisible {
            hide()
        } else {
            show()
        }
    }

    func applySettings() {
        guard let window else { return }
        if settings.showOnAllSpaces {
            var behavior: NSWindow.CollectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
            if settings.fullScreenEnhanced {
                behavior.insert(.stationary)
                behavior.insert(.ignoresCycle)
            }
            window.collectionBehavior = behavior
            window.level = settings.fullScreenEnhanced ? .screenSaver : .statusBar
        } else {
            // 关闭置顶时恢复为普通窗口层级，避免看起来“切换无效”。
            window.collectionBehavior = []
            window.level = .normal
        }
        AppLogger.shared.log(
            "OverlayWindow apply settings. showOnAllSpaces=\(settings.showOnAllSpaces) fullScreenEnhanced=\(settings.fullScreenEnhanced) level=\(window.level.rawValue)"
        )
        // Keep resize and interaction reliable: never ignore mouse events on the overlay window.
        // This avoids a persisted click-through setting making the window non-resizable.
        window.ignoresMouseEvents = false
        if settings.enableClickThrough {
            AppLogger.shared.log("Click-through is enabled in settings but temporarily ignored to keep window resizable.")
        }
        window.alphaValue = settings.fadeWhenInactive && !window.isKeyWindow ? 0.86 : 1.0
        if settings.rememberWindowFrame {
            window.setFrameAutosaveName(FrameStore.autosaveName)
        }
        if window.isVisible {
            if settings.showOnAllSpaces {
                window.orderFrontRegardless()
            } else {
                window.orderFront(nil)
            }
        }
    }

    func isVisible() -> Bool {
        window?.isVisible ?? false
    }

    func windowDidMove(_ notification: Notification) {
        persistFrameIfNeeded()
    }

    func windowDidResize(_ notification: Notification) {
        persistFrameIfNeeded()
    }

    func windowDidBecomeKey(_ notification: Notification) {
        applySettings()
    }

    func windowDidResignKey(_ notification: Notification) {
        applySettings()
    }

    private func persistFrameIfNeeded() {
        guard settings.rememberWindowFrame else { return }
        window?.saveFrame(usingName: FrameStore.autosaveName)
        if let frame = window?.frame {
            AppLogger.shared.log("OverlayWindow frame persisted: x=\(Int(frame.origin.x)) y=\(Int(frame.origin.y)) w=\(Int(frame.size.width)) h=\(Int(frame.size.height))")
        }
    }

    private func ensureWindowIsVisible(_ window: NSWindow) {
        let currentFrame = window.frame
        let expandedFrame = currentFrame.insetBy(dx: -60, dy: -60)
        let isVisibleOnAnyScreen = NSScreen.screens.contains { screen in
            screen.visibleFrame.intersects(expandedFrame)
        }

        if !isVisibleOnAnyScreen {
            if let screen = NSScreen.main ?? NSScreen.screens.first {
                let size = currentFrame.size
                let x = screen.visibleFrame.midX - size.width / 2
                let y = screen.visibleFrame.midY - size.height / 2
                window.setFrameOrigin(NSPoint(x: x, y: y))
            } else {
                window.center()
            }
        }
    }
}
