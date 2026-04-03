import AppKit
import Carbon.HIToolbox
import SwiftUI

struct OverlayRootView: View {
    @EnvironmentObject private var appState: OverlayAppState
    @EnvironmentObject private var settings: SettingsStore

    var body: some View {
        ZStack {
            GlassBackgroundView(
                material: settings.material,
                opacity: settings.glassOpacity,
                cornerRadius: settings.cornerRadius
            )

            VStack(alignment: .leading, spacing: 10) {
                WindowDragHandle()
                ScrollView {
                    VStack(alignment: .leading, spacing: 14) {
                        TodaySectionView(section: appState.snapshot?.today)
                        WeekSectionView(section: appState.snapshot?.week)
                        ReminderSectionView(section: appState.snapshot?.reminders)
                        if settings.debugInfoEnabled, let text = appState.snapshot?.text {
                            DebugTextView(text: text)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .topLeading)
                    .padding(.bottom, 2)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
        }
        .clipShape(RoundedRectangle(cornerRadius: settings.cornerRadius, style: .continuous))
        .shadow(color: Color.black.opacity(0.18), radius: settings.shadowRadius, y: 16)
        .frame(minWidth: 300, minHeight: 320)
    }
}

struct WindowDragHandle: View {
    var body: some View {
        ZStack {
            WindowDragArea()
            HStack {
                Spacer()
                Capsule()
                    .fill(Color.white.opacity(0.28))
                    .frame(width: 56, height: 5)
                Spacer()
            }
        }
        .frame(height: 18)
    }
}

struct WindowDragArea: NSViewRepresentable {
    func makeNSView(context: Context) -> DragCaptureView {
        DragCaptureView()
    }

    func updateNSView(_ nsView: DragCaptureView, context: Context) {}
}

final class DragCaptureView: NSView {
    override func mouseDown(with event: NSEvent) {
        window?.performDrag(with: event)
    }
}

struct TodaySectionView: View {
    let section: TodaySection?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("今日 todo")
                .font(.headline)
            Text(section.map { "\($0.progress.doneCount)/\($0.progress.totalCount) · \($0.progress.bar)" } ?? "暂无数据")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if let section, !section.items.isEmpty {
                ForEach(section.items) { item in
                    RowView(
                        leading: item.done ? "✅" : "⬜",
                        title: item.name,
                        trailing: item.displayTime.isEmpty ? nil : item.displayTime
                    )
                }
            } else {
                EmptyStateRow(text: "暂无今日任务")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct WeekSectionView: View {
    let section: WeekSection?

    private func normalizedWeekdayRange(_ value: String) -> String {
        let trimmed = value
            .replacingOccurrences(of: "(", with: "")
            .replacingOccurrences(of: ")", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.replacingOccurrences(of: "-", with: " - ")
            .replacingOccurrences(of: "  ", with: " ")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("本周 todo")
                .font(.headline)
            Text(section.map { "\($0.progress.doneCount)/\($0.progress.totalCount) · \($0.progress.bar)" } ?? "暂无数据")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if let section, !section.items.isEmpty {
                ForEach(section.items) { item in
                    RowView(
                        leading: item.done ? "✅" : "⬜",
                        title: item.taskName,
                        trailing: normalizedWeekdayRange(item.weekdayRange)
                    )
                }
            } else {
                EmptyStateRow(text: "暂无本周任务")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct ReminderSectionView: View {
    let section: ReminderSection?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("待办提醒事项")
                .font(.headline)
            Text(section.map { "未完成 \($0.pendingCount) 条" } ?? "暂无数据")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if let section, !section.items.isEmpty {
                ForEach(section.items) { item in
                    RowView(leading: "⬜", title: item.name, trailing: nil)
                }
            } else {
                EmptyStateRow(text: "暂无提醒事项")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct RowView: View {
    let leading: String
    let title: String
    let trailing: String?

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Text(leading)
            Text(title)
                .frame(maxWidth: .infinity, alignment: .leading)
            if let trailing, !trailing.isEmpty {
                Text(trailing)
                    .foregroundStyle(.secondary)
            }
        }
        .font(.system(size: 14))
    }
}

struct EmptyStateRow: View {
    let text: String

    var body: some View {
        Text(text)
            .foregroundStyle(.secondary)
            .font(.system(size: 13))
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct DebugTextView: View {
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("调试文本（与钉钉正文一致）")
                .font(.headline)
            Text(text)
                .font(.system(size: 12, design: .monospaced))
                .frame(maxWidth: .infinity, alignment: .leading)
                .textSelection(.enabled)
        }
    }
}

struct HotKeyRecorderButton: View {
    let title: String
    let currentHotKey: HotKeyDescriptor
    let onRecord: (HotKeyDescriptor) -> Void

    @State private var isRecording = false
    @State private var monitor: Any?

    var body: some View {
        Button(isRecording ? "按下新快捷键..." : "\(title)：\(currentHotKey.displayString)") {
            startRecording()
        }
        .buttonStyle(.borderedProminent)
        .onDisappear {
            stopRecording()
        }
    }

    private func startRecording() {
        stopRecording()
        isRecording = true
        monitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            if event.keyCode == UInt16(kVK_Escape) {
                stopRecording()
                return nil
            }
            let descriptor = HotKeyDescriptor.from(event: event)
            onRecord(descriptor)
            stopRecording()
            return nil
        }
    }

    private func stopRecording() {
        isRecording = false
        if let monitor {
            NSEvent.removeMonitor(monitor)
            self.monitor = nil
        }
    }
}

struct SettingsView: View {
    @EnvironmentObject private var settings: SettingsStore
    @EnvironmentObject private var appState: OverlayAppState

    var body: some View {
        Form {
            Section("快捷键") {
                HotKeyRecorderButton(title: "显示/隐藏窗口", currentHotKey: settings.toggleWindowHotKey) {
                    settings.setToggleWindowHotKey($0)
                }
                HotKeyRecorderButton(title: "切换置顶", currentHotKey: settings.togglePinHotKey) {
                    settings.setTogglePinHotKey($0)
                }
                if let shortcutErrorMessage = settings.shortcutErrorMessage {
                    Text(shortcutErrorMessage)
                        .foregroundStyle(.orange)
                }
            }

            Section("外观") {
                Slider(value: $settings.glassOpacity, in: 0.25...1.0) {
                    Text("透明度")
                } minimumValueLabel: {
                    Text("淡")
                } maximumValueLabel: {
                    Text("实")
                }

                Picker("材质", selection: $settings.material) {
                    ForEach(OverlayMaterial.allCases) { material in
                        Text(material.displayName).tag(material)
                    }
                }
            }

            Section("行为") {
                Toggle(
                    "发送钉钉消息",
                    isOn: Binding(
                        get: { settings.dingtalkEnabled },
                        set: { appState.updateDingtalkEnabled($0) }
                    )
                )
                Toggle("登录后自启动", isOn: $settings.launchAtLogin)
                Toggle("启动时自动显示窗口", isOn: $settings.showOnLaunch)
                Toggle("记住窗口位置与尺寸", isOn: $settings.rememberWindowFrame)
                Toggle("在所有桌面置顶显示", isOn: $settings.showOnAllSpaces)
                Toggle("全屏兼容增强模式", isOn: $settings.fullScreenEnhanced)
                Stepper(value: $settings.refreshInterval, in: 10...600, step: 10) {
                    Text("自动刷新间隔：\(Int(settings.refreshInterval)) 秒")
                }
            }

            Section("高级") {
                TextField("服务地址", text: $settings.serviceURL)
                    .textFieldStyle(.roundedBorder)
                TextField("Python 项目路径", text: $settings.pythonProjectRoot)
                    .textFieldStyle(.roundedBorder)
                Toggle("自动管理 Python 服务", isOn: $settings.autoManagePythonService)
                Stepper(value: $settings.requestTimeout, in: 2...30, step: 1) {
                    Text("请求超时：\(Int(settings.requestTimeout)) 秒")
                }
                Toggle("显示调试信息", isOn: $settings.debugInfoEnabled)
                Toggle("隐藏时保留菜单栏图标", isOn: $settings.keepMenuBarIcon)
                Toggle("鼠标穿透", isOn: $settings.enableClickThrough)
                Toggle("失焦时降低透明度", isOn: $settings.fadeWhenInactive)
            }

            if let runtimeMessage = appState.runtimeMessage {
                Section("状态") {
                    Text(runtimeMessage)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .formStyle(.grouped)
        .padding(18)
        .frame(width: 560, height: 620)
    }
}
