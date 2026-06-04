# Bolao Futebol 2026

Versao iOS nativa em SwiftUI, mantida em paralelo ao app web/Capacitor atual.

## Estrutura

- `project.yml`: definicao do projeto para XcodeGen.
- `Bolao3/`: codigo SwiftUI do app.
- `.github/workflows/ios-native-bolao3-build.yml`: build em nuvem para simulador iOS.

## Primeiro objetivo

Esta primeira versao conecta no backend Flask via API JSON:

- `POST /api/v1/login`
- `GET /api/v1/dashboard`
- `GET /api/v1/jogos`
- `GET /api/v1/palpites`
- `POST /api/v1/palpites`
- `GET /api/v1/ranking`

Ela ainda nao substitui o app TestFlight atual. Para publicar em paralelo no TestFlight, o proximo passo e criar um novo Bundle ID e um novo provisioning profile para `br.com.kohler.bolao2026.bolao3`.
