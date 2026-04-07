import Combine
import Foundation

@MainActor
final class SettingsStore: ObservableObject {
    @Published var serviceURL: String {
        didSet { defaults.set(serviceURL, forKey: SettingsKey.serviceURL) }
    }
    @Published var pythonProjectRoot: String {
        didSet { defaults.set(pythonProjectRoot, forKey: SettingsKey.pythonProjectRoot) }
    }
    @Published var autoManagePythonService: Bool {
        didSet { defaults.set(autoManagePythonService, forKey: SettingsKey.autoManagePythonService) }
    }
    @Published var requestTimeout: Double {
        didSet { defaults.set(requestTimeout, forKey: SettingsKey.requestTimeout) }
    }
    @Published var refreshInterval: Double {
        didSet { defaults.set(refreshInterval, forKey: SettingsKey.refreshInterval) }
    }
    @Published var showOnLaunch: Bool {
        didSet { defaults.set(showOnLaunch, forKey: SettingsKey.showOnLaunch) }
    }
    @Published var rememberWindowFrame: Bool {
        didSet { defaults.set(rememberWindowFrame, forKey: SettingsKey.rememberWindowFrame) }
    }
    @Published var launchAtLogin: Bool {
        didSet { defaults.set(launchAtLogin, forKey: SettingsKey.launchAtLogin) }
    }
    @Published var keepMenuBarIcon: Bool {
        didSet { defaults.set(keepMenuBarIcon, forKey: SettingsKey.keepMenuBarIcon) }
    }
    @Published var debugInfoEnabled: Bool {
        didSet { defaults.set(debugInfoEnabled, forKey: SettingsKey.debugInfoEnabled) }
    }
    @Published var showOnAllSpaces: Bool {
        didSet { defaults.set(showOnAllSpaces, forKey: SettingsKey.showOnAllSpaces) }
    }
    @Published var fullScreenEnhanced: Bool {
        didSet { defaults.set(fullScreenEnhanced, forKey: SettingsKey.fullScreenEnhanced) }
    }
    @Published var glassOpacity: Double {
        didSet { defaults.set(glassOpacity, forKey: SettingsKey.glassOpacity) }
    }
    @Published var material: OverlayMaterial {
        didSet { defaults.set(material.rawValue, forKey: SettingsKey.material) }
    }
    @Published var cornerRadius: Double {
        didSet { defaults.set(cornerRadius, forKey: SettingsKey.cornerRadius) }
    }
    @Published var shadowRadius: Double {
        didSet { defaults.set(shadowRadius, forKey: SettingsKey.shadowRadius) }
    }
    @Published var fontSize: Double {
        didSet { defaults.set(fontSize, forKey: SettingsKey.fontSize) }
    }
    @Published var enableClickThrough: Bool {
        didSet { defaults.set(enableClickThrough, forKey: SettingsKey.enableClickThrough) }
    }
    @Published var fadeWhenInactive: Bool {
        didSet { defaults.set(fadeWhenInactive, forKey: SettingsKey.fadeWhenInactive) }
    }
    @Published var dingtalkEnabled: Bool {
        didSet { defaults.set(dingtalkEnabled, forKey: SettingsKey.dingtalkEnabled) }
    }
    @Published var remindersEnabled: Bool {
        didSet { defaults.set(remindersEnabled, forKey: SettingsKey.remindersEnabled) }
    }
    @Published var toggleWindowHotKey: HotKeyDescriptor {
        didSet { defaults.set(encode(hotKey: toggleWindowHotKey), forKey: SettingsKey.toggleWindowHotKey) }
    }
    @Published var togglePinHotKey: HotKeyDescriptor {
        didSet { defaults.set(encode(hotKey: togglePinHotKey), forKey: SettingsKey.togglePinHotKey) }
    }
    @Published var shortcutErrorMessage: String?

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        serviceURL = defaults.string(forKey: SettingsKey.serviceURL) ?? "http://127.0.0.1:33189"
        pythonProjectRoot = defaults.string(forKey: SettingsKey.pythonProjectRoot) ?? "/Users/zhouhuaifeng/Code/personal/py_workspace/notion_ext"
        autoManagePythonService = defaults.object(forKey: SettingsKey.autoManagePythonService) as? Bool ?? true
        requestTimeout = defaults.object(forKey: SettingsKey.requestTimeout) as? Double ?? 8
        refreshInterval = defaults.object(forKey: SettingsKey.refreshInterval) as? Double ?? 300
        showOnLaunch = defaults.object(forKey: SettingsKey.showOnLaunch) as? Bool ?? true
        rememberWindowFrame = defaults.object(forKey: SettingsKey.rememberWindowFrame) as? Bool ?? true
        launchAtLogin = defaults.object(forKey: SettingsKey.launchAtLogin) as? Bool ?? false
        keepMenuBarIcon = defaults.object(forKey: SettingsKey.keepMenuBarIcon) as? Bool ?? true
        debugInfoEnabled = defaults.object(forKey: SettingsKey.debugInfoEnabled) as? Bool ?? false
        showOnAllSpaces = defaults.object(forKey: SettingsKey.showOnAllSpaces) as? Bool ?? true
        fullScreenEnhanced = defaults.object(forKey: SettingsKey.fullScreenEnhanced) as? Bool ?? true
        glassOpacity = defaults.object(forKey: SettingsKey.glassOpacity) as? Double ?? 0.78
        material = OverlayMaterial(rawValue: defaults.string(forKey: SettingsKey.material) ?? "") ?? .hudWindow
        cornerRadius = defaults.object(forKey: SettingsKey.cornerRadius) as? Double ?? 24
        shadowRadius = defaults.object(forKey: SettingsKey.shadowRadius) as? Double ?? 18
        fontSize = defaults.object(forKey: SettingsKey.fontSize) as? Double ?? 14
        enableClickThrough = defaults.object(forKey: SettingsKey.enableClickThrough) as? Bool ?? false
        fadeWhenInactive = defaults.object(forKey: SettingsKey.fadeWhenInactive) as? Bool ?? false
        dingtalkEnabled = defaults.object(forKey: SettingsKey.dingtalkEnabled) as? Bool ?? true
        remindersEnabled = defaults.object(forKey: SettingsKey.remindersEnabled) as? Bool ?? false
        toggleWindowHotKey = Self.decodeHotKey(defaults.string(forKey: SettingsKey.toggleWindowHotKey)) ?? .toggleWindowDefault
        togglePinHotKey = Self.decodeHotKey(defaults.string(forKey: SettingsKey.togglePinHotKey)) ?? .togglePinDefault
    }

    func setToggleWindowHotKey(_ descriptor: HotKeyDescriptor) {
        shortcutErrorMessage = nil
        guard descriptor.isValid else {
            shortcutErrorMessage = "快捷键至少要包含一个修饰键。"
            return
        }
        guard descriptor != togglePinHotKey else {
            shortcutErrorMessage = "显示/隐藏快捷键不能与置顶快捷键重复。"
            return
        }
        toggleWindowHotKey = descriptor
    }

    func setTogglePinHotKey(_ descriptor: HotKeyDescriptor) {
        shortcutErrorMessage = nil
        guard descriptor.isValid else {
            shortcutErrorMessage = "快捷键至少要包含一个修饰键。"
            return
        }
        guard descriptor != toggleWindowHotKey else {
            shortcutErrorMessage = "置顶快捷键不能与显示/隐藏快捷键重复。"
            return
        }
        togglePinHotKey = descriptor
    }

    private func encode(hotKey: HotKeyDescriptor) -> String {
        "\(hotKey.keyCode):\(hotKey.modifiers)"
    }

    private static func decodeHotKey(_ rawValue: String?) -> HotKeyDescriptor? {
        guard let rawValue else { return nil }
        let parts = rawValue.split(separator: ":")
        guard parts.count == 2, let keyCode = UInt32(parts[0]), let modifiers = UInt32(parts[1]) else {
            return nil
        }
        return HotKeyDescriptor(keyCode: keyCode, modifiers: modifiers)
    }
}
