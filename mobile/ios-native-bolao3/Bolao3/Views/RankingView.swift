import SwiftUI

struct RankingView: View {
    @EnvironmentObject private var appState: AppState
    @State private var ranking: [RankingItem] = []
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            List {
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
            .task { await load() }
            .refreshable { await load() }
        }
    }

    private func load() async {
        do {
            ranking = try await appState.api.ranking()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
