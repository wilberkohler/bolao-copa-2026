import SwiftUI

struct PalpitesView: View {
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
                            PalpiteRow(jogo: jogo) {
                                await load()
                            }
                        }
                    }
                }
                if let errorMessage {
                    Text(errorMessage).foregroundStyle(.red)
                }
            }
            .navigationTitle("Palpites")
            .task { await load() }
            .refreshable { await load() }
        }
    }

    private func load() async {
        do {
            jogos = try await appState.api.palpites()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct PalpiteRow: View {
    @EnvironmentObject private var appState: AppState
    let jogo: Jogo
    let onSaved: () async -> Void

    @State private var golsA = ""
    @State private var golsB = ""
    @State private var message: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("\(jogo.timeA ?? "-") x \(jogo.timeB ?? "-")")
                .font(.headline)

            HStack {
                TextField("A", text: $golsA)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 56)
                Text("x")
                TextField("B", text: $golsB)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 56)
                Spacer()
                Button("Salvar") {
                    Task { await save() }
                }
                .buttonStyle(.bordered)
                .disabled(!jogo.editavel)
            }

            if let resultado = jogo.resultado {
                Text("Resultado: \(resultado.golsA) x \(resultado.golsB)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else if !jogo.editavel {
                Text("Palpite bloqueado")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if let message {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .onAppear {
            golsA = jogo.palpite?.golsA.map(String.init) ?? ""
            golsB = jogo.palpite?.golsB.map(String.init) ?? ""
        }
    }

    private func save() async {
        guard let a = Int(golsA), let b = Int(golsB) else {
            message = "Informe os dois placares."
            return
        }
        do {
            try await appState.api.salvarPalpite(jogoId: jogo.id, golsA: a, golsB: b)
            message = "Salvo."
            await onSaved()
        } catch {
            message = error.localizedDescription
        }
    }
}
