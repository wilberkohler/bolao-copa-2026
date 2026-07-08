import SwiftUI

struct PalpitesView: View {
    @EnvironmentObject private var appState: AppState
    @State private var jogos: [Jogo] = []
    @State private var selectedGrupo = ""
    @State private var playoffStartIndex = 0
    @State private var drafts: [Int: DraftPalpite] = [:]
    @State private var isLoading = false
    @State private var message: String?
    @State private var errorMessage: String?
    @FocusState private var focusedField: PalpiteField?

    private let knockoutVisualOrder: [Int: Int] = [
        74: 0, 77: 1, 89: 2,
        73: 3, 75: 4, 90: 5,
        97: 6,
        83: 7, 84: 8, 93: 9,
        81: 10, 82: 11, 94: 12,
        98: 13, 101: 14,
        76: 15, 78: 16, 91: 17,
        79: 18, 80: 19, 92: 20,
        99: 21,
        86: 22, 88: 23, 95: 24,
        85: 25, 87: 26, 96: 27,
        100: 28, 102: 29, 103: 30, 104: 31
    ]

    private var grupos: [String] {
        let values = Array(Set(jogos.map { groupKey(for: $0) }))
        return values.sorted { lhs, rhs in
            if lhs == "Outros" { return true }
            if rhs == "Outros" { return false }
            return lhs < rhs
        }
    }

    private var jogosDaAba: [Jogo] {
        jogos.filter { groupKey(for: $0) == selectedGrupo }
    }

    private var jogosEditaveisDaAba: [Jogo] {
        jogosDaAba.filter { $0.editavel }
    }

    private var isKnockoutTab: Bool {
        selectedGrupo == "Outros" || jogosDaAba.contains { $0.mataMata }
    }

    private var pendentesDaAba: Int {
        jogosEditaveisDaAba.filter { jogo in
            let draft = drafts[jogo.id] ?? DraftPalpite()
            let missingScore = draft.golsA.trimmingCharacters(in: .whitespaces).isEmpty ||
                draft.golsB.trimmingCharacters(in: .whitespaces).isEmpty
            let missingQualified = jogo.mataMata && draft.classificado.trimmingCharacters(in: .whitespaces).isEmpty
            return missingScore || missingQualified
        }.count
    }

    private var playoffPhases: [String] {
        orderedPhases(from: jogosDaAba.filter { $0.mataMata })
    }

    private var visiblePlayoffPhases: [String] {
        guard !playoffPhases.isEmpty else { return [] }
        if playoffStartIndex >= 4 {
            return Array(playoffPhases.dropFirst(4))
        }
        return Array(playoffPhases.dropFirst(playoffStartIndex).prefix(3))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if !grupos.isEmpty {
                    groupTabs
                    actionBar
                    Divider()
                }

                content
                    .overlay {
                        if isLoading {
                            ProgressView()
                                .padding()
                                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                        }
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
            .onChange(of: selectedGrupo) { _, _ in
                playoffStartIndex = 0
            }
        }
    }

    @ViewBuilder
    private var content: some View {
        if isKnockoutTab {
            knockoutContent
        } else {
            regularList
        }
    }

    private var regularList: some View {
        List {
            messages

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
        .refreshable {
            await load(force: true)
        }
    }

    private var knockoutContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                messages
                    .padding(.horizontal)

                playoffPhaseTabs

                ScrollView(.horizontal, showsIndicators: true) {
                    let layouts = playoffPhaseLayouts()
                    HStack(alignment: .top, spacing: 28) {
                        ForEach(Array(layouts.enumerated()), id: \.element.phase) { offset, layout in
                            KnockoutPhaseColumn(
                                layout: layout,
                                isFirstVisible: offset == 0,
                                isLastVisible: offset == layouts.count - 1 || layout.phaseIndex == 4,
                                drafts: $drafts,
                                focusedField: $focusedField
                            )
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 14)
                }
            }
        }
        .refreshable {
            await load(force: true)
        }
        .background(Color(.systemGroupedBackground))
    }

    @ViewBuilder
    private var messages: some View {
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
    }

    private var groupTabs: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(grupos, id: \.self) { grupo in
                    Button {
                        selectedGrupo = grupo
                    } label: {
                        Text(tabTitle(for: grupo))
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

    private var playoffPhaseTabs: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(0..<playoffTabCount, id: \.self) { index in
                    Button {
                        playoffStartIndex = index
                    } label: {
                        Text(playoffTabTitle(index))
                            .font(.subheadline.weight(.bold))
                            .padding(.horizontal, 14)
                            .padding(.vertical, 9)
                            .background(playoffStartIndex == index ? Color.green : Color(.secondarySystemBackground))
                            .foregroundStyle(playoffStartIndex == index ? .white : .primary)
                            .clipShape(Capsule())
                            .shadow(color: .black.opacity(playoffStartIndex == index ? 0.14 : 0.06), radius: 6, y: 3)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 4)
        }
    }

    private var actionBar: some View {
        VStack(spacing: 10) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(tabTitle(for: selectedGrupo))
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

    private var playoffTabCount: Int {
        min(5, max(playoffPhases.count, 1))
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
                golsB: jogo.palpite?.golsB.map(String.init) ?? "",
                classificado: jogo.palpite?.classificado ?? ""
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
            let classificado = draft.classificado.trimmingCharacters(in: .whitespaces)

            if aText.isEmpty && bText.isEmpty && classificado.isEmpty {
                continue
            }
            guard let golsA = Int(aText), let golsB = Int(bText), golsA >= 0, golsB >= 0 else {
                invalidos += 1
                continue
            }
            payload.append(SavePalpite(
                jogoId: jogo.id,
                golsA: golsA,
                golsB: golsB,
                classificado: classificado.isEmpty ? nil : classificado
            ))
        }

        if payload.isEmpty {
            message = invalidos > 0 ? "Revise placares ou classificados invalidos." : "Nao ha palpites para salvar nesta aba."
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

    private func groupKey(for jogo: Jogo) -> String {
        jogo.mataMata ? "Outros" : (jogo.grupo ?? "Outros")
    }

    private func tabTitle(for grupo: String) -> String {
        grupo == "Outros" ? "Eliminatorias" : "Grupo \(grupo)"
    }

    private func orderedPhases(from jogos: [Jogo]) -> [String] {
        var result: [String] = []
        for jogo in jogos.sorted(by: sortByDateAndNumber) {
            if !result.contains(jogo.fase) {
                result.append(jogo.fase)
            }
        }
        return result
    }

    private func sortByDateAndNumber(_ lhs: Jogo, _ rhs: Jogo) -> Bool {
        if lhs.mataMata || rhs.mataMata {
            let leftOrder = lhs.numeroPartida.flatMap { knockoutVisualOrder[$0] } ?? Int.max
            let rightOrder = rhs.numeroPartida.flatMap { knockoutVisualOrder[$0] } ?? Int.max
            if leftOrder != rightOrder {
                return leftOrder < rightOrder
            }
        }

        if let leftNumber = lhs.numeroPartida, let rightNumber = rhs.numeroPartida, leftNumber != rightNumber {
            return leftNumber < rightNumber
        }
        return lhs.id < rhs.id
    }

    private func playoffTabTitle(_ index: Int) -> String {
        switch index {
        case 0:
            return "Rodada de 32"
        case 1:
            return "Oitavas de Final"
        case 2:
            return "Quartas de Final"
        case 3:
            return "Semifinal"
        default:
            return "Terceiro Lugar & Final"
        }
    }

    private func playoffPhaseLayouts() -> [KnockoutPhaseLayout] {
        let visibleStartIndex = playoffStartIndex >= 4 ? 4 : playoffStartIndex
        var layouts: [KnockoutPhaseLayout] = []

        for (offset, phase) in visiblePlayoffPhases.enumerated() {
            let phaseIndex = visibleStartIndex + offset
            let phaseGames = jogosDaAba
                .filter { $0.fase == phase }
                .sorted(by: sortByDateAndNumber)
            let positions = positionsForPhase(phaseGames, previous: layouts.last)
            layouts.append(KnockoutPhaseLayout(
                phase: phase,
                phaseIndex: phaseIndex,
                matches: positions,
                height: layoutHeight(for: positions)
            ))
        }

        return layouts
    }

    private func positionsForPhase(_ jogos: [Jogo], previous: KnockoutPhaseLayout?) -> [PositionedKnockoutMatch] {
        guard let previous, !previous.matches.isEmpty, !jogos.isEmpty else {
            return jogos.enumerated().map { index, jogo in
                PositionedKnockoutMatch(jogo: jogo, top: CGFloat(index) * (KnockoutLayout.cardHeight + KnockoutLayout.cardGap))
            }
        }

        let ratio = max(1, previous.matches.count / max(jogos.count, 1))
        var result: [PositionedKnockoutMatch] = []

        for (index, jogo) in jogos.enumerated() {
            let start = min(index * ratio, previous.matches.count - 1)
            let end = min((index + 1) * ratio, previous.matches.count)
            let sources = Array(previous.matches[start..<max(start + 1, end)])
            let sourceCenter = sources.reduce(CGFloat(0)) { partial, source in
                partial + source.centerY
            } / CGFloat(max(sources.count, 1))

            var top = max(0, sourceCenter - (KnockoutLayout.cardHeight / 2))
            if let last = result.last {
                top = max(top, last.top + KnockoutLayout.cardHeight + KnockoutLayout.cardGap)
            }
            result.append(PositionedKnockoutMatch(jogo: jogo, top: top))
        }

        return result
    }

    private func layoutHeight(for positions: [PositionedKnockoutMatch]) -> CGFloat {
        guard let bottom = positions.map({ $0.top + KnockoutLayout.cardHeight }).max() else {
            return KnockoutLayout.cardHeight
        }
        return bottom
    }
}

private struct DraftPalpite {
    var golsA = ""
    var golsB = ""
    var classificado = ""
}

private enum PalpiteField: Hashable {
    case golsA(Int)
    case golsB(Int)
}

private struct PositionedKnockoutMatch: Identifiable {
    let jogo: Jogo
    let top: CGFloat

    var id: Int { jogo.id }
    var centerY: CGFloat { top + (KnockoutLayout.cardHeight / 2) }
}

private struct KnockoutPhaseLayout: Identifiable, Hashable {
    let phase: String
    let phaseIndex: Int
    let matches: [PositionedKnockoutMatch]
    let height: CGFloat

    var id: String { phase }

    static func == (lhs: KnockoutPhaseLayout, rhs: KnockoutPhaseLayout) -> Bool {
        lhs.phase == rhs.phase && lhs.phaseIndex == rhs.phaseIndex && lhs.matches.map(\.id) == rhs.matches.map(\.id)
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(phase)
        hasher.combine(phaseIndex)
        hasher.combine(matches.map(\.id))
    }
}

private enum KnockoutLayout {
    static let cardHeight: CGFloat = 318
    static let cardWidth: CGFloat = 310
    static let cardGap: CGFloat = 16
    static let connectorWidth: CGFloat = 28
}

private struct KnockoutPhaseColumn: View {
    let layout: KnockoutPhaseLayout
    let isFirstVisible: Bool
    let isLastVisible: Bool
    @Binding var drafts: [Int: DraftPalpite]
    let focusedField: FocusState<PalpiteField?>.Binding

    var body: some View {
        ZStack(alignment: .top) {
            ForEach(layout.matches) { match in
                KnockoutMatchCard(
                    jogo: match.jogo,
                    isFirstVisible: isFirstVisible,
                    isLastVisible: isLastVisible,
                    draft: Binding(
                        get: { drafts[match.jogo.id] ?? DraftPalpite() },
                        set: { drafts[match.jogo.id] = $0 }
                    ),
                    focusedField: focusedField
                )
                .offset(y: match.top)
            }
        }
        .frame(width: KnockoutLayout.cardWidth, height: layout.height, alignment: .top)
    }
}

private struct KnockoutMatchCard: View {
    let jogo: Jogo
    let isFirstVisible: Bool
    let isLastVisible: Bool
    @Binding var draft: DraftPalpite
    let focusedField: FocusState<PalpiteField?>.Binding
    @State private var showGroupPredictions = false

    private var teamA: String { jogo.timeA ?? "-" }
    private var teamB: String { jogo.timeB ?? "-" }
    private var groupPredictions: [PalpiteGrupo] {
        jogo.palpitesGrupo ?? []
    }
    private var submittedGroupPredictions: [PalpiteGrupo] {
        groupPredictions.filter { $0.palpite != nil }
    }
    private var groupPredictionsAvailable: Bool {
        jogo.palpitesGrupoDisponiveis == true || !groupPredictions.isEmpty
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(matchDate)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                Spacer()
                if let numero = jogo.numeroPartida {
                    Text("#\(numero)")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                }
            }

            VStack(spacing: 8) {
                KnockoutTeamPredictionRow(
                    name: teamA,
                    code: jogo.siglaTimeA,
                    score: $draft.golsA,
                    field: .golsA(jogo.id),
                    isEditable: jogo.editavel,
                    focusedField: focusedField
                )

                HStack {
                    Spacer()
                    Text("x")
                        .font(.headline.weight(.bold))
                        .foregroundStyle(.secondary)
                        .frame(width: 48)
                    Spacer()
                }

                KnockoutTeamPredictionRow(
                    name: teamB,
                    code: jogo.siglaTimeB,
                    score: $draft.golsB,
                    field: .golsB(jogo.id),
                    isEditable: jogo.editavel,
                    focusedField: focusedField
                )
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Clasf. (mata-mata)")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)

                if jogo.editavel {
                    Picker("Classificado", selection: $draft.classificado) {
                        Text("-- Classificado correto --").tag("")
                        Text(teamA).tag(teamA)
                        Text(teamB).tag(teamB)
                    }
                    .pickerStyle(.menu)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 8))
                } else {
                    Text(draft.classificado.isEmpty ? "-" : draft.classificado)
                        .font(.subheadline.weight(.semibold))
                }
            }

            Divider()

            HStack {
                VStack(alignment: .leading, spacing: 5) {
                    Text(deadlineText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)

                    if groupPredictionsAvailable {
                        Button {
                            showGroupPredictions = true
                        } label: {
                            HStack(spacing: 5) {
                                Image(systemName: "person.2")
                                Text("Palpites do grupo")
                                Text("\(submittedGroupPredictions.count)")
                                    .font(.caption2.weight(.bold))
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.gray, in: Capsule())
                            }
                            .font(.caption.weight(.semibold))
                        }
                        .buttonStyle(.plain)
                        .foregroundStyle(.green)
                        .accessibilityLabel("Palpites do grupo, \(submittedGroupPredictions.count) enviados")
                    }
                }
                Spacer()
                if let pontuacao = jogo.pontuacao {
                    Text("\(pontuacao.pontos) pts")
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(Color.green, in: Capsule())
                        .foregroundStyle(.white)
                } else {
                    Text(jogo.status)
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(Color.gray, in: Capsule())
                        .foregroundStyle(.white)
                }
            }
        }
        .padding(14)
        .frame(height: KnockoutLayout.cardHeight, alignment: .top)
        .background(Color(.systemBackground), in: RoundedRectangle(cornerRadius: 8))
        .overlay(alignment: .leading) {
            Rectangle()
                .fill(Color.yellow)
                .frame(width: 4)
        }
        .overlay(alignment: .leading) {
            if !isFirstVisible {
                Rectangle()
                    .fill(Color(.systemGray3))
                    .frame(width: KnockoutLayout.connectorWidth, height: 2)
                    .offset(x: -KnockoutLayout.connectorWidth)
            }
        }
        .overlay(alignment: .trailing) {
            if !isLastVisible {
                Rectangle()
                    .fill(Color(.systemGray3))
                    .frame(width: KnockoutLayout.connectorWidth, height: 2)
                    .offset(x: KnockoutLayout.connectorWidth)
            }
        }
        .shadow(color: .black.opacity(0.12), radius: 7, y: 3)
        .sheet(isPresented: $showGroupPredictions) {
            GroupPredictionsSheet(jogo: jogo)
                .presentationDetents([.medium, .large])
        }
    }

    private var matchDate: String {
        let date = jogo.dataExibicao ?? jogo.dataJogo ?? ""
        let time = jogo.horaExibicao ?? jogo.horaBrasilia ?? ""
        return "\(date) - \(time)"
    }

    private var deadlineText: String {
        guard let prazo = jogo.prazoPalpiteExibicao, !prazo.isEmpty else {
            return jogo.editavel ? "Aberto para palpite" : "Prazo encerrado"
        }
        return "Prazo: \(prazo)"
    }
}

private struct KnockoutTeamPredictionRow: View {
    let name: String
    let code: String?
    @Binding var score: String
    let field: PalpiteField
    let isEditable: Bool
    let focusedField: FocusState<PalpiteField?>.Binding

    var body: some View {
        HStack(spacing: 8) {
            RoundedRectangle(cornerRadius: 4)
                .stroke(Color(.systemGray3), lineWidth: 1)
                .frame(width: 20, height: 20)

            VStack(alignment: .leading, spacing: 2) {
                Text(name)
                    .font(.headline)
                    .lineLimit(2)
                    .minimumScaleFactor(0.82)
                if let code {
                    Text(code)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                }
            }

            Spacer(minLength: 8)

            TextField("-", text: $score)
                .keyboardType(.numberPad)
                .multilineTextAlignment(.center)
                .focused(focusedField, equals: field)
                .textFieldStyle(.roundedBorder)
                .frame(width: 58)
                .disabled(!isEditable)
        }
    }
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
                    Text("\(jogo.dataExibicao ?? jogo.dataJogo ?? "") \(jogo.horaExibicao ?? jogo.horaBrasilia ?? "")")
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

            GroupPredictionsList(jogo: jogo)
        }
        .padding(.vertical, 6)
        .listRowBackground(isBrazilGame ? Color.yellow.opacity(0.12) : Color.clear)
    }
}

private struct GroupPredictionsList: View {
    let jogo: Jogo

    private var groupPredictions: [PalpiteGrupo] {
        jogo.palpitesGrupo ?? []
    }

    private var submitted: [PalpiteGrupo] {
        groupPredictions.filter { $0.palpite != nil }
    }
    private var groupPredictionsAvailable: Bool {
        jogo.palpitesGrupoDisponiveis == true || !groupPredictions.isEmpty
    }

    var body: some View {
        if groupPredictionsAvailable {
            DisclosureGroup {
                VStack(alignment: .leading, spacing: 8) {
                    if submitted.isEmpty {
                        Text("Nenhum palpite enviado pelo grupo.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(submitted) { item in
                            HStack {
                                Text(item.apelido + (item.isCurrent ? " (voce)" : ""))
                                    .font(.caption.weight(item.isCurrent ? .bold : .regular))
                                Spacer()
                                if let palpite = item.palpite {
                                    Text("\(scoreText(palpite.golsA)) x \(scoreText(palpite.golsB))")
                                        .font(.caption.weight(.bold))
                                    if jogo.mataMata, let classificado = palpite.classificado {
                                        Text(classificado)
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(.top, 6)
            } label: {
                Label("Palpites do grupo (\(submitted.count))", systemImage: "person.2")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.green)
            }
        }
    }

    private func scoreText(_ value: Int?) -> String {
        value.map(String.init) ?? "-"
    }
}

private struct GroupPredictionsSheet: View {
    let jogo: Jogo
    @Environment(\.dismiss) private var dismiss

    private var groupPredictions: [PalpiteGrupo] {
        jogo.palpitesGrupo ?? []
    }

    private var submitted: [PalpiteGrupo] {
        groupPredictions.filter { $0.palpite != nil }
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    if submitted.isEmpty {
                        Text("Nenhum palpite enviado pelo grupo.")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(submitted) { item in
                            HStack(alignment: .top, spacing: 12) {
                                VStack(alignment: .leading, spacing: 3) {
                                    Text(item.apelido + (item.isCurrent ? " (voce)" : ""))
                                        .font(.subheadline.weight(item.isCurrent ? .bold : .semibold))
                                    if jogo.mataMata, let classificado = item.palpite?.classificado, !classificado.isEmpty {
                                        Text("Classificado: \(classificado)")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                Spacer()
                                if let palpite = item.palpite {
                                    Text("\(scoreText(palpite.golsA)) x \(scoreText(palpite.golsB))")
                                        .font(.headline.weight(.bold))
                                        .monospacedDigit()
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                } header: {
                    Text(matchTitle)
                }
            }
            .navigationTitle("Palpites do grupo")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Fechar") {
                        dismiss()
                    }
                }
            }
        }
    }

    private var matchTitle: String {
        "\(jogo.timeA ?? "-") x \(jogo.timeB ?? "-")"
    }

    private func scoreText(_ value: Int?) -> String {
        value.map(String.init) ?? "-"
    }
}
