import Foundation
import ServiceManagement

enum LoginItemError: LocalizedError {
    case unsupported
    case registrationFailed(Error)

    var errorDescription: String? {
        switch self {
        case .unsupported:
            return "当前运行方式不支持登录自启动，请从 .app 包启动后再开启。"
        case .registrationFailed(let error):
            return "登录自启动设置失败：\(error.localizedDescription)"
        }
    }
}

struct LoginItemManager {
    func sync(enabled: Bool) throws {
        guard #available(macOS 13.0, *) else {
            throw LoginItemError.unsupported
        }
        do {
            if enabled {
                try SMAppService.mainApp.register()
            } else {
                try SMAppService.mainApp.unregister()
            }
        } catch {
            throw LoginItemError.registrationFailed(error)
        }
    }
}
