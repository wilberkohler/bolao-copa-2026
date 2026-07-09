# Contexto importado da thread "Bolao"

Importado em 2026-06-25 a partir da thread antiga "Bolao".

## Projeto atual

- Pasta atual: `C:\Users\NTB-ENG\Documents\Bolao`
- Repositorio Git: `https://github.com/wilberkohler/bolao-copa-2026.git`
- Branch: `main`
- A pasta atual era um repo vazio; foi conectada ao `origin/main` e recebeu a base limpa do GitHub.
- O projeto antigo local completo estava em `C:\Users\NTB-ENG\Documents\Python\Bolao 2`.
- A pasta antiga ainda tinha alteracoes locais e artefatos gerados nao migrados automaticamente, incluindo `instance/bolao.db`, `__pycache__`, screenshots, `work/`, `dist/` e alguns templates modificados.

## App e stack

- App publico: `WK Futebol 2026`.
- Backend principal: Flask/Python em `app.py`, com SQLAlchemy e SQLite/Postgres conforme ambiente.
- Deploy web: Render, historicamente em `https://bolao2026-9jgh.onrender.com/login`.
- Mobile/iOS:
  - wrapper Capacitor em `mobile/ios-wrapper`;
  - app nativo SwiftUI em `mobile/ios-native-bolao3`;
  - StoreKit usado para compra dentro do app.

## Funcionalidades relevantes

- Login/cadastro, usuarios, grupos publicos e privados.
- Palpites/previsoes por jogo, com bloqueio por prazo.
- Ranking geral, ranking por fase e ranking por selecao/pais em destaque.
- Palpites do grupo ficam visiveis depois do prazo.
- Competidores inativos devem ficar fora do ranking.
- Grupo privado pago usa IAP da Apple, sem pagamento externo.
- Exclusao de conta existe no app e foi usada como resposta a pendencia da Apple.
- Relatorio de fim de rodada por e-mail inclui:
  - top 5 em formato de podio;
  - grafico diario de evolucao de participantes como PNG embutido;
  - `Pillow` foi adicionado ao `requirements.txt` para gerar o grafico.

## Commits recentes importantes

- `f674fd5 Add daily ranking evolution chart to reports`
- `22a86ab Clean private group legal wording`
- `65763b2 Show group predictions after deadline`
- `5e2e566 Render report top five as podium`
- `2084759 Hide inactive competitors from ranking`

## App Store Connect

- App Store Connect app id: `6773821649`.
- Nome usado na loja: `WK Futebol 2026`.
- Conta Apple/organizacao: `KOHLER ENGENHARIA LTDA`.
- A conta juridica foi considerada ativa no historico antigo.
- Contratos, dados fiscais e conta bancaria da Apple foram considerados ativos.
- IAP:
  - Nome: `Grupo Privado 2026`
  - Product ID: `private_group_2026`
  - Tipo: nao consumivel
  - Status visto no historico: aguardando/em revisao
  - Observacao: o primeiro IAP precisa ir junto com uma versao do app.

## Rejeicao e estrategia com a Apple

Historico de rejeicao envolveu principalmente:

- Guideline 2.3.6, metadata/classificacao etaria.
- Interpretacao da Apple de que o app contem "simulated gambling".
- Conta precisava ser organizacao, nao pessoa fisica.
- Remocao/neutralizacao de termos ligados a FIFA/Copa do Mundo e gambling real.
- Confirmacao de exclusao de conta.

Estado mais recente importado:

- Build usada na revisao/TestFlight: `1.0 (33)`.
- A Apple pediu `Frequent` para `Simulated Gambling`.
- Configuracao confirmada na conversa antiga:
  - Simulated Gambling / Simulacao de jogos de azar: `Frequent`
  - Contests / Competicoes: `Frequent`
  - Gambling / Jogos de azar real: `No`
  - Loot Boxes / Caixas de itens: `No`
- Classificacao final vista: `+18`, com Brasil como `A18`.
- A revisao foi reenviada em 2026-06-24 as 09:23 e ficou como `Aguardando revisao`.

## TestFlight

- Havia divergencia entre builds:
  - alguns testadores estavam na build `1.0 (27)`;
  - a build mais nova publicada/testada era `1.0 (33)`.
- Causa provavel: o link publico estava associado a um grupo que ainda entregava a build 27.
- Acao recomendada no historico:
  - abrir TestFlight > Grupos;
  - entrar no grupo do link publico;
  - adicionar a build 33;
  - remover/expirar a build 27 se possivel;
  - opcionalmente criar novo grupo/link publico com a build 33.

## Cuidados de texto e revisao

- Em metadados publicos, evitar termos como:
  - "FIFA";
  - "Copa do Mundo";
  - "aposta", "betting", "gambling", "odds", "cash", "dinheiro real", "premio financeiro".
- Nas notas para revisao da Apple, esses termos podem aparecer apenas para explicar que o app nao oferece gambling real.
- Preferir linguagem neutra:
  - "competicao recreativa";
  - "previsoes de futebol";
  - "rankings";
  - "grupos privados";
  - "selecao/pais em destaque";
  - "torneio mundial de futebol".

## Comandos uteis

```powershell
py -m pip install -r requirements.txt
py app.py
.\.venv\Scripts\python.exe -m py_compile app.py
```

Para deploy no Render, o fluxo historico foi commit/push no GitHub.

## Pendencias/observacoes importadas

- Verificar status atual da revisao na Apple antes de novas mudancas de App Store.
- Corrigir, se necessario, o grupo/link publico do TestFlight para entregar a build 33.
- A pasta antiga `Bolao 2` tinha mudancas locais nao commitadas; nao foram copiadas automaticamente para evitar trazer banco local, caches e artefatos.
- O README e alguns documentos antigos aparecem com caracteres quebrados; isso ja existia no repositorio e nao foi corrigido nesta importacao.
