import SwiftUI

struct MainTabView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem {
                    Label("Inicio", systemImage: "house")
                }

            JogosView()
                .tabItem {
                    Label("Jogos", systemImage: "calendar")
                }

            PalpitesView()
                .tabItem {
                    Label("Palpites", systemImage: "target")
                }

            RankingView()
                .tabItem {
                    Label("Ranking", systemImage: "chart.bar")
                }
        }
    }
}
