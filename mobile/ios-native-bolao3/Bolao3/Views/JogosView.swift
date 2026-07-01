import SwiftUI

struct JogosView: View {
    @EnvironmentObject private var appState: AppState
    @State private var jogos: [Jogo] = []
    @State private var errorMessage: String?
    @State private var pendingScrollTarget: Int?
    @State private var didInitialScroll = false

    private var jogosOrdenados: [Jogo] {
        jogos.sorted(by: Self.sortByDateAndNumber)
    }

    private var secoesPorData: [DateGamesSection] {
        var sections: [DateGamesSection] = []

        for jogo in jogosOrdenados {
            let key = jogo.dataJogo ?? jogo.dataExibicao ?? "sem-data"
            let title = Self.sectionTitle(for: jogo)
            if let lastIndex = sections.indices.last, sections[lastIndex].id == key {
                sections[lastIndex].jogos.append(jogo)
            } else {
                sections.append(DateGamesSection(id: key, title: title, jogos: [jogo]))
            }
        }

        return sections
    }

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                List {
                    ForEach(secoesPorData) { section in
                        Section(section.title) {
                            ForEach(section.jogos) { jogo in
                                JogoRow(jogo: jogo)
                                    .id(jogo.id)
                            }
                        }
                    }
                    if let errorMessage {
                        Text(errorMessage).foregroundStyle(.red)
                    }
                }
                .navigationTitle("Jogos")
                .task { await load() }
                .refreshable { await load(force: true, alignToToday: false) }
                .onChange(of: pendingScrollTarget) { target in
                    guard let target else { return }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                        withAnimation(.easeOut(duration: 0.35)) {
                            proxy.scrollTo(target, anchor: .top)
                        }
                        pendingScrollTarget = nil
                    }
                }
            }
        }
    }

    private func load(force: Bool = false, alignToToday: Bool = true) async {
        do {
            let loaded = try await appState.loadJogos(force: force)
            jogos = loaded
            errorMessage = nil
            if alignToToday, !didInitialScroll, let target = Self.initialScrollTarget(in: loaded) {
                didInitialScroll = true
                pendingScrollTarget = target
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private static func sortByDateAndNumber(_ lhs: Jogo, _ rhs: Jogo) -> Bool {
        let lhsDate = scheduledDate(for: lhs) ?? .distantFuture
        let rhsDate = scheduledDate(for: rhs) ?? .distantFuture
        if lhsDate != rhsDate {
            return lhsDate < rhsDate
        }
        return (lhs.numeroPartida ?? lhs.id) < (rhs.numeroPartida ?? rhs.id)
    }

    private static func initialScrollTarget(in jogos: [Jogo]) -> Int? {
        let ordered = jogos.sorted(by: sortByDateAndNumber)
        let calendar = Calendar.current
        let now = Date()

        if let today = ordered.first(where: { jogo in
            guard let date = scheduledDate(for: jogo) else { return false }
            return calendar.isDate(date, inSameDayAs: now)
        }) {
            return today.id
        }

        if let next = ordered.first(where: { jogo in
            guard let date = scheduledDate(for: jogo) else { return false }
            return date >= calendar.startOfDay(for: now)
        }) {
            return next.id
        }

        return ordered.last?.id
    }

    private static func sectionTitle(for jogo: Jogo) -> String {
        guard let date = scheduledDate(for: jogo) else {
            return jogo.dataExibicao ?? jogo.dataJogo ?? "Sem data"
        }

        let calendar = Calendar.current
        if calendar.isDateInToday(date) {
            return "Hoje"
        }
        if calendar.isDateInTomorrow(date) {
            return "Amanha"
        }
        return sectionDateFormatter.string(from: date)
    }

    private static func scheduledDate(for jogo: Jogo) -> Date? {
        guard let data = jogo.dataJogo, !data.isEmpty else { return nil }
        let hora = (jogo.horaBrasilia?.isEmpty == false ? jogo.horaBrasilia : "00:00") ?? "00:00"
        return dateTimeFormatter.date(from: "\(data) \(hora)") ?? dayFormatter.date(from: data)
    }

    private static let dateTimeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter
    }()

    private static let dayFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    private static let sectionDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "pt_BR")
        formatter.dateFormat = "dd/MM/yyyy"
        return formatter
    }()
}

struct JogoRow: View {
    let jogo: Jogo

    private var isBrazilGame: Bool {
        jogo.timeA == "Brasil" || jogo.timeB == "Brasil" || jogo.siglaTimeA == "BRA" || jogo.siglaTimeB == "BRA"
    }

    private var groupLabel: String {
        if let grupo = jogo.grupo, !grupo.isEmpty {
            return "Grupo \(grupo)"
        }
        return jogo.fase
    }

    private var statusLabel: String {
        if let pontuacao = jogo.pontuacao {
            return "Pontuado - \(pontuacao.pontos) pts"
        }
        if jogo.resultado != nil {
            return "Resultado"
        }
        if jogo.editavel {
            return "Aberto"
        }
        return jogo.status
    }

    private var statusColor: Color {
        if jogo.pontuacao != nil {
            return .green
        }
        if jogo.resultado != nil {
            return .blue
        }
        if jogo.editavel {
            return .green
        }
        return .gray
    }

    private var dateTimeLabel: String {
        let date = jogo.dataExibicao ?? jogo.dataJogo ?? ""
        let time = jogo.horaExibicao ?? jogo.horaBrasilia ?? ""
        return [date, time].filter { !$0.isEmpty }.joined(separator: " ")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                TeamCell(name: jogo.timeA ?? "-", code: jogo.siglaTimeA)
                ScoreCell(resultado: jogo.resultado)
                TeamCell(name: jogo.timeB ?? "-", code: jogo.siglaTimeB)
                Spacer()
                if isBrazilGame {
                    Image(systemName: "star.fill")
                        .foregroundStyle(.yellow)
                }
            }

            HStack {
                Text(dateTimeLabel)
                    .lineLimit(1)
                    .minimumScaleFactor(0.82)
                Spacer()
                StatusBadge(text: statusLabel, color: statusColor)
            }
            .font(.caption)
            .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                Text(groupLabel)
                if let cidade = jogo.cidade, !cidade.isEmpty {
                    Text(cidade)
                }
            }
            .font(.caption2)
            .foregroundStyle(.secondary)

            if jogo.mataMata, let classificado = jogo.resultado?.classificado, !classificado.isEmpty {
                Text("Classificado: \(classificado)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
        .listRowBackground(isBrazilGame ? Color.yellow.opacity(0.14) : Color.clear)
    }
}

private struct DateGamesSection: Identifiable {
    let id: String
    let title: String
    var jogos: [Jogo]
}

private struct ScoreCell: View {
    let resultado: Resultado?

    var body: some View {
        if let resultado {
            Text("\(resultado.golsA) x \(resultado.golsB)")
                .font(.headline.monospacedDigit())
                .foregroundStyle(.primary)
                .frame(minWidth: 52)
        } else {
            Text("x")
                .font(.headline)
                .foregroundStyle(.secondary)
                .frame(minWidth: 28)
        }
    }
}

private struct StatusBadge: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold))
            .foregroundStyle(color)
            .lineLimit(1)
            .minimumScaleFactor(0.8)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.12), in: Capsule())
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
