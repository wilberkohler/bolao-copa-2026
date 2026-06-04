import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case badResponse
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "URL invalida."
        case .badResponse:
            return "Resposta invalida do servidor."
        case .server(let message):
            return message
        }
    }
}

final class APIClient {
    private let baseURL = URL(string: "https://bolao2026-9jgh.onrender.com")!
    private let session: URLSession
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    init(session: URLSession = .shared) {
        self.session = session
    }

    func login(email: String, senha: String) async throws -> UserProfile {
        let body = ["email": email, "senha": senha]
        let data = try JSONEncoder().encode(body)
        let envelope: APIEnvelope<UserProfile> = try await request("/api/v1/login", method: "POST", body: data)
        guard let user = envelope.user else {
            throw APIError.server(envelope.error ?? "Login nao realizado.")
        }
        return user
    }

    func gruposCadastro() async throws -> [GrupoCadastro] {
        let response: GruposCadastroResponse = try await request("/api/v1/grupos")
        return response.grupos
    }

    func privateGroupConfig() async throws -> PrivateGroupConfigResponse {
        try await request("/api/v1/grupos-privados/config")
    }

    func activatePrivateGroup(productId: String, transactionId: String, originalTransactionId: String?) async throws -> PrivateGroupActivationResponse {
        let payload = PrivateGroupActivationRequest(
            productId: productId,
            transactionId: transactionId,
            originalTransactionId: originalTransactionId,
            platform: "apple"
        )
        let data = try encoder.encode(payload)
        return try await request("/api/v1/grupos-privados/ativar", method: "POST", body: data)
    }

    func registrar(nome: String, email: String, apelido: String, senha: String, grupoId: Int?, codigoGrupo: String?) async throws -> UserProfile {
        let payload = RegisterRequest(
            nome: nome,
            email: email,
            apelido: apelido,
            senha: senha,
            grupoId: grupoId,
            codigoGrupo: codigoGrupo
        )
        let data = try encoder.encode(payload)
        let envelope: APIEnvelope<UserProfile> = try await request("/api/v1/registro", method: "POST", body: data)
        guard let user = envelope.user else {
            throw APIError.server(envelope.error ?? "Cadastro nao realizado.")
        }
        return user
    }

    func currentUser() async throws -> UserProfile {
        let envelope: APIEnvelope<UserProfile> = try await request("/api/v1/me")
        guard let user = envelope.user else {
            throw APIError.server(envelope.error ?? "Sessao nao encontrada.")
        }
        return user
    }

    func logout() async throws {
        let _: EmptyResponse = try await request("/api/v1/logout", method: "POST")
    }

    func reenviarConfirmacaoEmail() async throws {
        let _: EmptyResponse = try await request("/api/v1/reenviar-confirmacao-email", method: "POST")
    }

    func highlightTeamOptions() async throws -> HighlightTeamOptionsResponse {
        try await request("/api/v1/time-destaque")
    }

    func updateHighlightTeam(_ code: String) async throws -> HighlightTeamOptionsResponse {
        let payload = HighlightTeamRequest(timeDestaque: code)
        let data = try encoder.encode(payload)
        return try await request("/api/v1/time-destaque", method: "POST", body: data)
    }

    func excluirConta(senha: String, confirmacao: String) async throws {
        let payload = DeleteAccountRequest(senha: senha, confirmacao: confirmacao)
        let data = try encoder.encode(payload)
        let _: EmptyResponse = try await request("/api/v1/excluir-conta", method: "POST", body: data)
    }

    func dashboard() async throws -> DashboardResponse {
        try await request("/api/v1/dashboard")
    }

    func jogos() async throws -> [Jogo] {
        let response: JogosResponse = try await request("/api/v1/jogos")
        return response.jogos
    }

    func palpites() async throws -> [Jogo] {
        let response: JogosResponse = try await request("/api/v1/palpites")
        return response.jogos
    }

    func ranking(etapa: RankingEtapa = .geral) async throws -> [RankingItem] {
        let response: RankingResponse = try await request("/api/v1/ranking?etapa=\(etapa.rawValue)")
        return response.ranking
    }

    func salvarPalpite(jogoId: Int, golsA: Int, golsB: Int) async throws {
        try await salvarPalpites([SavePalpite(jogoId: jogoId, golsA: golsA, golsB: golsB, classificado: nil)])
    }

    func salvarPalpites(_ palpites: [SavePalpite]) async throws {
        let payload = SavePalpitesRequest(acao: "salvar", palpites: palpites)
        let data = try encoder.encode(payload)
        let _: GenericSaveResponse = try await request("/api/v1/palpites", method: "POST", body: data)
    }

    func limparPalpitesFuturos(jogoIds: [Int]) async throws -> Int {
        let payload = ClearFuturePalpitesRequest(acao: "limpar_futuros", jogoIds: jogoIds)
        let data = try encoder.encode(payload)
        let response: GenericSaveResponse = try await request("/api/v1/palpites", method: "POST", body: data)
        return response.cleared ?? 0
    }

    private func request<T: Decodable>(_ path: String, method: String = "GET", body: Data? = nil) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body {
            request.httpBody = body
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.badResponse
        }
        if !(200..<300).contains(http.statusCode) {
            if let error = try? decoder.decode(ServerError.self, from: data), let message = error.error {
                throw APIError.server(message)
            }
            throw APIError.server("Erro \(http.statusCode) no servidor.")
        }
        return try decoder.decode(T.self, from: data)
    }
}

struct EmptyResponse: Decodable {
    let ok: Bool
}

struct ServerError: Decodable {
    let ok: Bool?
    let error: String?
}

struct GenericSaveResponse: Decodable {
    let ok: Bool
    let saved: Int?
    let cleared: Int?
}
