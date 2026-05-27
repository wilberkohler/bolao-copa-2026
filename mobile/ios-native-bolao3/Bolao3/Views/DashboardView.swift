import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var appState: AppState
    @State private var dashboard: DashboardResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            List {
                if let user = appState.user {
                    Section {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Ola, \(user.nome)")
                                .font(.title2.bold())
                            Text(user.ehAdmin ? "Administrador" : "Participante")
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                if let summary = dashboard?.summary {
                    Section("Resumo") {
                        StatRow(title: "Jogos", value: "\(summary.totalJogos)", icon: "calendar")
                        StatRow(title: "Palpites enviados", value: "\(summary.palpitesEnviados)", icon: "target")
                        StatRow(title: "Competidores", value: "\(summary.totalCompetidores)", icon: "person.3")
                    }
                }

                if let podium = dashboard?.podium, !podium.isEmpty {
                    Section("Podium atual") {
                        ForEach(podium) { item in
                            HStack {
                                Text("\(item.posicao)")
                                    .font(.headline)
                                    .frame(width: 28, height: 28)
                                    .background(.green.opacity(item.posicao == 1 ? 0.3 : 0.12), in: Circle())
                                VStack(alignment: .leading) {
                                    Text(item.nome).font(.headline)
                                    Text(item.apelido).font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer()
                                Text("\(item.pontos) pts").bold()
                            }
                        }
                    }
                }

                if let jogos = dashboard?.proximosJogos, !jogos.isEmpty {
                    Section("Proximos jogos") {
                        ForEach(jogos) { jogo in
                            JogoRow(jogo: jogo)
                        }
                    }
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage).foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Bolao 3")
            .toolbar {
                Button("Sair") {
                    Task { await appState.logout() }
                }
            }
            .overlay {
                if isLoading {
                    ProgressView()
                }
            }
            .task {
                await load()
            }
            .refreshable {
                await load()
            }
        }
    }

    private func load() async {
        isLoading = true
        errorMessage = nil
        do {
            dashboard = try await appState.api.dashboard()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}

struct StatRow: View {
    let title: String
    let value: String
    let icon: String

    var body: some View {
        HStack {
            Label(title, systemImage: icon)
            Spacer()
            Text(value).bold()
        }
    }
}
