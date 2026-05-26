# Transformar o Bolao em aplicativo iOS

## Recomendacao

Para este projeto Flask, o caminho mais rapido e seguro e publicar o backend web em HTTPS e criar um app iOS wrapper com Capacitor.

Isso evita reescrever todo o sistema em Swift agora e preserva:

- Login e cadastro
- Palpites
- Ranking
- Administracao de grupos, jogos e resultados
- Banco de dados e regras de pontuacao existentes

Estrutura preparada: `mobile/ios-wrapper/`

## Fluxo completo

1. Publique a aplicacao Flask em um dominio HTTPS.
2. Ajuste `mobile/ios-wrapper/capacitor.config.json` com a URL final.
3. Em um Mac:

```bash
cd mobile/ios-wrapper
npm install
npm run ios:prepare
npm run ios:open
```

4. No Xcode, configure assinatura, icones e gere o build.

## Observacao importante

O app iOS nao deve apontar para `127.0.0.1` nem para uma pasta local do Windows. Ele precisa acessar uma URL HTTPS onde o Flask esteja publicado.

## Opcional: modo PWA no iPhone

O projeto tambem possui manifest e service worker. Enquanto o app nativo nao for publicado, os usuarios podem abrir a URL pelo Safari e usar Compartilhar > Adicionar a Tela de Inicio.

## Checklist para App Store

- URL de producao com HTTPS valido
- Politica de privacidade publicada
- Termos de uso, se necessario
- Icones iOS no Xcode
- Screenshots para iPhone
- Conta Apple Developer ativa
