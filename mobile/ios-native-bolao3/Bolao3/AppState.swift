import Foundation

@MainActor
final class AppState: ObservableObject {
    @Published var user: UserProfile?
    @Published var isLoading = false
    @Published var message: String?

    let api = APIClient()

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
        user = nil
    }
}
