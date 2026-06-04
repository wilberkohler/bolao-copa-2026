# Wrapper iOS (Capacitor)

Este diretorio prepara um app iOS para o Bolao Futebol 2026 sem reescrever o backend Flask.

## Como funciona

- O app iOS abre a URL HTTPS do seu sistema web hospedado.
- O backend continua sendo este projeto Flask.
- O app pode ser publicado na App Store como um container nativo.
- Esta abordagem reaproveita as telas atuais, login, ranking, palpites e regras do sistema web.

## Pre-requisitos

- Mac com Xcode instalado
- Node.js 20+
- Conta Apple Developer
- Aplicacao Flask publicada com HTTPS (Render, Railway, VPS etc.)

## Passos

1. Publique o backend Flask em HTTPS.

O iOS nao deve apontar para `http://127.0.0.1:5000`, porque isso seria o proprio iPhone. Use uma URL publica, por exemplo:

```text
https://bolao-copa-2026.seudominio.com
```

2. Ajuste a URL no arquivo `capacitor.config.json`:

```json
"server": {
  "url": "https://bolao-copa-2026.seudominio.com",
  "cleartext": false
}
```

3. No terminal, dentro desta pasta:

```bash
npm install
npm run ios:prepare
npm run ios:open
```

4. No Xcode:

- Defina Team e Signing.
- Ajuste Bundle Identifier, se necessario.
- Configure icones de app e splash.
- Build e execute no simulador/dispositivo.

5. Publicacao:

- Archive no Xcode.
- Envie para App Store Connect.
- Preencha metadados e envie para revisao.

## Comandos uteis

```bash
npm run cap:doctor
npm run cap:sync
npm run cap:open:ios
```

Depois de alterar `capacitor.config.json`, rode:

```bash
npm run cap:sync
```

## Observacoes importantes

- iOS exige HTTPS para conteudo remoto por padrao (ATS).
- Se sua URL nao for HTTPS, a Apple pode rejeitar o app.
- Para notificacoes push, Login com Apple e recursos nativos, voce pode adicionar plugins Capacitor depois.
- Veja tambem `APP_STORE_CHECKLIST.md`.
