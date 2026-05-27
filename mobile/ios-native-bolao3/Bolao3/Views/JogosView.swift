import SwiftUI

struct JogosView: View {
    @EnvironmentObject private var appState: AppState
    @State private var jogos: [Jogo] = []
    @State private var errorMessage: String?

    var grupos: [String] {
        Array(Set(jogos.map { $0.grupo ?? "Outros" })).sorted()
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach(grupos, id: \.self) { grupo in
                    Section(grupo == "Outros" ? "Outros" : "Grupo \(grupo)") {
                        ForEach(jogos.filter { ($0.grupo ?? "Outros") == grupo }) { jogo in
                            JogoRow(jogo: jogo)
                        }
                    }
                }
                if let errorMessage {
                    Text(errorMessage).foregroundStyle(.red)
                }
            }
            .navigationTitle("Jogos")
            .task { await load() }
            .refreshable { await load() }
        }
    }

    private func load() async {
        do {
            jogos = try await appState.api.jogos()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct JogoRow: View {
    let jogo: Jogo

    private var isBrazilGame: Bool {
        jogo.timeA == "Brasil" || jogo.timeB == "Brasil" || jogo.siglaTimeA == "BRA" || jogo.siglaTimeB == "BRA"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("\(jogo.timeA ?? "-") x \(jogo.timeB ?? "-")")
                    .font(.headline)
                Spacer()
                if isBrazilGame {
                    Image(systemName: "star.fill")
                        .foregroundStyle(.yellow)
                }
            }
            HStack {
                Text(jogo.dataJogo ?? "")
                Text(jogo.horaBrasilia ?? "")
                Spacer()
                Text(jogo.status)
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
        .listRowBackground(isBrazilGame ? Color.yellow.opacity(0.14) : Color.clear)
    }
}
