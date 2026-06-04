import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState
    @AppStorage("appearanceMode") private var appearanceMode = "system"

    private var preferredScheme: ColorScheme? {
        switch appearanceMode {
        case "dark":
            return .dark
        case "light":
            return .light
        default:
            return nil
        }
    }

    var body: some View {
        Group {
            if appState.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .task {
            await appState.restoreSession()
        }
        .preferredColorScheme(preferredScheme)
        .overlay(alignment: .topTrailing) {
            ThemeToggleButton(appearanceMode: $appearanceMode)
                .padding(.top, 8)
                .padding(.trailing, 10)
        }
    }
}

private struct ThemeToggleButton: View {
    @Binding var appearanceMode: String

    private var isDark: Bool {
        appearanceMode == "dark"
    }

    var body: some View {
        Button {
            appearanceMode = isDark ? "light" : "dark"
        } label: {
            Image(systemName: isDark ? "sun.max.fill" : "moon.fill")
                .font(.caption.weight(.bold))
                .frame(width: 30, height: 30)
                .background(.thinMaterial, in: Circle())
                .overlay(Circle().stroke(Color.primary.opacity(0.12), lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(isDark ? "Usar tema claro" : "Usar tema escuro")
    }
}
