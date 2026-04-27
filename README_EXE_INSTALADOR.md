# 📦 BOLÃO COPA 2026 - Instalador EXE Único

## 🎯 O que é

Um único arquivo **`BolaoInstalador.exe`** que contém **tudo** necessário para instalar a aplicação Bolão Copa 2026 como serviço Windows.

## ✨ Principais Vantagens

✅ **Nenhuma dependência** - Não precisa de Python instalado  
✅ **Um arquivo só** - Simples de distribuir e usar  
✅ **Clique duplo** - Qualquer pessoa consegue instalar  
✅ **Automático** - Faz tudo: dependências, serviço, firewall  
✅ **Profissional** - Interface clara e informativa  

## 📥 Como usar

### 1. Fazer Download
- Baixe a pasta `dist` do SharePoint ou do link fornecido
- Ou extraia o arquivo ZIP `BolaoInstalador.zip`

### 2. Instalar (Qualquer pessoa consegue!)

**No Windows 10/11:**

```
1. Localize o arquivo BolaoInstalador.exe
2. Clique duplo nele
3. Clique "Sim" quando perguntado sobre privilégios
4. Aguarde 2-3 minutos
5. O navegador abre automaticamente
6. Pronto! Aplicação está rodando
```

**No Windows 7/8:**

```
1. Clique direito em BolaoInstalador.exe
2. Selecione "Executar como administrador"
3. Clique "Sim"
4. Aguarde 2-3 minutos
5. Aplicação está pronta
```

### 3. Acessar

Após instalação, acesse em:

```
http://localhost:5055           (Localmente)
http://NAEST202502:5055         (Pela rede)
```

## 📋 Pré-requisitos

✅ Windows 7 ou superior  
✅ Acesso de Administrador  
✅ Conexão com internet (só na primeira instalação)  
❌ NÃO precisa de Python!

## 🔧 O que o instalador faz automaticamente

1. ✅ Verifica sistema
2. ✅ Instala todas as dependências Python
3. ✅ Copia arquivos da aplicação
4. ✅ Registra como Serviço Windows (BolaoCopa2026)
5. ✅ Abre porta 5055 no Firewall
6. ✅ Configura auto-restart em caso de falha
7. ✅ Inicia o serviço
8. ✅ Abre navegador na aplicação

## 📊 Estrutura do Download

```
dist/
├── BolaoInstalador.exe          ← Execute este arquivo
├── app.py, models.py, scoring.py
├── templates/                    ← Páginas HTML
├── static/                       ← CSS e imagens
├── requirements.txt
└── ... (outros arquivos)
```

## ⚙️ Configuração Avançada

Se precisar customizar porta ou hostname, edite **antes** de instalar:

```json
{
  "bind_host": "0.0.0.0",
  "port": 5055,
  "public_host": "NAEST202502"
}
```

Arquivo: `service_config.json`

## ❌ Remover

Abra PowerShell como admin e execute:

```powershell
Get-Service BolaoCopa2026 | Stop-Service
sc.exe delete BolaoCopa2026
netsh advfirewall firewall delete rule name="Bolao Copa 2026"
```

Ou use os scripts `.bat` / `.ps1` anteriores com o parâmetro `remove`.

## 🐛 Solução de Problemas

### "Este arquivo não é um tipo de arquivo Windows"
- O Windows pode bloquear .exe baixado da internet
- Solução: Clique direito → Propriedades → Desbloquear

### "Acesso Negado" na instalação
- Clique direito → "Executar como administrador"
- Confirme na caixa de diálogo

### Aplicação não abre no navegador
- Abra manualmente: `http://localhost:5055`
- Aguarde 10 segundos para o serviço iniciar

### Porta 5055 em uso
- Edite `service_config.json` antes de instalar
- Mude para porta diferente (ex: 5056)

## 📞 Próximas Ações

1. **Copie** a pasta `dist` para seu SharePoint
2. **Compartilhe** o link com os usuários
3. **Usuários** fazem download e duplo-clique em `BolaoInstalador.exe`
4. **Pronto!** Tudo funciona automaticamente

## 📌 Versão

- **Tipo**: Instalador EXE Portável
- **Versão**: 1.0
- **Data**: Abril 2026
- **Compilado com**: PyInstaller + Python 3.11+

## ✅ Benefícios para Usuários Finais

| Antes | Depois |
|-------|--------|
| "Precisa instalar Python?" | "Clica no .exe e pronto!" |
| Múltiplos scripts .bat/.ps1 | Um único arquivo |
| Erros de dependências | Tudo automático |
| Requer conhecimento técnico | Para qualquer um |

---

**Simplificar é o segredo! 🚀**
