import AppKit
import Carbon.HIToolbox
import Foundation

struct OverlayResponse: Codable {
    let generatedAt: String
    let title: String
    let text: String
    let runningItems: [String]
    let today: TodaySection
    let week: WeekSection
    let reminders: ReminderSection
    let periods: PeriodsSection?
}

struct TodaySection: Codable {
    let progress: ProgressPayload
    let items: [TodayItem]
}

struct WeekSection: Codable {
    let progress: ProgressPayload
    let items: [WeekItem]
}

struct ReminderSection: Codable {
    let pendingCount: Int
    let items: [ReminderItem]
}

struct ProgressPayload: Codable {
    let doneCount: Int
    let totalCount: Int
    let percent: Int
    let bar: String
}

struct PeriodsSection: Codable {
    let month: PeriodProgressPayload
    let quarter: PeriodProgressPayload
    let year: PeriodProgressPayload
}

struct PeriodProgressPayload: Codable {
    let percent: Int
}

struct TodayItem: Codable, Identifiable {
    let id: String
    let name: String
    let status: String?
    let done: Bool
    let timeStart: String?
    let timeEnd: String?
    let displayTime: String
}

struct WeekItem: Codable, Identifiable {
    let taskName: String
    let done: Bool
    let id: String
    let startDate: String?
    let endDate: String?
    let weekdayRange: String
}

struct ReminderItem: Codable, Identifiable {
    let id: String
    let name: String
    let completed: Bool
}

struct ReportSettingsPayload: Codable {
    let dingtalkEnabled: Bool
    let remindersEnabled: Bool
}

struct CompleteItemRequestPayload: Codable {
    let kind: String
    let id: String
    let value: Bool
}

struct CompleteItemResponsePayload: Codable {
    let ok: Bool
    let error: String?
}

enum OverlayCompleteKind: String {
    case notionToday = "notion_today"
    case notionWeek = "notion_week"
    case appleReminder = "apple_reminder"
}

enum OverlayMaterial: String, CaseIterable, Identifiable {
    case hudWindow
    case sidebar
    case menu
    case contentBackground

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .hudWindow:
            return "HUD"
        case .sidebar:
            return "Sidebar"
        case .menu:
            return "Menu"
        case .contentBackground:
            return "Content"
        }
    }

    var nsMaterial: NSVisualEffectView.Material {
        switch self {
        case .hudWindow:
            return .hudWindow
        case .sidebar:
            return .sidebar
        case .menu:
            return .menu
        case .contentBackground:
            return .contentBackground
        }
    }
}

struct HotKeyDescriptor: Equatable, Codable {
    let keyCode: UInt32
    let modifiers: UInt32

    static let toggleWindowDefault = HotKeyDescriptor(
        keyCode: UInt32(kVK_Space),
        modifiers: UInt32(cmdKey | optionKey)
    )

    static let togglePinDefault = HotKeyDescriptor(
        keyCode: UInt32(kVK_ANSI_P),
        modifiers: UInt32(cmdKey | optionKey | shiftKey)
    )

    var displayString: String {
        let modifierDisplay = [
            (UInt32(controlKey), "⌃"),
            (UInt32(optionKey), "⌥"),
            (UInt32(shiftKey), "⇧"),
            (UInt32(cmdKey), "⌘"),
        ]
        let prefix = modifierDisplay
            .filter { modifiers & $0.0 != 0 }
            .map(\.1)
            .joined()
        return prefix + Self.keyName(for: keyCode)
    }

    var isValid: Bool {
        modifiers != 0
    }

    static func from(event: NSEvent) -> HotKeyDescriptor {
        HotKeyDescriptor(
            keyCode: UInt32(event.keyCode),
            modifiers: carbonModifiers(from: event.modifierFlags)
        )
    }

    static func carbonModifiers(from flags: NSEvent.ModifierFlags) -> UInt32 {
        var result: UInt32 = 0
        if flags.contains(.command) { result |= UInt32(cmdKey) }
        if flags.contains(.option) { result |= UInt32(optionKey) }
        if flags.contains(.shift) { result |= UInt32(shiftKey) }
        if flags.contains(.control) { result |= UInt32(controlKey) }
        return result
    }

    private static func keyName(for keyCode: UInt32) -> String {
        switch Int(keyCode) {
        case kVK_Space:
            return "Space"
        case kVK_Return:
            return "Return"
        case kVK_Escape:
            return "Esc"
        case kVK_Tab:
            return "Tab"
        case kVK_Delete:
            return "Delete"
        case kVK_UpArrow:
            return "Up"
        case kVK_DownArrow:
            return "Down"
        case kVK_LeftArrow:
            return "Left"
        case kVK_RightArrow:
            return "Right"
        default:
            let map: [UInt32: String] = [
                UInt32(kVK_ANSI_A): "A",
                UInt32(kVK_ANSI_B): "B",
                UInt32(kVK_ANSI_C): "C",
                UInt32(kVK_ANSI_D): "D",
                UInt32(kVK_ANSI_E): "E",
                UInt32(kVK_ANSI_F): "F",
                UInt32(kVK_ANSI_G): "G",
                UInt32(kVK_ANSI_H): "H",
                UInt32(kVK_ANSI_I): "I",
                UInt32(kVK_ANSI_J): "J",
                UInt32(kVK_ANSI_K): "K",
                UInt32(kVK_ANSI_L): "L",
                UInt32(kVK_ANSI_M): "M",
                UInt32(kVK_ANSI_N): "N",
                UInt32(kVK_ANSI_O): "O",
                UInt32(kVK_ANSI_P): "P",
                UInt32(kVK_ANSI_Q): "Q",
                UInt32(kVK_ANSI_R): "R",
                UInt32(kVK_ANSI_S): "S",
                UInt32(kVK_ANSI_T): "T",
                UInt32(kVK_ANSI_U): "U",
                UInt32(kVK_ANSI_V): "V",
                UInt32(kVK_ANSI_W): "W",
                UInt32(kVK_ANSI_X): "X",
                UInt32(kVK_ANSI_Y): "Y",
                UInt32(kVK_ANSI_Z): "Z",
                UInt32(kVK_ANSI_0): "0",
                UInt32(kVK_ANSI_1): "1",
                UInt32(kVK_ANSI_2): "2",
                UInt32(kVK_ANSI_3): "3",
                UInt32(kVK_ANSI_4): "4",
                UInt32(kVK_ANSI_5): "5",
                UInt32(kVK_ANSI_6): "6",
                UInt32(kVK_ANSI_7): "7",
                UInt32(kVK_ANSI_8): "8",
                UInt32(kVK_ANSI_9): "9",
            ]
            return map[keyCode, default: "Key\(keyCode)"]
        }
    }
}

enum SettingsKey {
    static let serviceURL = "serviceURL"
    static let requestTimeout = "requestTimeout"
    static let pythonProjectRoot = "pythonProjectRoot"
    static let autoManagePythonService = "autoManagePythonService"
    static let refreshInterval = "refreshInterval"
    static let showOnLaunch = "showOnLaunch"
    static let rememberWindowFrame = "rememberWindowFrame"
    static let launchAtLogin = "launchAtLogin"
    static let keepMenuBarIcon = "keepMenuBarIcon"
    static let debugInfoEnabled = "debugInfoEnabled"
    static let showOnAllSpaces = "showOnAllSpaces"
    static let fullScreenEnhanced = "fullScreenEnhanced"
    static let glassOpacity = "glassOpacity"
    static let material = "material"
    static let cornerRadius = "cornerRadius"
    static let shadowRadius = "shadowRadius"
    static let fontSize = "fontSize"
    static let enableClickThrough = "enableClickThrough"
    static let fadeWhenInactive = "fadeWhenInactive"
    static let dingtalkEnabled = "dingtalkEnabled"
    static let remindersEnabled = "remindersEnabled"
    static let toggleWindowHotKey = "toggleWindowHotKey"
    static let togglePinHotKey = "togglePinHotKey"
}
