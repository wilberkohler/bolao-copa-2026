# 📋 BOLÃO COPA 2026 - Sistema de Instalação Completo

## 🎯 Resumo

Você agora tem um **sistema de instalação unificado** que automatiza toda a configuração do Bolão Copa 2026 como serviço Windows com uma única execução.

## 📦 O que foi criado

### Dentro da Pasta Bolao-Copa-2026 (SharePoint):

1. **`INSTALAR_COMPLETO.ps1`** 
   - Script PowerShell (RECOMENDADO)
   - Instalação completa com auto-elevação
   - Melhor interface e formatação
   - Suporta Windows 10/11

2. **`INSTALAR_COMPLETO.bat`**
   - Script Batch (ALTERNATIVA)
   - Interface mais simples
   - Compatível com Windows 7/8/10/11

3. **`GUIA_INSTALACAO.md`**
   - Guia detalhado em markdown
   - Solução de problemas
   - Comandos úteis

4. **`INICIO_RAPIDO.md`**
   - Quick start para iniciantes
   - Explica qual script usar

5. **`CONFIG_INSTALACAO.json`**
   - Template de configuração customizável
   - Explica cada parâmetro
   - Para usuários avançados

## 🚀 Como usar

### OPÇÃO 1: PowerShell (Recomendado)

```powershell
# Abrir arquivo: INSTALAR_COMPLETO.ps1
# Clique direito → Executar com PowerShell
# OU no PowerShell:

.\INSTALAR_COMPLETO.ps1                  # Instalar
.\INSTALAR_COMPLETO.ps1 -Action remove   # Remover
.\INSTALAR_COMPLETO.ps1 -Action status   # Ver status
```

### OPÇÃO 2: Batch (Alternativa)

```batch
REM Clique direito → Executar como administrador
REM OU no CMD:

INSTALAR_COMPLETO.bat           REM Instalar
INSTALAR_COMPLETO.bat remove    REM Remover
INSTALAR_COMPLETO.bat status    REM Ver status
```

## ✅ O que cada script faz automaticamente

1. ✅ **Verifica pré-requisitos**
   - Python instalado
   - Privilégios de administrador

2. ✅ **Auto-eleva privilégios**
   - Sem necessidade de clique direito manual
   - Transparente para o usuário

3. ✅ **Instala dependências**
   - Flask, SQLAlchemy, Waitress
   - pywin32 para serviço Windows

4. ✅ **Registra serviço Windows**
   - Inicia automaticamente no boot
   - Nome: `BolaoCopa2026`

5. ✅ **Configura auto-restart**
   - 3 tentativas em intervalos de 60s
   - Reinicia automaticamente se falhar

6. ✅ **Abre firewall**
   - Porta 5055 automaticamente
   - Permite acesso pela rede

7. ✅ **Inicia o serviço**
   - Aplicação pronta para usar
   - Acesso em http://NAEST202502:5055

8. ✅ **Exibe URLs de acesso**
   - Localmente: http://localhost:5055
   - Pela rede: http://NAEST202502:5055
   - Por IP: http://[seu-ip]:5055

## 📝 Pré-requisitos

- ✅ Windows 7 ou superior (Win 10/11 recomendado)
- ✅ Python 3.8+ (instale de https://www.python.org)
- ✅ Acesso de Administrador
- ✅ Conexão com internet (só na primeira instalação)

## 🌐 Acessar após instalação

```
Localmente:     http://localhost:5055
Pela rede:      http://NAEST202502:5055
```

## ⚙️ Após a instalação - Comandos úteis

```powershell
# PowerShell:
Get-Service BolaoCopa2026              # Ver status
Start-Service BolaoCopa2026            # Iniciar
Stop-Service BolaoCopa2026             # Parar
Restart-Service BolaoCopa2026          # Reiniciar
```

```batch
REM Batch/CMD:
sc query BolaoCopa2026                 REM Ver status
net start BolaoCopa2026                REM Iniciar
net stop BolaoCopa2026                 REM Parar
```

## 📊 Arquitetura

```
Bolao-Copa-2026/
├── 🐍 app.py                      ← Aplicação Flask (950 linhas)
├── 📋 models.py                   ← Banco de dados (8 tabelas)
├── 🏆 scoring.py                  ← Lógica de pontuação
├── ⚙️ windows_service.py          ← Wrapper do serviço
├── 🚀 service_runner.py           ← Waitress WSGI server
├── 📦 runtime_config.py           ← Configurações
├── ⚙️ service_config.json         ← Config persistente
├── 📋 requirements.txt            ← Dependências
│
├── 🎯 INSTALAR_COMPLETO.ps1       ← Script PowerShell (NOVO)
├── 🎯 INSTALAR_COMPLETO.bat       ← Script Batch (NOVO)
├── 📖 GUIA_INSTALACAO.md          ← Guia detalhado (NOVO)
├── 🚀 INICIO_RAPIDO.md            ← Quick start (NOVO)
├── ⚙️ CONFIG_INSTALACAO.json      ← Config template (NOVO)
│
├── 📁 templates/                  ← HTML (12+ arquivos)
├── 📁 static/                     ← CSS, JS, imagens
├── 📁 instance/                   ← Banco de dados (criado)
└── README.md                      ← Documentação original
```

## 🔧 Customização (Avançado)

Se precisar mudar porta ou hostname:

1. Edite `service_config.json`:
   ```json
   {
     "bind_host": "0.0.0.0",
     "port": 5055,
     "public_host": "NAEST202502"
   }
   ```

2. Execute o script novamente

## 🐛 Solução de Problemas

### "Script não pode ser carregado"
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
```

### "Access Denied"
- Execute como administrador (clique direito)
- Verifique se tem permissão no disco

### "Python não encontrado"
- Instale Python de https://www.python.org
- Marque "Add Python to PATH" durante instalação

### Porta 5055 em uso
- Edite `service_config.json`
- Mude para porta diferente (ex: 5056)
- Execute script novamente

## 📞 Próximos passos

1. **Copie** a pasta `Bolao-Copa-2026` para a máquina de destino
2. **Execute** `INSTALAR_COMPLETO.ps1` ou `.bat`
3. **Aguarde** 2-3 minutos
4. **Abra** a URL no navegador
5. **Registre-se** como primeiro usuário

## 📌 Versão

- **Script Version**: 1.0
- **Data**: Abril 2026
- **Status**: Pronto para produção

## 📄 Estrutura de deploy

```
OneDrive/NAEST/Documentos/Bolao-Copa-2026/  ← SharePoint sincronizado
├── INSTALAR_COMPLETO.ps1                    ← Usuários usam isto
├── INSTALAR_COMPLETO.bat
├── Todos os arquivos da aplicação
└── ...
```

## ✨ Benefícios do novo sistema

✅ **Instalação em um clique** - Sem linhas de comando  
✅ **Auto-elevação de privilégios** - Sem "Execute como admin"  
✅ **Idempotente** - Seguro rodar múltiplas vezes  
✅ **Tratamento de erros** - Feedback claro ao usuário  
✅ **Fácil remoção** - Comando simples para desinstalar  
✅ **Duas opções** - PowerShell ou Batch  
✅ **Documentação completa** - Guias e exemplos  
✅ **Pronto para rede** - SharePoint sincronizado

---

**Próximo uso**: Simplesmente execute um dos scripts de instalação! 🚀
