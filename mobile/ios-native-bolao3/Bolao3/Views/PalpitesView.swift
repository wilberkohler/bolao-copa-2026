import SwiftUI

struct PalpitesView: View {
    @EnvironmentObject private var appState: AppState
    @State private var jogos: [Jogo] = []
    @State private var selectedGrupo = ""
    @State private var drafts: [Int: DraftPalpite] = [:]
    @State private var isLoading = false
    @State private var message: String?
    @State private var errorMessage: String?
    @FocusState private var focusedField: PalpiteField?

    private var grupos: [String] {
        Array(Set(jogos.map { $0.grupo ?? "Outros" })).sorted()
    }

    private var jogosDaAba: [Jogo] {
        jogos.filter { ($0.grupo ?? "Outros") == selectedGrupo }
    }

    private var jogosEditaveisDaAba: [Jogo] {
        jogosDaAba.filter { $0.editavel }
    }

    private var pendentesDaAba: Int {
        jogosEditaveisDaAba.filter { jogo in
            let draft = drafts[jogo.id] ?? DraftPalpite()
            return draft.golsA.trimmingCharacters(in: .whitespaces).isEmpty ||
                draft.golsB.trimmingCharacters(in: .whitespaces).isEmpty
        }.count
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if !grupos.isEmpty {
                    groupTabs
                    actionBar
                    Divider()
                }

                List {
                    if let message {
                        Text(message)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(.footnote)
                            .foregroundStyle(.red)
                    }

                    ForEach(jogosDaAba) { jogo in
                        PalpiteGameRow(
                            jogo: jogo,
                            draft: Binding(
                                get: { drafts[jogo.id] ?? DraftPalpite() },
                                set: { drafts[jogo.id] = $0 }
                            ),
                            focusedField: $focusedField
                        )
                    }
                }
                .listStyle(.plain)
                .overlay {
                    if isLoading {
                        ProgressView()
                    }
                }
                .refreshable {
                    await load(force: true)
                }
            }
            .navigationTitle("Palpites")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await load(force: true) }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(isLoading)
                }

                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Ocultar teclado") {
                        focusedField = nil
                    }
                }
            }
            .task { await load() }
        }
    }

    private var groupTabs: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(grupos, id: \.self) { grupo in
                    Button {
                        selectedGrupo = grupo
                    } label: {
                        Text(grupo == "Outros" ? "Outros" : "Grupo \(grupo)")
                            .font(.subheadline.weight(.semibold))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(selectedGrupo == grupo ? Color.green : Color(.secondarySystemBackground))
                            .foregroundStyle(selectedGrupo == grupo ? .white : .primary)
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 10)
        }
    }

    private var actionBar: some View {
        VStack(spacing: 10) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(selectedGrupo == "Outros" ? "Outros" : "Grupo \(selectedGrupo)")
                        .font(.headline)
                    Text("\(jogosDaAba.count) jogos | \(pendentesDaAba) pendentes")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }

            HStack(spacing: 8) {
                Button {
                    preencherVaziosDaAba()
                } label: {
                    Label("Preencher vazios", systemImage: "wand.and.stars")
                }
                .buttonStyle(.bordered)
                .disabled(jogosEditaveisDaAba.isEmpty)

                Button {
                    Task { await limparFuturosDaAba() }
                } label: {
                    Label("Limpar futuros", systemImage: "trash")
                }
                .buttonStyle(.bordered)
                .tint(.red)
                .disabled(jogosEditaveisDaAba.isEmpty || isLoading)
            }

            Button {
                Task { await salvarAba() }
            } label: {
                Label("Salvar palpites desta aba", systemImage: "checkmark.circle")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(jogosEditaveisDaAba.isEmpty || isLoading)
        }
        .padding(.horizontal)
        .padding(.bottom, 12)
    }

    private func load(force: Bool = false) async {
        isLoading = true
        do {
            let loaded = try await appState.loadPalpites(force: force)
            jogos = loaded
            rebuildDrafts(from: loaded)
            if selectedGrupo.isEmpty || !grupos.contains(selectedGrupo) {
                selectedGrupo = grupos.first ?? ""
            }
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func rebuildDrafts(from jogos: [Jogo]) {
        var updated = drafts
        for jogo in jogos {
            updated[jogo.id] = DraftPalpite(
                golsA: jogo.palpite?.golsA.map(String.init) ?? "",
                golsB: jogo.palpite?.golsB.map(String.init) ?? ""
            )
        }
        drafts = updated
    }

    private func preencherVaziosDaAba() {
        for jogo in jogosEditaveisDaAba {
            var draft = drafts[jogo.id] ?? DraftPalpite()
            if draft.golsA.trimmingCharacters(in: .whitespaces).isEmpty {
                draft.golsA = String(Int.random(in: 0...4))
            }
            if draft.golsB.trimmingCharacters(in: .whitespaces).isEmpty {
                draft.golsB = String(Int.random(in: 0...4))
            }
            drafts[jogo.id] = draft
        }
        message = "Campos vazios preenchidos para a aba ativa."
    }

    private func limparFuturosDaAba() async {
        let jogoIds = jogosEditaveisDaAba.map(\.id)
        guard !jogoIds.isEmpty else { return }

        isLoading = true
        do {
            let cleared = try await appState.api.limparPalpitesFuturos(jogoIds: jogoIds)
            for id in jogoIds {
                drafts[id] = DraftPalpite()
            }
            appState.invalidateAfterPalpiteChange()
            message = "\(cleared) palpite(s) futuro(s) limpo(s) nesta aba."
            await load(force: true)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func salvarAba() async {
        var payload: [SavePalpite] = []
        var invalidos = 0

        for jogo in jogosEditaveisDaAba {
            let draft = drafts[jogo.id] ?? DraftPalpite()
            let aText = draft.golsA.trimmingCharacters(in: .whitespaces)
            let bText = draft.golsB.trimmingCharacters(in: .whitespaces)
            if aText.isEmpty && bText.isEmpty {
                continue
            }
            guard let golsA = Int(aText), let golsB = Int(bText), golsA >= 0, golsB >= 0 else {
                invalidos += 1
                continue
            }
            payload.append(SavePalpite(jogoId: jogo.id, golsA: golsA, golsB: golsB))
        }

        if payload.isEmpty {
            message = invalidos > 0 ? "Revise placares invalidos." : "Nao ha palpites para salvar nesta aba."
            return
        }

        isLoading = true
        do {
            try await appState.api.salvarPalpites(payload)
            appState.invalidateAfterPalpiteChange()
            message = "\(payload.count) palpite(s) salvo(s) nesta aba."
            await load(force: true)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}

private struct DraftPalpite {
    var golsA = ""
    var golsB = ""
}

private enum PalpiteField: Hashable {
    case golsA(Int)
    case golsB(Int)
}

private struct PalpiteGameRow: View {
    let jogo: Jogo
    @Binding var draft: DraftPalpite
    let focusedField: FocusState<PalpiteField?>.Binding

    private var isBrazilGame: Bool {
        jogo.timeA == "Brasil" || jogo.timeB == "Brasil" || jogo.siglaTimeA == "BRA" || jogo.siglaTimeB == "BRA"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        TeamCell(name: jogo.timeA ?? "-", code: jogo.siglaTimeA)
                        Text("x")
                            .font(.headline)
                            .foregroundStyle(.secondary)
                        TeamCell(name: jogo.timeB ?? "-", code: jogo.siglaTimeB)
                        if isBrazilGame {
                            Image(systemName: "star.fill")
                                .foregroundStyle(.yellow)
                        }
                    }
                    Text("\(jogo.dataJogo ?? "") \(jogo.horaBrasilia ?? "")")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text(jogo.status)
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 5)
                    .background(jogo.editavel ? Color.green.opacity(0.16) : Color.gray.opacity(0.16), in: Capsule())
            }

            HStack(spacing: 10) {
                TextField("A", text: $draft.golsA)
                    .keyboardType(.numberPad)
                    .focused(focusedField, equals: .golsA(jogo.id))
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 58)
                    .disabled(!jogo.editavel)

                Text("x")
                    .foregroundStyle(.secondary)

                TextField("B", text: $draft.golsB)
                    .keyboardType(.numberPad)
                    .focused(focusedField, equals: .golsB(jogo.id))
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 58)
                    .disabled(!jogo.editavel)

                Spacer()

                if let pontuacao = jogo.pontuacao {
                    Text("\(pontuacao.pontos) pts")
                        .font(.subheadline.weight(.bold))
                }
            }

            if let resultado = jogo.resultado {
                Text("Resultado: \(resultado.golsA) x \(resultado.golsB)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else if !jogo.editavel {
                Text("Prazo encerrado")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 6)
        .listRowBackground(isBrazilGame ? Color.yellow.opacity(0.12) : Color.clear)
    }
}
