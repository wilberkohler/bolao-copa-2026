# Publicar no TestFlight pelo GitHub Actions

O workflow abaixo foi preparado:

```text
.github/workflows/ios-testflight.yml
```

Ele gera um archive iOS assinado, exporta o `.ipa` e envia para o TestFlight usando App Store Connect API.

## Secrets necessarios no GitHub

Crie em:

```text
GitHub > Repositorio > Settings > Secrets and variables > Actions > New repository secret
```

Secrets:

```text
IOS_APP_URL
APPLE_TEAM_ID
IOS_DISTRIBUTION_CERTIFICATE_BASE64
IOS_DISTRIBUTION_CERTIFICATE_PASSWORD
IOS_PROVISIONING_PROFILE_BASE64
IOS_PROVISIONING_PROFILE_NAME
KEYCHAIN_PASSWORD
APP_STORE_CONNECT_KEY_ID
APP_STORE_CONNECT_ISSUER_ID
APP_STORE_CONNECT_API_KEY_P8
```

## Criacao automatizada pelo PowerShell

Se tiver o GitHub CLI instalado e autenticado, rode:

```powershell
cd "C:\caminho\para\Bolao 2"
.\scripts\set_github_ios_secrets.ps1
```

Se o comando `gh` nao existir, instale o GitHub CLI:

```powershell
winget install --id GitHub.cli
```

Depois autentique:

```powershell
gh auth login
```

O script pede os valores no PowerShell, converte os arquivos `.p12` e `.mobileprovision` para base64 e envia tudo como repository secrets.

## O que e cada secret

`IOS_APP_URL`

URL HTTPS onde o Flask esta publicado.

Exemplo:

```text
https://bolao-copa-2026.seudominio.com
```

`APPLE_TEAM_ID`

Team ID da sua conta Apple Developer.

Onde ver:

```text
developer.apple.com/account > Membership details
```

`IOS_DISTRIBUTION_CERTIFICATE_BASE64`

Certificado Apple Distribution exportado como `.p12` e convertido para base64.

No Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\caminho\certificado.p12")) | Set-Clipboard
```

`IOS_DISTRIBUTION_CERTIFICATE_PASSWORD`

Senha usada ao exportar o certificado `.p12`.

`IOS_PROVISIONING_PROFILE_BASE64`

Provisioning Profile App Store, arquivo `.mobileprovision`, convertido para base64.

No Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\caminho\perfil.mobileprovision")) | Set-Clipboard
```

`IOS_PROVISIONING_PROFILE_NAME`

Nome do provisioning profile, exatamente como aparece na Apple Developer.

`KEYCHAIN_PASSWORD`

Uma senha qualquer criada por voce somente para o keychain temporario do GitHub Actions.

Exemplo:

```text
uma-senha-grande-e-unica
```

`APP_STORE_CONNECT_KEY_ID`

Key ID da chave criada em App Store Connect.

`APP_STORE_CONNECT_ISSUER_ID`

Issuer ID exibido na pagina de App Store Connect API.

`APP_STORE_CONNECT_API_KEY_P8`

Conteudo completo do arquivo `.p8` baixado do App Store Connect.

Inclua desde:

```text
-----BEGIN PRIVATE KEY-----
```

ate:

```text
-----END PRIVATE KEY-----
```

## Criar App Store Connect API Key

No App Store Connect:

```text
Users and Access > Integrations > App Store Connect API > Keys
```

Crie uma chave com permissao suficiente para upload de builds. Baixe o arquivo `.p8` imediatamente, porque a Apple permite baixar somente uma vez.

## Rodar publicacao

Depois de configurar todos os secrets:

```text
GitHub > Actions > iOS TestFlight > Run workflow
```

O build deve aparecer no App Store Connect em:

```text
My Apps > Bolao Copa 2026 > TestFlight
```

## Observacao

Este workflow assume o Bundle ID:

```text
br.com.kohler.bolao2026
```

O Bundle ID deve existir na Apple Developer e o provisioning profile precisa apontar para ele.
