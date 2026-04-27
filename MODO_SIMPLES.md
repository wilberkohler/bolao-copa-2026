# ⚡ MODO SIMPLES: Bolão Copa 2026 - Um Clique!

## 🎯 O Objetivo

O sistema agora é **tão simples** que qualquer pessoa consegue instalar sem conhecimento técnico:

1. **Clique** em `BolaoInstalador.exe`
2. **Clique** "Sim" na confirmação
3. **Aguarde** 2-3 minutos
4. **Pronto!** Aplicação rodando

## ✨ Por que é diferente agora

| Antes | Agora |
|-------|-------|
| ❌ Precisa Python | ✅ Sem Python |
| ❌ Múltiplos scripts | ✅ Um arquivo só |
| ❌ Linhas de comando | ✅ Clique duplo |
| ❌ Erros de dependências | ✅ Tudo automático |
| ❌ Usuário não consegue | ✅ Qualquer um consegue |

## 📦 Arquivo Final

```
BolaoInstalador.exe  (~ 70-100 MB)
```

**Tudo** necessário está dentro desse um arquivo:
- Python runtime
- Todas as libraries (Flask, SQLAlchemy, etc)
- Aplicação completa (templates, banco de dados)
- Scripts de instalação como serviço

## 🚀 Como Distribuir

### Opção 1: Link de Download
```
Crie um link de download para a pasta "dist"
Usuarios fazem download de BolaoInstalador.exe
Executam e pronto!
```

### Opção 2: Pen Drive
```
Copie a pasta "dist" inteira
Leve em pen drives
Qualquer máquina Windows 10/11 funciona
```

### Opção 3: SharePoint
```
Faça upload da pasta "dist" no SharePoint
Compartilhe o link
Usuarios baixam e executam
```

## 📋 Pré-requisitos

- ✅ Windows 10 ou 11
- ✅ 500 MB de espaço em disco
- ✅ Acesso de Administrador (1 vez)
- ✅ Nada mais!

## 🔧 Instalação

### Passo 1: Download
```
1. Clique no link de download
2. Aguarde baixar BolaoInstalador.exe
3. Veja na pasta Downloads
```

### Passo 2: Instalar
```
1. Clique duplo em BolaoInstalador.exe
2. Clique "Sim" na caixa de diálogo
3. Deixa rodar (2-3 minutos)
```

### Passo 3: Usar
```
1. Navegador abre automaticamente
2. URL: http://localhost:5055
3. Pronto para usar!
```

## ✅ Automático

O script `BolaoInstalador.exe` faz tudo:

1. ✅ Instala dependências Python
2. ✅ Copia arquivos da aplicação
3. ✅ Registra como serviço Windows
4. ✅ Abre porta no Firewall
5. ✅ Inicia automaticamente
6. ✅ Abre navegador

Tudo **sem** o usuário fazer nada além de clicar "Sim"!

## 🌐 Acesso Compartilhado

Após instalação em **qualquer máquina**, acesse de qualquer outra:

```
http://NAEST202502:5055    (Mesmo nome de máquina)
http://[IP]:5055           (Por IP interno)
```

## 🔄 Reiniciar o Serviço

Se precisar parar/iniciar:

```powershell
Get-Service BolaoCopa2026           # Ver status
Stop-Service BolaoCopa2026          # Parar
Start-Service BolaoCopa2026         # Iniciar
Restart-Service BolaoCopa2026       # Reiniciar
```

## ❌ Remover

Se precisar desinstalar:

```powershell
Stop-Service BolaoCopa2026
sc.exe delete BolaoCopa2026
netsh advfirewall firewall delete rule name="Bolao Copa 2026"
```

Ou procure `BolaoInstalador.exe` novamente com `-uninstall`:

```powershell
.\BolaoInstalador.exe -uninstall
```

## 📌 Arquitetura Final

```
Distribuir:
dist/
├── BolaoInstalador.exe         ← Execute isto!
├── app.py, models.py
├── templates/, static/
├── windows_service.py
└── ... (tudo que precisa)

Resultado na máquina do usuário:
C:\Program Files\BolaoInstalador\
├── Aplicação rodando como Serviço Windows
├── Acessível em http://localhost:5055
├── Compartilhado pela rede
└── Auto-reinicia em caso de falha
```

## 🎁 Benefícios

✅ **Zero conhecimento técnico**  
✅ **Um clique só**  
✅ **Sem erros de Python**  
✅ **Sem dependências**  
✅ **Portável (pen drive)**  
✅ **Profissional**  
✅ **Fácil compartilhamento**  

## 🚀 Próximas Ações

1. **Aguarde** compilação terminar (BolaoInstalador.exe criado)
2. **Copie** pasta `dist` para SharePoint
3. **Compartilhe** link com usuários
4. **Usuários** executam `BolaoInstalador.exe`
5. **Pronto!** Copa 2026 rodando!

---

**Simples. Eficiente. Profissional. 🎯**
