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
                        PodiumView(items: podium)
                            .listRowInsets(EdgeInsets(top: 14, leading: 12, bottom: 14, trailing: 12))
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

struct PodiumView: View {
    let items: [PodiumItem]

    private var displayItems: [PodiumItem] {
        let ordered = items.sorted { $0.posicao < $1.posicao }
        if ordered.count >= 3 {
            return [ordered[1], ordered[0], ordered[2]]
        }
        if ordered.count == 2 {
            return [ordered[1], ordered[0]]
        }
        return ordered
    }

    var body: some View {
        HStack(alignment: .bottom, spacing: 10) {
            ForEach(displayItems) { item in
                PodiumColumn(item: item)
                    .frame(maxWidth: .infinity)
            }
        }
        .frame(minHeight: 190)
    }
}

struct PodiumColumn: View {
    let item: PodiumItem

    private var height: CGFloat {
        switch item.posicao {
        case 1: return 112
        case 2: return 82
        default: return 68
        }
    }

    private var color: Color {
        switch item.posicao {
        case 1: return .green
        case 2: return .blue
        default: return .orange
        }
    }

    var body: some View {
        VStack(spacing: 8) {
            VStack(spacing: 2) {
                Image(systemName: item.posicao == 1 ? "trophy.fill" : "medal.fill")
                    .foregroundStyle(color)
                Text(item.apelido)
                    .font(.caption.weight(.semibold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)
                Text("\(item.pontos) pts")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            VStack(spacing: 6) {
                Text("\(item.posicao)")
                    .font(.title3.bold())
                    .foregroundStyle(.white)
                    .frame(width: 34, height: 34)
                    .background(color, in: Circle())
                RoundedRectangle(cornerRadius: 8)
                    .fill(color.opacity(0.22))
                    .frame(height: height)
                    .overlay(alignment: .bottom) {
                        Text(item.nome)
                            .font(.caption2.weight(.semibold))
                            .lineLimit(2)
                            .multilineTextAlignment(.center)
                            .padding(6)
                    }
            }
        }
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
