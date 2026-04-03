import Foundation
import Darwin

final class BackendServiceManager {
    private var process: Process?
    private var didStartManagedProcess = false

    func startIfNeeded(projectRoot: String, serviceURL: String) {
        guard process == nil else { return }
        guard let port = parsePort(from: serviceURL) else {
            AppLogger.shared.log("Backend start skipped: invalid serviceURL=\(serviceURL)")
            return
        }

        if isPortListening(port: port) {
            AppLogger.shared.log("Backend already running on port \(port), skip auto-start")
            return
        }

        let rootURL = URL(fileURLWithPath: projectRoot, isDirectory: true)
        var isDir: ObjCBool = false
        guard FileManager.default.fileExists(atPath: rootURL.path, isDirectory: &isDir), isDir.boolValue else {
            AppLogger.shared.log("Backend start failed: invalid project root \(projectRoot)")
            return
        }

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        proc.arguments = ["python3", "-m", "notion_ext"]
        proc.currentDirectoryURL = rootURL
        proc.standardOutput = nil
        proc.standardError = nil
        proc.terminationHandler = { p in
            AppLogger.shared.log("Managed backend terminated. status=\(p.terminationStatus)")
        }

        do {
            try proc.run()
            process = proc
            didStartManagedProcess = true
            AppLogger.shared.log("Managed backend started. pid=\(proc.processIdentifier)")
        } catch {
            AppLogger.shared.log("Managed backend failed to start: \(error.localizedDescription)")
        }
    }

    func stopIfManaged() {
        guard didStartManagedProcess, let process else { return }
        AppLogger.shared.log("Stopping managed backend. pid=\(process.processIdentifier)")
        if process.isRunning {
            process.terminate()
            DispatchQueue.global().asyncAfter(deadline: .now() + 1.0) {
                if process.isRunning {
                    process.interrupt()
                }
            }
        }
        self.process = nil
        didStartManagedProcess = false
    }

    private func parsePort(from serviceURL: String) -> Int? {
        guard let url = URL(string: serviceURL) else { return nil }
        return url.port ?? 33189
    }

    private func isPortListening(port: Int) -> Bool {
        let fd = socket(AF_INET, SOCK_STREAM, 0)
        if fd < 0 { return false }
        defer { close(fd) }

        var addr = sockaddr_in()
        addr.sin_len = UInt8(MemoryLayout<sockaddr_in>.stride)
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_port = in_port_t(UInt16(port).bigEndian)
        inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr)

        let result = withUnsafePointer(to: &addr) { ptr in
            ptr.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockPtr in
                connect(fd, sockPtr, socklen_t(MemoryLayout<sockaddr_in>.stride))
            }
        }
        return result == 0
    }
}

