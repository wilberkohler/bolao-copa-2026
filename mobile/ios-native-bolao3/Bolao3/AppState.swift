import Foundation

@MainActor
final class AppState: ObservableObject {
    @Published var user: UserProfile?
    @Published var isLoading = false
    @Published var message: String?
    @Published var dashboardCache: DashboardResponse?
    @Published var jogosCache: [Jogo] = []
    @Published var palpitesCache: [Jogo] = []
    @Published var rankingCache: [RankingEtapa: [RankingItem]] = [:]

    let api = APIClient()
    private var dashboardLoadedAt: Date?
    private var jogosLoadedAt: Date?
    private var palpitesLoadedAt: Date?
    private var rankingLoadedAt: [RankingEtapa: Date] = [:]
    private let cacheLifetime: TimeInterval = 120

    var isAuthenticated: Bool {
        user != nil
    }

    func login(email: String, senha: String) async {
        isLoading = true
        message = nil
        do {
            user = try await api.login(email: email, senha: senha)
        } catch {
            message = error.localizedDescription
        }
        isLoading = false
    }

    func registrar(nome: String, email: String, apelido: String, senha: String, grupoId: Int?, codigoGrupo: String?) async {
        isLoading = true
        message = nil
        do {
            user = try await api.registrar(
                nome: nome,
                email: email,
                apelido: apelido,
                senha: senha,
                grupoId: grupoId,
                codigoGrupo: codigoGrupo
            )
            clearCaches()
        } catch {
            message = error.localizedDescription
        }
        isLoading = false
    }

    func restoreSession() async {
        isLoading = true
        do {
            user = try await api.currentUser()
        } catch {
            user = nil
        }
        isLoading = false
    }

    func logout() async {
        try? await api.logout()
        clearCaches()
        user = nil
    }

    func clearCaches() {
        dashboardCache = nil
        jogosCache = []
        palpitesCache = []
        rankingCache = [:]
        dashboardLoadedAt = nil
        jogosLoadedAt = nil
        palpitesLoadedAt = nil
        rankingLoadedAt = [:]
    }

    func loadDashboard(force: Bool = false) async throws -> DashboardResponse {
        if !force, let dashboardCache, isFresh(dashboardLoadedAt) {
            return dashboardCache
        }
        let loaded = try await api.dashboard()
        dashboardCache = loaded
        dashboardLoadedAt = Date()
        return loaded
    }

    func loadJogos(force: Bool = false) async throws -> [Jogo] {
        if !force, !jogosCache.isEmpty, isFresh(jogosLoadedAt) {
            return jogosCache
        }
        let loaded = try await api.jogos()
        jogosCache = loaded
        jogosLoadedAt = Date()
        return loaded
    }

    func loadPalpites(force: Bool = false) async throws -> [Jogo] {
        if !force, !palpitesCache.isEmpty, isFresh(palpitesLoadedAt) {
            return palpitesCache
        }
        let loaded = try await api.palpites()
        palpitesCache = loaded
        palpitesLoadedAt = Date()
        return loaded
    }

    func loadRanking(etapa: RankingEtapa = .geral, force: Bool = false) async throws -> [RankingItem] {
        if !force, let cached = rankingCache[etapa], !cached.isEmpty, isFresh(rankingLoadedAt[etapa]) {
            return cached
        }
        let loaded = try await api.ranking(etapa: etapa)
        rankingCache[etapa] = loaded
        rankingLoadedAt[etapa] = Date()
        return loaded
    }

    func invalidateAfterPalpiteChange() {
        dashboardLoadedAt = nil
        palpitesLoadedAt = nil
        rankingLoadedAt = [:]
    }

    private func isFresh(_ loadedAt: Date?) -> Bool {
        guard let loadedAt else {
            return false
        }
        return Date().timeIntervalSince(loadedAt) < cacheLifetime
    }
}
