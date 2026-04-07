import AppKit
import Combine
import Foundation
import SwiftUI

@MainActor
final class OverlayAppState: ObservableObject {
    @Published private(set) var snapshot: OverlayResponse?
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?
    @Published var runtimeMessage: String?
    @Published private(set) var isWindowVisible = false
    @Published private(set) var isUpdatingDingtalkSetting = false
    @Published private(set) var completingTokens = Set<String>()

    let settings: SettingsStore

    private let apiClient = OverlayAPIClient()
    private let loginItemManager = LoginItemManager()
    private let hotKeyManager = HotKeyManager.shared
    private let settingsWindowManager = SettingsWindowManager()
    private let backendServiceManager = BackendServiceManager()
    private let remindersPermissionManager = RemindersPermissionManager()
    private var pollingTask: Task<Void, Never>?
    private var currentRefreshTask: Task<Void, Never>?
    private var subscriptions = Set<AnyCancellable>()
    let windowManager: OverlayWindowManager
    var menuBarController: MenuBarController?

    init(settings: SettingsStore) {
        self.settings = settings
        self.windowManager = OverlayWindowManager(settings: settings)
        bindSettings()
    }

    func bootstrap() {
        AppLogger.shared.log("AppState bootstrap start")
        Task { @MainActor [weak self] in
            guard let self else { return }
            remindersPermissionManager.logCurrentStatus()
            if settings.autoManagePythonService {
                backendServiceManager.startIfNeeded(
                    projectRoot: settings.pythonProjectRoot,
                    serviceURL: settings.serviceURL
                )
            }
        }
        let rootView = AnyView(OverlayRootView().environmentObject(self).environmentObject(settings))
        windowManager.configure(with: rootView)
        if settings.showOnLaunch {
            windowManager.show()
            isWindowVisible = true
        }
        registerHotKeys()
        applyLaunchAtLogin()
        startPolling()
        syncReportSettings()
        AppLogger.shared.log("AppState bootstrap done. showOnLaunch=\(settings.showOnLaunch)")
    }

    func shutdown() {
        AppLogger.shared.log("AppState shutdown")
        backendServiceManager.stopIfManaged()
    }

    func refreshNow() {
        AppLogger.shared.log("Refresh requested (manual)")
        currentRefreshTask?.cancel()
        currentRefreshTask = Task { [weak self] in
            guard let self else { return }
            await self.refresh()
        }
    }

    func toggleWindowVisibility() {
        AppLogger.shared.log("Toggle window visibility")
        windowManager.toggleVisibility()
        isWindowVisible = windowManager.isVisible()
        menuBarController?.refreshMenu()
    }

    func togglePinning() {
        AppLogger.shared.log("Toggle pinning")
        settings.showOnAllSpaces.toggle()
        windowManager.applySettings()
        runtimeMessage = settings.showOnAllSpaces ? "已开启置顶显示" : "已关闭置顶显示"
    }

    func openSettings() {
        AppLogger.shared.log("Open settings window")
        settingsWindowManager.show(settings: settings, appState: self)
    }

    func isCompleting(kind: OverlayCompleteKind, id: String) -> Bool {
        completingTokens.contains(completionToken(kind: kind, id: id))
    }

    func setItemCompleted(kind: OverlayCompleteKind, id: String, value: Bool) {
        guard !id.isEmpty else { return }
        let token = completionToken(kind: kind, id: id)
        guard !completingTokens.contains(token) else { return }
        completingTokens.insert(token)

        Task { [weak self] in
            guard let self else { return }
            defer { self.completingTokens.remove(token) }
            do {
                _ = try await apiClient.completeItem(settings: settings, kind: kind, id: id, value: value)
                runtimeMessage = value ? "已标记完成" : "已恢复为未完成"
                await refresh()
            } catch {
                runtimeMessage = "更新状态失败：\(error.localizedDescription)"
                AppLogger.shared.log(
                    "Set item completed failed: kind=\(kind.rawValue) id=\(id) value=\(value) error=\(error.localizedDescription)"
                )
            }
        }
    }

    func updateDingtalkEnabled(_ enabled: Bool) {
        let previous = settings.dingtalkEnabled
        settings.dingtalkEnabled = enabled
        isUpdatingDingtalkSetting = true
        Task { [weak self] in
            guard let self else { return }
            defer { isUpdatingDingtalkSetting = false }
            do {
                let payload = try await apiClient.updateReportSettings(
                    settings: settings,
                    dingtalkEnabled: enabled,
                    remindersEnabled: settings.remindersEnabled
                )
                settings.dingtalkEnabled = payload.dingtalkEnabled
                settings.remindersEnabled = payload.remindersEnabled
                runtimeMessage = payload.dingtalkEnabled ? "已开启钉钉发送" : "已关闭钉钉发送"
                AppLogger.shared.log("Update dingtalk setting success: \(payload.dingtalkEnabled)")
            } catch {
                settings.dingtalkEnabled = previous
                runtimeMessage = "更新钉钉发送开关失败：\(error.localizedDescription)"
                AppLogger.shared.log("Update dingtalk setting failed: \(error.localizedDescription)")
            }
        }
    }

    func updateRemindersEnabled(_ enabled: Bool) {
        let previous = settings.remindersEnabled
        settings.remindersEnabled = enabled
        isUpdatingDingtalkSetting = true
        Task { [weak self] in
            guard let self else { return }
            defer { isUpdatingDingtalkSetting = false }
            do {
                let payload = try await apiClient.updateReportSettings(
                    settings: settings,
                    dingtalkEnabled: settings.dingtalkEnabled,
                    remindersEnabled: enabled
                )
                settings.dingtalkEnabled = payload.dingtalkEnabled
                settings.remindersEnabled = payload.remindersEnabled
                runtimeMessage = payload.remindersEnabled ? "已开启待办事项获取" : "已关闭待办事项获取"
                refreshNow()
                AppLogger.shared.log("Update reminders setting success: \(payload.remindersEnabled)")
            } catch {
                settings.remindersEnabled = previous
                runtimeMessage = "更新待办事项开关失败：\(error.localizedDescription)"
                AppLogger.shared.log("Update reminders setting failed: \(error.localizedDescription)")
            }
        }
    }

    private func refresh() async {
        isLoading = true
        defer { isLoading = false }

        do {
            AppLogger.shared.log("Refresh begin: \(settings.serviceURL)")
            let freshSnapshot = try await apiClient.fetchSnapshot(settings: settings)
            snapshot = freshSnapshot
            errorMessage = nil
            AppLogger.shared.log("Refresh success. generatedAt=\(freshSnapshot.generatedAt)")
        } catch {
            errorMessage = error.localizedDescription
            AppLogger.shared.log("Refresh failed: \(error.localizedDescription)")
        }
    }

    private func startPolling() {
        pollingTask?.cancel()
        pollingTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                await refresh()
                let nanos = UInt64(max(settings.refreshInterval, 300) * 1_000_000_000)
                try? await Task.sleep(nanoseconds: nanos)
            }
        }
    }

    private func syncReportSettings() {
        Task { [weak self] in
            guard let self else { return }
            do {
                let payload = try await apiClient.fetchReportSettings(settings: settings)
                settings.dingtalkEnabled = payload.dingtalkEnabled
                settings.remindersEnabled = payload.remindersEnabled
                AppLogger.shared.log(
                    "Fetched report settings. dingtalkEnabled=\(payload.dingtalkEnabled) remindersEnabled=\(payload.remindersEnabled)"
                )
            } catch {
                AppLogger.shared.log("Fetch report settings failed: \(error.localizedDescription)")
            }
        }
    }

    private func bindSettings() {
        settings.$showOnAllSpaces
            .sink { [weak self] _ in
                self?.windowManager.applySettings()
                self?.menuBarController?.refreshMenu()
            }
            .store(in: &subscriptions)

        settings.$fullScreenEnhanced
            .sink { [weak self] _ in
                self?.windowManager.applySettings()
            }
            .store(in: &subscriptions)

        Publishers.Merge(
            settings.$enableClickThrough.map { _ in () }.eraseToAnyPublisher(),
            settings.$fadeWhenInactive.map { _ in () }.eraseToAnyPublisher()
        )
        .sink { [weak self] _ in
            self?.windowManager.applySettings()
        }
        .store(in: &subscriptions)

        Publishers.Merge(
            settings.$toggleWindowHotKey.map { _ in () }.eraseToAnyPublisher(),
            settings.$togglePinHotKey.map { _ in () }.eraseToAnyPublisher()
        )
        .sink { [weak self] _ in
            self?.registerHotKeys()
        }
        .store(in: &subscriptions)

        settings.$keepMenuBarIcon
            .sink { [weak self] _ in
                self?.menuBarController?.applyVisibility()
            }
            .store(in: &subscriptions)

        settings.$launchAtLogin
            .dropFirst()
            .sink { [weak self] _ in
                self?.applyLaunchAtLogin()
            }
            .store(in: &subscriptions)

        settings.$refreshInterval
            .dropFirst()
            .sink { [weak self] _ in
                self?.startPolling()
            }
            .store(in: &subscriptions)

        settings.$serviceURL
            .dropFirst()
            .sink { [weak self] _ in
                self?.refreshNow()
            }
            .store(in: &subscriptions)
    }

    private func registerHotKeys() {
        do {
            try hotKeyManager.register(
                toggleWindow: settings.toggleWindowHotKey,
                togglePin: settings.togglePinHotKey,
                onToggleWindow: { [weak self] in
                    Task { @MainActor in
                        self?.toggleWindowVisibility()
                    }
                },
                onTogglePin: { [weak self] in
                    Task { @MainActor in
                        self?.togglePinning()
                    }
                }
            )
            runtimeMessage = nil
            AppLogger.shared.log("Hotkeys registered. toggleWindow=\(settings.toggleWindowHotKey.displayString) togglePin=\(settings.togglePinHotKey.displayString)")
        } catch {
            AppLogger.shared.log("Hotkey registration failed with custom shortcuts: \(error.localizedDescription)")
            do {
                try hotKeyManager.register(
                    toggleWindow: .toggleWindowDefault,
                    togglePin: .togglePinDefault,
                    onToggleWindow: { [weak self] in
                        Task { @MainActor in
                            self?.toggleWindowVisibility()
                        }
                    },
                    onTogglePin: { [weak self] in
                        Task { @MainActor in
                            self?.togglePinning()
                        }
                    }
                )
                runtimeMessage = "自定义快捷键不可用，已回退默认快捷键。"
                AppLogger.shared.log("Hotkeys fallback to defaults succeeded.")
            } catch {
                runtimeMessage = error.localizedDescription
                AppLogger.shared.log("Hotkeys fallback failed: \(error.localizedDescription)")
            }
        }
    }

    private func applyLaunchAtLogin() {
        do {
            try loginItemManager.sync(enabled: settings.launchAtLogin)
            if settings.launchAtLogin {
                runtimeMessage = "已开启登录自启动。"
            }
        } catch {
            runtimeMessage = error.localizedDescription
        }
    }

    private func completionToken(kind: OverlayCompleteKind, id: String) -> String {
        "\(kind.rawValue):\(id)"
    }
}

@MainActor
final class OverlayEnvironment {
    static let shared = OverlayEnvironment()

    let settings = SettingsStore()
    lazy var appState = OverlayAppState(settings: settings)

    private init() {}
}
