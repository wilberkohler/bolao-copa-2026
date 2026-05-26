# Build iOS em nuvem com GitHub Actions

Este projeto inclui o workflow:

```text
.github/workflows/ios-cloud-build.yml
```

Ele roda em um runner macOS do GitHub, gera o projeto iOS do Capacitor e compila o app para iOS Simulator. Essa etapa valida que o projeto iOS esta correto mesmo sem um Mac local.

## 1. Criar repositorio no GitHub

No GitHub, crie um repositorio novo, por exemplo:

```text
bolao-copa-2026
```

Depois, no terminal local dentro da pasta do projeto:

```powershell
git remote add origin https://github.com/SEU_USUARIO/bolao-copa-2026.git
git branch -M main
git add .
git commit -m "Preparar build iOS em nuvem"
git push -u origin main
```

Se o repositorio local ja tiver commits, ajuste apenas o remote e faca o push.

## 2. Rodar o build iOS

No GitHub:

1. Abra o repositorio.
2. Entre em Actions.
3. Selecione iOS Cloud Build.
4. Clique em Run workflow.
5. Opcionalmente, informe a URL HTTPS do Flask em `app_url`.

## 3. Configurar URL por secret

Quando tiver a URL HTTPS definitiva do backend Flask, voce pode salvar no GitHub:

```text
Settings > Secrets and variables > Actions > New repository secret
```

Nome:

```text
IOS_APP_URL
```

Valor:

```text
https://seu-dominio.com
```

O workflow usara essa URL automaticamente quando `app_url` nao for informado manualmente.

## 4. Publicacao na App Store

Este primeiro workflow valida build de simulador sem assinatura.

Para TestFlight/App Store, ainda sera necessario configurar:

- Certificado Apple Distribution
- Provisioning Profile
- App Store Connect API Key
- Bundle ID registrado na Apple Developer
- Workflow de archive/export/upload

Esses dados devem entrar no GitHub como secrets. Nao coloque senhas, certificados ou chaves diretamente no codigo.

