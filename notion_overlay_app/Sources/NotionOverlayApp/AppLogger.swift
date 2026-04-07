import Foundation

final class AppLogger {
    static let shared = AppLogger()

    private let queue = DispatchQueue(label: "NotionOverlayApp.Logger")
    private let formatter: DateFormatter
    private let fileURL: URL

    private init() {
        formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSS"

        fileURL = Self.resolveLogFileURL()

        if !FileManager.default.fileExists(atPath: fileURL.path) {
            try? FileManager.default.createDirectory(
                at: fileURL.deletingLastPathComponent(),
                withIntermediateDirectories: true
            )
            FileManager.default.createFile(atPath: fileURL.path, contents: Data(), attributes: nil)
        }
    }

    func log(_ message: String) {
        queue.async {
            let timestamp = self.formatter.string(from: Date())
            let line = "[\(timestamp)] \(message)\n"
            guard let data = line.data(using: .utf8) else { return }
            do {
                let handle = try FileHandle(forWritingTo: self.fileURL)
                defer { try? handle.close() }
                try handle.seekToEnd()
                try handle.write(contentsOf: data)
            } catch {
                // Ignore logging failures to avoid affecting app behavior.
            }
        }
    }

    private static func resolveLogFileURL() -> URL {
        let fileManager = FileManager.default

        if let configuredRoot = UserDefaults.standard.string(forKey: "pythonProjectRoot")?
            .trimmingCharacters(in: .whitespacesAndNewlines),
           !configuredRoot.isEmpty {
            let configuredURL = URL(fileURLWithPath: configuredRoot, isDirectory: true).standardizedFileURL
            var isDir: ObjCBool = false
            if fileManager.fileExists(atPath: configuredURL.path, isDirectory: &isDir), isDir.boolValue {
                return configuredURL.appendingPathComponent("notion_ext.log")
            }
        }

        let cwd = URL(fileURLWithPath: fileManager.currentDirectoryPath, isDirectory: true).standardizedFileURL
        let projectRoot: URL
        if cwd.lastPathComponent == "notion_overlay_app" {
            projectRoot = cwd.deletingLastPathComponent()
        } else {
            projectRoot = cwd
        }
        return projectRoot.appendingPathComponent("notion_ext.log")
    }
}
