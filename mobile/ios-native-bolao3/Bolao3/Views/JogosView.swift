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
            .refreshable { await load(force: true) }
        }
    }

    private func load(force: Bool = false) async {
        do {
            jogos = try await appState.loadJogos(force: force)
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
                TeamCell(name: jogo.timeA ?? "-", code: jogo.siglaTimeA)
                Text("x")
                    .font(.headline)
                    .foregroundStyle(.secondary)
                TeamCell(name: jogo.timeB ?? "-", code: jogo.siglaTimeB)
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

struct TeamCell: View {
    let name: String
    let code: String?

    private var isBrazil: Bool {
        name == "Brasil" || code == "BRA"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(name)
                .font(.headline)
                .lineLimit(1)
                .minimumScaleFactor(0.72)
            if let code, !code.isEmpty {
                Text(code)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
        .frame(minWidth: 86, alignment: .leading)
        .background(isBrazil ? Color.yellow.opacity(0.45) : Color.clear, in: RoundedRectangle(cornerRadius: 8))
        .overlay {
            if isBrazil {
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.yellow.opacity(0.75), lineWidth: 1)
            }
        }
    }
}
