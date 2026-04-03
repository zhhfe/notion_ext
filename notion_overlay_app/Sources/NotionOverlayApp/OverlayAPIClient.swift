import Foundation

enum OverlayAPIError: LocalizedError {
    case invalidURL
    case unexpectedResponse

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "服务地址无效。"
        case .unexpectedResponse:
            return "服务返回了无法识别的数据。"
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
    func updateReportSettings(settings: SettingsStore, dingtalkEnabled: Bool) async throws -> ReportSettingsPayload {
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
        request.httpBody = try encoder.encode(ReportSettingsPayload(dingtalkEnabled: dingtalkEnabled))

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw OverlayAPIError.unexpectedResponse
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return try decoder.decode(ReportSettingsPayload.self, from: data)
    }
}
