# Bolão Copa 2026 — Sistema Compartilhado em Rede

## 📋 Visão Geral

Sistema web de palpites para a Copa do Mundo FIFA 2026 com autenticação, grupos de usuários e compartilhamento de palpites.

### Funcionalidades Principais

- ✅ **Autenticação**: Primeiro acesso com cadastro simples (nome, email, apelido, senha)
- ✅ **Grupos**: Usuários se associam a grupos existentes ou criam novos (apenas admin)
- ✅ **Compartilhamento**: Visualize palpites de todos do grupo, edite apenas o seu
- ✅ **104 Jogos**: Pré-carregados com datas, horários convertidos para Brasília (BRT)
- ✅ **Pontuação Automática**: 10/7/5/5/2 pts por acerto de placar/vencedor
- ✅ **Rankings**: Geral e por fase

---

## 🚀 Instalação e Execução

### Pré-requisitos

- Python 3.10+
- Windows/Mac/Linux

### 1. Baixar e Descompactar

1. Acesse a pasta compartilhada no SharePoint
2. Baixe toda a pasta `Bolao-Copa-2026`
3. Descompacte em um local permanente

```
C:\Users\SeuUsuario\Bolao-Copa-2026\
```

### 2. Instalar Dependências

Abra o PowerShell ou Prompt de Comando na pasta do projeto:

```powershell
cd C:\Users\SeuUsuario\Bolao-Copa-2026
py -m pip install -r requirements.txt
```

### 3. Iniciar o Servidor

```powershell
py app.py
```

Você verá:
```
 * Running on http://127.0.0.1:5000
```

### 4. Acessar a Aplicação

Abra o navegador:
```
http://127.0.0.1:5000
```

---

## 👤 Primeiro Acesso

### Criar Primeiro Usuário (Admin)

1. Clique em **Cadastro**
2. Preencha:
   - **Nome**: seu nome completo
   - **E-mail**: email único
   - **Apelido**: como quer ser chamado
   - **Senha**: escolha uma segura
   - **Grupo**: deixe em branco (será criado depois)

3. Clique em **Cadastrar**

### Configurar como Admin

Como primeiro usuário, você precisa se tornar admin manualmente (via banco de dados):

1. Parar o servidor (Ctrl+C)
2. No PowerShell, execute:

```powershell
py -c "from models import db; from app import app; app.app_context().push(); from models import User; u = User.query.filter_by(email='seu@email.com').first(); u.eh_admin = True; db.session.commit(); print('Admin criado!')"
```

3. Reiniciar: `py app.py`

---

## 🔑 Recursos por Perfil

### Usuário Normal

- ✅ Ver próximos jogos e palpites enviados
- ✅ Enviar e alterar palpites (até 23h59 BRT do dia anterior)
- ✅ Ver palpites de outros usuários do grupo
- ✅ Ver ranking geral e por fase

### Admin

- ✅ Tudo do usuário normal
- ✅ Criar e gerenciar grupos
- ✅ Lançar resultados reais
- ✅ Recalcular pontuação

---

## 📖 Fluxo de Uso

### 1️⃣ Criar Grupo (Admin)

1. Ir para **Admin** → **Grupos**
2. Clicar em **Novo Grupo**
3. Preencher:
   - **Nome**: ex. "Amigos da Empresa"
   - **Descrição**: opcional
4. Salvar

### 2️⃣ Novos Usuários se Cadastram

1. Clique em **Cadastro**
2. Escolha um **Grupo** existente
3. Pronto! Já pode fazer palpites

### 3️⃣ Fazer Palpites

1. Ir para **Palpites**
2. Escolher jogos (todos do grupo aparecem)
3. Preencher gols (para mata-mata, também preencher classificado se empate)
4. Clicar **Salvar Palpites**
5. Pode alterar quantas vezes quiser até o prazo

### 4️⃣ Lançar Resultados (Admin)

1. Ir para **Admin** → **Resultados**
2. Buscar jogo
3. Preencher gols reais e classificado
4. Clicar **Salvar Resultado**
5. Pontuação é calculada automaticamente

### 5️⃣ Ver Ranking

- **Ranking Geral**: vê todos os usuários
- **Ranking por Fase**: seleciona fase específica

---

## 📊 Sistema de Pontuação

Por partida:

| Situação | Pontos |
|----------|--------|
| Placar exato | 10 |
| Vencedor + saldo correto | 7 |
| Apenas vencedor | 5 |
| Empate (mas placar diferente) | 5 |
| Um gol correto | 2 |
| Errou tudo | 0 |
| **+** Classificado correto (mata-mata) | +3 |

**Exemplo**: Brasil 2×1 Marrocos
- Palpite: Brasil 2×1 Marrocos = **10 pts**
- Palpite: Brasil 2×0 Marrocos = **7 pts** (vencedor + saldo)
- Palpite: Brasil 1×0 Marrocos = **5 pts** (só vencedor)

---

## 🔒 Segurança e Permissões

- ✅ Cada usuário só edita seu próprio palpite
- ✅ Palpites bloqueados automaticamente após prazo
- ✅ Senhas com hash (bcrypt)
- ✅ Grupos isolam palpites por equipe
- ✅ Admin controla tudo

---

## ⏰ Prazos

- **Prazo para palpite**: 23h59 (horário de Brasília) do dia anterior ao jogo
- **Exemplo**: Jogo em 12/06 às 17:00 ET → Prazo em 11/06 às 23h59 BRT

---

## 🌐 Usar em Rede (Acesso Compartilhado)

### Opção 1: Usando a Pasta Compartilhada

1. Salvar em: `C:\...\SharePoint\NAEST\` (ou similar)
2. Todos executam: `py app.py` localmente
3. Cada um acessa: `http://127.0.0.1:5000`

⚠️ **Limitação**: Cada pessoa tem seu próprio servidor local. Se quiser compartilhado de verdade, veja opção 2.

### Opção 2: Servidor Centralizado (Recomendado)

1. Designar 1 máquina como "servidor"
2. Nessa máquina, executar: `py app.py --host 0.0.0.0`
3. Outros acessam via IP da máquina: `http://192.168.1.100:5000`

---

## 📁 Estrutura do Projeto

```
Bolao-Copa-2026/
├── app.py                              # Aplicação Flask
├── models.py                           # Modelos SQL (User, Grupo, Jogo, Palpite, etc)
├── scoring.py                          # Lógica de pontuação e ranking
├── seed_jogos_copa_2026.py            # 104 jogos pré-carregados
├── requirements.txt                    # Dependências
├── instance/
│   └── bolao.db                       # Banco de dados SQLite (criado automaticamente)
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── auth/
│   │   ├── login.html
│   │   └── registro.html
│   ├── palpites/
│   │   └── index.html
│   ├── ranking/
│   │   ├── geral.html
│   │   └── fase.html
│   ├── resultados/
│   │   ├── lista.html
│   │   └── form.html
│   └── admin/
│       ├── grupos_lista.html
│       └── grupos_form.html
├── static/
│   └── css/
│       └── style.css
└── README.md                          # Este arquivo
```

---

## 🆘 Troubleshooting

### Erro: "Port 5000 already in use"

Outro processo está usando a porta 5000. Opções:

```powershell
# Matar processo na porta 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Ou usar outra porta
py app.py --port 5001
```

### Erro: "Database is locked"

Feche todas as abas do navegador e tente novamente.

### Senha esquecida

Resetar via banco de dados:

```powershell
py -c "from models import db, User; from app import app; app.app_context().push(); u = User.query.filter_by(email='seu@email.com').first(); u.set_password('nova_senha'); db.session.commit(); print('Senha resetada!')"
```

---

## 📞 Contato

Para dúvidas sobre configuração, contact admnistrador do grupo.

---

## 📱 Aplicativo iOS

Este projeto pode virar app iOS sem reescrever o backend, usando wrapper com Capacitor.

- Guia completo: `IOS_APP_SETUP.md`
- Estrutura pronta: `mobile/ios-wrapper/`

Resumo rápido:

1. Publique o sistema Flask em uma URL HTTPS.
2. Edite `mobile/ios-wrapper/capacitor.config.json` com sua URL.
3. No Mac com Xcode:

```bash
cd mobile/ios-wrapper
npm install
npm run cap:add:ios
npm run cap:sync
npm run cap:open:ios
```

---

**Versão**: 1.0  
**Data**: Abril 2026  
**Copa do Mundo**: 11 de junho a 19 de julho de 2026
