# 📋 Instruções: Salvar Aplicação no SharePoint

## 1. Preparar a Pasta

1. Abra `C:\Users\Wilber Kohler\Documents\Python\Bolao` no Windows Explorer
2. Selecione **todos os arquivos e pastas** (exceto `instance` se for deixar banco de dados local)
3. Copie (Ctrl+C)

## 2. Sincronizar com SharePoint (Recomendado - Automático)

### Se você já tem SharePoint sincronizado como pasta local:

1. Abra File Explorer
2. Navegue até: `C:\Users\Wilber Kohler\OneDrive\SharePoint\...` (ou equivalente)
3. Crie pasta `Bolao-Copa-2026`
4. Cole os arquivos (Ctrl+V)

✅ **Vantagem**: Sincronização automática entre máquinas

### Se não tem sincronizado ainda:

1. Abra: https://naestconsultoria.sharepoint.com
2. Navegue até a pasta compartilhada
3. Clique em **"Sincronizar"** no canto superior
4. Escolha local no computador
5. Siga as instruções

## 3. Acesso Compartilhado (Todos pelo mesmo servidor)

### Opção A: Cada pessoa executa localmente

**Pré-requisito**: Python 3.10+ instalado em cada máquina

```powershell
# Na máquina de cada pessoa
cd C:\Users\Usuario\OneDrive\SharePoint\Bolao-Copa-2026
py app.py
```

Acessar: `http://127.0.0.1:5000` (localhost)

⚠️ Cada pessoa tem seu próprio servidor local.

### Opção B: Servidor centralizado (Recomendado)

**Pré-requisito**: 1 máquina rodando 24/7 (ou durante horários de uso)

**Na máquina servidor**:

```powershell
cd C:\Users\Usuario\OneDrive\SharePoint\Bolao-Copa-2026

# Descobrir IP local da máquina
ipconfig

# Procurar por "IPv4 Address: 192.168.x.x"

# Executar servidor (exponha para rede)
py app.py --host 0.0.0.0 --port 5000
```

**Nos computadores dos usuários**:

1. Abra navegador
2. Digite: `http://192.168.1.100:5000` (substitua IP)
3. Pronto! Todos veem os mesmos dados

✅ **Vantagem**: Dados centralizados e atualizados em tempo real

## 4. Configuração Inicial (Após Copiar)

```powershell
# 1. Instalar dependências
cd C:\Users\Wilber Kohler\OneDrive\SharePoint\Bolao-Copa-2026
py -m pip install -r requirements.txt

# 2. Criar primeiro admin
py criar_admin.py

# 3. Iniciar servidor
py app.py
```

## 5. Compartilhar Link da Aplicação

Se usando Opção B (servidor centralizado):

**Envie aos usuários via e-mail ou chat**:

```
Acesse o Bolão em: http://192.168.1.100:5000

Login inicial:
- E-mail: (que você criou no criar_admin.py)
- Senha: (que você criou no criar_admin.py)
```

## 6. Backup do Banco de Dados

O arquivo `instance/bolao.db` contém todos os dados (palpites, resultados, usuários).

**Para backup**:

```powershell
# Copiar arquivo do banco
Copy-Item "instance\bolao.db" "C:\Backup\bolao_$(Get-Date -f 'yyyy-MM-dd').db"
```

**Restaurar**:

```powershell
# Parar servidor (Ctrl+C)
# Copiar arquivo de backup para instance/bolao.db
# Reiniciar servidor
```

## 7. Resolver Problemas de Acesso em Rede

### Firewall bloqueando

```powershell
# Abrir porta 5000 no Windows Firewall (como admin)
netsh advfirewall firewall add rule name="Flask 5000" dir=in action=allow protocol=tcp localport=5000
```

### Outros computadores não conseguem conectar

1. Verificar se servidor está em `http://0.0.0.0:5000` (não localhost)
2. Verificar IP local: `ipconfig` (procurar IPv4 address)
3. Testar na mesma máquina primeiro: `http://127.0.0.1:5000`
4. Testar de outra máquina: `http://192.168.x.x:5000`

## 8. Deploy em Produção (Futuro)

Para acesso remoto (VPN, nuvem, etc):

1. Usar **Gunicorn** em vez de Flask dev server
2. Usar **Nginx** como proxy reverso
3. Usar **SSL/HTTPS**
4. Rodar em **servidor dedicado** (AWS, Azure, etc)

---

**Pronto!** 🎉 A aplicação está compartilhada e pronta para uso.
