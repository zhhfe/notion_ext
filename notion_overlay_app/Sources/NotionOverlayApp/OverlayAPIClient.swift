import Foundation

enum OverlayAPIError: LocalizedError {
    case invalidURL
    case unexpectedResponse
    case serverError(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "服务地址无效。"
        case .unexpectedResponse:
            return "服务返回了无法识别的数据。"
        case let .serverError(message):
            return message
        }
    }
}

struct OverlayAPIClient {
    @MainActor
    private func baseURL(settings: SettingsStore) throws -> String {
        let baseURL = settings.serviceURL
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard !baseURL.isEmpty else {
            throw OverlayAPIError.invalidURL
        }
        return baseURL
    }

    @MainActor
    func fetchSnapshot(settings: SettingsStore) async throws -> OverlayResponse {
        let endpoint = try baseURL(settings: settings) + "/report/overlay"
        guard let url = URL(string: endpoint) else {
            throw OverlayAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = settings.requestTimeout
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw OverlayAPIError.unexpectedResponse
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(OverlayResponse.self, from: data)
    }

    @MainActor
    func fetchReportSettings(settings: SettingsStore) async throws -> ReportSettingsPayload {
        let endpoint = try baseURL(settings: settings) + "/report/settings"
        guard let url = URL(string: endpoint) else {
            throw OverlayAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = settings.requestTimeout
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw OverlayAPIError.unexpectedResponse
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(ReportSettingsPayload.self, from: data)
    }

    @MainActor
    func updateReportSettings(
        settings: SettingsStore,
        dingtalkEnabled: Bool,
        remindersEnabled: Bool
    ) async throws -> ReportSettingsPayload {
        let endpoint = try baseURL(settings: settings) + "/report/settings"
        guard let url = URL(string: endpoint) else {
            throw OverlayAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = settings.requestTimeout
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(
            ReportSettingsPayload(
                dingtalkEnabled: dingtalkEnabled,
                remindersEnabled: remindersEnabled
            )
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw OverlayAPIError.unexpectedResponse
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(ReportSettingsPayload.self, from: data)
    }

    @MainActor
    func completeItem(settings: SettingsStore, kind: OverlayCompleteKind, id: String, value: Bool) async throws -> CompleteItemResponsePayload {
        let endpoint = try baseURL(settings: settings) + "/report/complete"
        guard let url = URL(string: endpoint) else {
            throw OverlayAPIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = settings.requestTimeout
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(CompleteItemRequestPayload(kind: kind.rawValue, id: id, value: value))

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw OverlayAPIError.unexpectedResponse
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let payload = (try? decoder.decode(CompleteItemResponsePayload.self, from: data))
            ?? CompleteItemResponsePayload(ok: false, error: "服务返回了无法识别的数据。")

        guard http.statusCode == 200, payload.ok else {
            throw OverlayAPIError.serverError(payload.error ?? "写回失败，请稍后重试。")
        }
        return payload
    }
}
