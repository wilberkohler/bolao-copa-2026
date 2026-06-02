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

                    Text("Use as opcoes para alternar o ranking. A selecao em destaque usa o pais escolhido na tela Conta.")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                ForEach(ranking) { item in
                    DisclosureGroup {
                        VStack(spacing: 8) {
                            RankingStatRow(title: "Placares exatos", value: "\(item.placaresExatos)")
                            RankingStatRow(title: "Vencedores corretos", value: "\(item.vencedoresCorretos)")
                            RankingStatRow(title: "Saldos corretos", value: "\(item.saldosCorretos ?? 0)")
                            RankingStatRow(title: "Classificados corretos", value: "\(item.classificadosCorretos ?? 0)")
                            RankingStatRow(title: "Palpites enviados", value: "\(item.palpitesEnviados ?? 0)")
                            RankingStatRow(title: "Nao enviados", value: "\(item.palpitesNaoEnviados ?? 0)")
                            RankingStatRow(title: "Aproveitamento", value: "\(item.aproveitamento)%")
                            RankingStatRow(title: "Ultima pontuacao", value: "\(item.ultimaPontuacao ?? 0) pts")
                        }
                        .padding(.top, 8)
                    } label: {
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

private struct RankingStatRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .fontWeight(.semibold)
        }
        .font(.subheadline)
    }
}
