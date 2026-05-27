import Foundation

struct APIEnvelope<T: Decodable>: Decodable {
    let ok: Bool
    let error: String?
    let user: T?
}

struct UserProfile: Decodable, Identifiable {
    let id: Int
    let nome: String
    let email: String
    let apelido: String?
    let ehAdmin: Bool
    let grupo: GrupoResumo?
    let competidor: CompetidorResumo?

    enum CodingKeys: String, CodingKey {
        case id, nome, email, apelido, grupo, competidor
        case ehAdmin = "eh_admin"
    }
}

struct GrupoResumo: Decodable, Identifiable {
    let id: Int
    let nome: String
}

struct CompetidorResumo: Decodable, Identifiable {
    let id: Int
    let nome: String
    let apelido: String
}

struct DashboardResponse: Decodable {
    let ok: Bool
    let summary: DashboardSummary
    let podium: [PodiumItem]
    let proximosJogos: [Jogo]

    enum CodingKeys: String, CodingKey {
        case ok, summary, podium
        case proximosJogos = "proximos_jogos"
    }
}

struct DashboardSummary: Decodable {
    let totalJogos: Int
    let palpitesEnviados: Int
    let totalCompetidores: Int

    enum CodingKeys: String, CodingKey {
        case totalJogos = "total_jogos"
        case palpitesEnviados = "palpites_enviados"
        case totalCompetidores = "total_competidores"
    }
}

struct PodiumItem: Decodable, Identifiable {
    var id: Int { posicao }
    let posicao: Int
    let nome: String
    let apelido: String
    let pontos: Int
}

struct JogosResponse: Decodable {
    let ok: Bool
    let jogos: [Jogo]
}

struct RankingResponse: Decodable {
    let ok: Bool
    let ranking: [RankingItem]
}

struct RankingItem: Decodable, Identifiable {
    var id: Int { posicao }
    let posicao: Int
    let nome: String
    let apelido: String
    let pontos: Int
    let placaresExatos: Int
    let vencedoresCorretos: Int
    let aproveitamento: Double

    enum CodingKeys: String, CodingKey {
        case posicao, nome, apelido, pontos, aproveitamento
        case placaresExatos = "placares_exatos"
        case vencedoresCorretos = "vencedores_corretos"
    }
}

struct Jogo: Decodable, Identifiable {
    let id: Int
    let fase: String
    let grupo: String?
    let dataJogo: String?
    let horaBrasilia: String?
    let timeA: String?
    let timeB: String?
    let siglaTimeA: String?
    let siglaTimeB: String?
    let estadio: String?
    let cidade: String?
    let status: String
    let editavel: Bool
    let resultado: Resultado?
    let palpite: Palpite?
    let pontuacao: Pontuacao?

    enum CodingKeys: String, CodingKey {
        case id, fase, grupo, status, editavel, resultado, palpite, pontuacao
        case dataJogo = "data_jogo"
        case horaBrasilia = "hora_brasilia"
        case timeA = "time_a"
        case timeB = "time_b"
        case siglaTimeA = "sigla_time_a"
        case siglaTimeB = "sigla_time_b"
        case estadio, cidade
    }
}

struct Resultado: Decodable {
    let golsA: Int
    let golsB: Int
    let classificado: String?

    enum CodingKeys: String, CodingKey {
        case golsA = "gols_a"
        case golsB = "gols_b"
        case classificado
    }
}

struct Palpite: Decodable {
    let golsA: Int?
    let golsB: Int?
    let classificado: String?

    enum CodingKeys: String, CodingKey {
        case golsA = "gols_a"
        case golsB = "gols_b"
        case classificado
    }
}

struct Pontuacao: Decodable {
    let pontos: Int
}

struct SavePalpite: Encodable {
    let jogoId: Int
    let golsA: Int
    let golsB: Int

    enum CodingKeys: String, CodingKey {
        case jogoId = "jogo_id"
        case golsA = "gols_a"
        case golsB = "gols_b"
    }
}

struct SavePalpitesRequest: Encodable {
    let acao: String?
    let palpites: [SavePalpite]
}

struct ClearFuturePalpitesRequest: Encodable {
    let acao: String
    let jogoIds: [Int]

    enum CodingKeys: String, CodingKey {
        case acao
        case jogoIds = "jogo_ids"
    }
}
