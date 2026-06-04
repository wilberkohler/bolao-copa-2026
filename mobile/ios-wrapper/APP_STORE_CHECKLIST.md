# Checklist iOS / App Store

## Antes de abrir no Xcode

- Publicar o Flask em uma URL HTTPS valida.
- Trocar `https://SEU_DOMINIO_AQUI` em `capacitor.config.json` pela URL final.
- Confirmar que login, cadastro, palpites, ranking e solicitacao de exclusao funcionam pela URL publicada.
- Rodar `npm install`.
- Em um Mac, rodar `npm run ios:prepare`.

## No Xcode

- Abrir com `npm run ios:open`.
- Configurar Team em Signing & Capabilities.
- Conferir Bundle Identifier: `br.com.kohler.bolao2026`.
- Gerar AppIcon em todos os tamanhos exigidos.
- Testar em simulador e em iPhone real.
- Criar Archive e enviar para App Store Connect.

## Metadados obrigatorios

- Politica de privacidade publicada em uma URL publica.
- Texto curto explicando que o app gerencia palpites recreativos de futebol em 2026.
- Screenshots para os tamanhos de iPhone exigidos pela Apple.
- Informar se ha login obrigatorio.
- Informar que o usuario pode solicitar exclusao de conta em `/solicitar-exclusao-dados`.
