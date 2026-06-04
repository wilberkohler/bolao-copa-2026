import SwiftUI

struct RegrasView: View {
    var body: some View {
        NavigationStack {
            List {
                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        Label("Regras do Bolao", systemImage: "book.closed.fill")
                            .font(.title2.bold())
                            .foregroundStyle(.green)
                        Text("Pontuacao, prazos, desempates e orientacoes para jogar.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 6)
                }

                Section("Pontuacao") {
                    RuleScoreRow(title: "Placar exato", points: "10 pts", color: .green)
                    RuleScoreRow(title: "Vencedor correto + saldo correto", points: "7 pts", color: .blue)
                    RuleScoreRow(title: "Vencedor correto", points: "5 pts", color: .cyan)
                    RuleScoreRow(title: "Empate correto com placar diferente", points: "5 pts", color: .cyan)
                    RuleScoreRow(title: "Gols corretos de um dos times", points: "2 pts", color: .orange)
                    RuleScoreRow(title: "Classificado correto no mata-mata", points: "+3 pts", color: .purple)
                    RuleScoreRow(title: "Sem acertos relevantes", points: "0 pts", color: .red)
                }

                Section("Prazos") {
                    RuleBullet(text: "Todos os horarios exibidos estao em Brasilia.")
                    RuleBullet(text: "O prazo do palpite encerra as 23:59 do dia anterior ao jogo.")
                    RuleBullet(text: "Depois do prazo, o palpite fica bloqueado para edicao.")
                    RuleBullet(text: "Jogos sem palpite dentro do prazo contam como nao enviados.")
                }

                Section("Como acompanhar") {
                    RuleBullet(text: "Use Jogos para consultar datas, grupos e resultados.")
                    RuleBullet(text: "Use Palpites para preencher, salvar e limpar apenas os jogos permitidos.")
                    RuleBullet(text: "Use Ranking para acompanhar Geral, Fase de Grupos e Eliminatorias.")
                    RuleBullet(text: "O podium da tela inicial mostra os tres primeiros colocados atuais.")
                }

                Section("Ranking por etapas") {
                    RuleBullet(text: "Geral: soma todos os jogos cadastrados.")
                    RuleBullet(text: "Fase de Grupos: soma apenas os jogos antes do mata-mata.")
                    RuleBullet(text: "Eliminatorias: recomeca do zero na etapa eliminatoria e segue ate a final.")
                }

                Section("Desempate") {
                    NumberedRule(number: 1, text: "Maior pontuacao total.")
                    NumberedRule(number: 2, text: "Maior quantidade de placares exatos.")
                    NumberedRule(number: 3, text: "Maior quantidade de vencedores corretos.")
                    NumberedRule(number: 4, text: "Maior quantidade de saldos corretos.")
                    NumberedRule(number: 5, text: "Maior quantidade de classificados corretos.")
                    NumberedRule(number: 6, text: "Maior quantidade de palpites enviados.")
                    NumberedRule(number: 7, text: "Menor quantidade de palpites nao enviados.")
                    NumberedRule(number: 8, text: "Ordem alfabetica do apelido.")
                }

                Section("Versao para computador") {
                    RuleBullet(text: "Para tarefas mais detalhadas, como comparar tabelas grandes, administrar participantes ou revisar muitas informacoes de uma vez, acesse tambem a versao para computador.")
                    Link(destination: URL(string: "https://bolao2026-9jgh.onrender.com")!) {
                        Label("Abrir versao web", systemImage: "safari")
                    }
                }
            }
            .navigationTitle("Regras")
        }
    }
}

private struct RuleScoreRow: View {
    let title: String
    let points: String
    let color: Color

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title)
            Spacer(minLength: 12)
            Text(points)
                .font(.headline)
                .foregroundStyle(color)
        }
    }
}

private struct RuleBullet: View {
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
                .padding(.top, 2)
            Text(text)
        }
    }
}

private struct NumberedRule: View {
    let number: Int
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Text("\(number)")
                .font(.caption.bold())
                .foregroundStyle(.white)
                .frame(width: 24, height: 24)
                .background(.green, in: Circle())
            Text(text)
        }
    }
}
