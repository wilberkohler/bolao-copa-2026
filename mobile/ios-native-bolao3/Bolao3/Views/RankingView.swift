import SwiftUI

struct RankingView: View {
    @EnvironmentObject private var appState: AppState
    @State private var ranking: [RankingItem] = []
    @State private var etapa: RankingEtapa = .geral
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Picker("Etapa", selection: $etapa) {
                        ForEach(RankingEtapa.allCases) { item in
                            Text(item.title).tag(item)
                        }
                    }
                    .pickerStyle(.segmented)

                    Text(etapa.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                ForEach(ranking) { item in
                    HStack {
                        Text("\(item.posicao)")
                            .font(.headline)
                            .frame(width: 32, height: 32)
                            .background(.green.opacity(item.posicao <= 3 ? 0.22 : 0.08), in: Circle())
                        VStack(alignment: .leading) {
                            Text(item.nome).font(.headline)
                            Text("\(item.placaresExatos) exatos | \(item.vencedoresCorretos) vencedores")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text("\(item.pontos) pts").bold()
                    }
                }
                if let errorMessage {
                    Text(errorMessage).foregroundStyle(.red)
                }
            }
            .navigationTitle("Ranking")
            .task(id: etapa) { await load() }
            .refreshable { await load(force: true) }
        }
    }

    private func load(force: Bool = false) async {
        do {
            ranking = try await appState.loadRanking(etapa: etapa, force: force)
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
