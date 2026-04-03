import Carbon
import Foundation

private func handleHotKeyEvent(
    _ nextHandler: EventHandlerCallRef?,
    _ eventRef: EventRef?,
    _ userData: UnsafeMutableRawPointer?
) -> OSStatus {
    guard let eventRef else { return noErr }
    AppLogger.shared.log("HotKey event received")
    return HotKeyManager.dispatch(eventRef: eventRef)
}

enum HotKeyRegistrationError: LocalizedError {
    case failed(OSStatus)

    var errorDescription: String? {
        switch self {
        case .failed(let status):
            return "全局快捷键注册失败（OSStatus: \(status)）。可能与系统或其他应用冲突。"
        }
    }
}

final class HotKeyManager {
    static let shared = HotKeyManager()

    private var hotKeyRefs: [UInt32: EventHotKeyRef?] = [:]
    private var handlerRef: EventHandlerRef?
    private static var callbacks: [UInt32: () -> Void] = [:]
    private static var handlerInstalled = false

    private init() {
        installHandlerIfNeeded()
    }

    static func dispatch(eventRef: EventRef) -> OSStatus {
        var hotKeyID = EventHotKeyID()
        let status = GetEventParameter(
            eventRef,
            EventParamName(kEventParamDirectObject),
            EventParamType(typeEventHotKeyID),
            nil,
            MemoryLayout<EventHotKeyID>.size,
            nil,
            &hotKeyID
        )
        guard status == noErr else { return status }
        callbacks[hotKeyID.id]?()
        return noErr
    }

    func register(toggleWindow: HotKeyDescriptor, togglePin: HotKeyDescriptor, onToggleWindow: @escaping () -> Void, onTogglePin: @escaping () -> Void) throws {
        unregisterAll()
        try register(hotKey: toggleWindow, identifier: 1, callback: onToggleWindow)
        try register(hotKey: togglePin, identifier: 2, callback: onTogglePin)
    }

    func unregisterAll() {
        for (identifier, ref) in hotKeyRefs {
            if let ref {
                UnregisterEventHotKey(ref)
            }
            Self.callbacks[identifier] = nil
        }
        hotKeyRefs.removeAll()
    }

    private func installHandlerIfNeeded() {
        guard !Self.handlerInstalled else { return }
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        let status = InstallEventHandler(
            GetEventDispatcherTarget(),
            handleHotKeyEvent,
            1,
            &eventType,
            nil,
            &handlerRef
        )
        AppLogger.shared.log("HotKey install handler status=\(status)")

        Self.handlerInstalled = true
    }

    private func register(hotKey: HotKeyDescriptor, identifier: UInt32, callback: @escaping () -> Void) throws {
        var ref: EventHotKeyRef?
        let hotKeyID = EventHotKeyID(signature: OSType(0x4E544F56), id: identifier)
        let status = RegisterEventHotKey(
            hotKey.keyCode,
            hotKey.modifiers,
            hotKeyID,
            GetEventDispatcherTarget(),
            0,
            &ref
        )

        guard status == noErr else {
            AppLogger.shared.log("HotKey register failed. id=\(identifier) keyCode=\(hotKey.keyCode) modifiers=\(hotKey.modifiers) status=\(status)")
            throw HotKeyRegistrationError.failed(status)
        }

        hotKeyRefs[identifier] = ref
        Self.callbacks[identifier] = callback
        AppLogger.shared.log("HotKey registered. id=\(identifier) keyCode=\(hotKey.keyCode) modifiers=\(hotKey.modifiers)")
    }
}
