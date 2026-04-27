# ✅ Checklist de Funcionalidades

## Sistema de Autenticação

- [ ] Página de login acessível em `/login`
- [ ] Página de cadastro acessível em `/registro`
- [ ] Cadastro cria usuário com hash de senha
- [ ] Login valida credenciais
- [ ] Logout limpa sessão
- [ ] Sessão persiste entre reloads
- [ ] Redirecionamento automático para login se não autenticado

## Sistema de Grupos

- [ ] Admin consegue criar novo grupo
- [ ] Admin consegue editar grupo
- [ ] Admin consegue excluir grupo vazio
- [ ] Novo usuário consegue se asociar a um grupo
- [ ] Usuário muda de grupo (se permitido)
- [ ] Usuários do grupo veem palpites uns dos outros
- [ ] Usuários de grupos diferentes NOT veem palpites

## Palpites

- [ ] Usuário consegue ver próximos jogos
- [ ] Usuário consegue enviar palpite para jogo aberto
- [ ] Usuário consegue alterar palpite antes do prazo
- [ ] Usuário NÃO consegue alterar após prazo (campo bloqueado)
- [ ] Palpite de mata-mata exige classificado se empate
- [ ] Histórico de alterações é registrado
- [ ] Data/hora de envio e última alteração são gravadas
- [ ] Usuário vê palpites de outros do grupo (visualização)
- [ ] Usuário SÓ edita seu próprio palpite

## Resultados

- [ ] Admin consegue lançar resultado para jogo
- [ ] Admin consegue editar resultado
- [ ] Após resultado, pontuação é calculada automaticamente
- [ ] Resultado de mata-mata exige classificado
- [ ] Histórico de quem lançou é registrado

## Pontuação

- [ ] Placar exato = 10 pts
- [ ] Vencedor + saldo = 7 pts
- [ ] Apenas vencedor = 5 pts
- [ ] Empate (placar diferente) = 5 pts
- [ ] Um gol correto = 2 pts
- [ ] Erro total = 0 pts
- [ ] Classificado correto em mata-mata = +3 pts
- [ ] Pontos NÃO se somam (exlusivos)
- [ ] Bônus classificado É cumulativo

## Rankings

- [ ] Ranking geral lista todos usuários
- [ ] Ranking geral ordena por: pts → exatos → vencedores → saldos → classif → palpites → apelido
- [ ] Ranking por fase filtra por fase escolhida
- [ ] Cards destacam: líder, mais exatos, melhor aproveitamento
- [ ] Aproveitamento % é calculado corretamente

## Dados

- [ ] 107 jogos pré-carregados na primeira execução
- [ ] Horários convertidos ET → Brasília
- [ ] Prazo = 23h59 BRT dia anterior
- [ ] Todas as 12 fases incluídas (grupos A-L + mata-mata)
- [ ] Banco de dados persiste entre reinicializações

## Interface

- [ ] Menu responde apenas se usuário logado
- [ ] Menu mostra nome/apelido do usuário logado
- [ ] Menu mostra grupo do usuário logado
- [ ] Botões Admin aparecem apenas para admin
- [ ] Cores de status: verde (aberto), azul (enviado), amarelo (sem), cinza (bloqueado)
- [ ] Design responsivo (mobile/desktop)

## Admin Features

- [ ] Admin consegue criar grupos
- [ ] Admin consegue lançar resultados
- [ ] Admin consegue recalcular pontuação
- [ ] Admin consegue ver botão de Admin no menu
- [ ] Admin consegue gerenciar usuários (se implementado)

## Segurança

- [ ] Senhas são hasheadas (não em texto plano)
- [ ] `check_password()` funciona após salvar
- [ ] Usuário inativo NÃO consegue fazer login
- [ ] Usuário inativo NÃO consegue enviar palpites
- [ ] Email é único
- [ ] Apelido é único
- [ ] CSRF protection (se aplicável)
- [ ] SQL injection prevention (SQLAlchemy ORM)

## Conversão de Horários

- [ ] ET (Eastern Time) original preservado
- [ ] BRT (Brasília) calculado corretamente
- [ ] Prazo usa BRT
- [ ] Display mostra BRT por padrão
- [ ] Todos os jogos têm ambos os horários

## Deploy em Rede

- [ ] Aplicação inicia sem erros
- [ ] Banco de dados criado automaticamente
- [ ] Jogos carregados na primeira execução
- [ ] Funciona com `--host 0.0.0.0` para acesso remoto
- [ ] README está correto
- [ ] SHAREPOINT_SETUP.md tem instruções claras
- [ ] Script `criar_admin.py` funciona

---

## Testes Manuais Sugeridos

### Teste 1: Fluxo Completo
1. Criar admin: `py criar_admin.py`
2. Login com admin
3. Criar grupo "Teste"
4. Logout
5. Cadastro novo usuário no grupo "Teste"
6. Fazer palpite
7. Admin lança resultado
8. Verificar pontuação

### Teste 2: Múltiplos Usuários
1. Cadastrar 3 usuários no mesmo grupo
2. Cada um faz palpites diferentes
3. Ver que todos veem palpites dos outros
4. Verificar que só conseguem editar o seu

### Teste 3: Prazo
1. Buscar um jogo com prazo próximo
2. Verificar que campo de edição está aberto
3. Fazer palpite
4. Esperar passar do prazo
5. Verificar que campo fica desabilitado

---

**Status**: ✅ Pronto para Produção  
**Versão**: 1.0  
**Data**: Abril 2026
