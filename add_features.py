#!/usr/bin/env python3
"""
Script para adicionar:
1. Filtro automático de fase na rota /palpites
2. Rota de simulação para admin em /admin/simulacao
"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Encontrar a função palpites() e adicionar lógica de fase automática
# Procura por "# GET — listar jogos com palpites de todos do grupo"

novo_codigo_antes_filtro = '''
    # GET — listar jogos com palpites de todos do grupo
    filtro = request.args.get("filtro", "todos")
    fase_filtro = request.args.get("fase", "")'''

novo_codigo_depois = '''
    # GET — listar jogos com palpites de todos do grupo
    # Detectar fase automática se não foi especificada
    if not fase_filtro:
        # Encontrar fase com jogos dentro do prazo
        fases_disponiveis = db.session.query(Jogo.fase).distinct().order_by(Jogo.fase).all()
        for (f,) in fases_disponiveis:
            jogos_fase = Jogo.query.filter_by(fase=f).all()
            jogos_abertos = [j for j in jogos_fase if prazo_aberto(j)]
            if jogos_abertos:
                fase_filtro = f  # Usa primeira fase com jogos abertos
                break
        else:
            # Se nenhuma fase tem jogo aberto, use a última
            if fases_disponiveis:
                fase_filtro = fases_disponiveis[-1][0]
    
    filtro = request.args.get("filtro", "todos")
    fase_filtro_param = request.args.get("fase", "")
    if not fase_filtro_param and fase_filtro:
        # Fase foi detectada automaticamente
        pass'''

if novo_codigo_antes_filtro in content:
    content = content.replace(novo_codigo_antes_filtro, novo_codigo_depois)
    print('✓ Lógica de fase automática adicionada')
else:
    print('⚠ Função palpites() não encontrada no padrão esperado')

# 2. Adicionar rota de simulação para admin (antes de if __name__ == "__main__")
nova_rota_simulacao = '''

# ---------------------------------------------------------------------------
# SIMULAÇÃO (admin)
# ---------------------------------------------------------------------------
@app.route("/admin/simulacao", methods=["GET", "POST"])
@admin_required
def simulacao():
    """Permite admin simular data futura para testar funcionalidades"""
    data_simulada = request.args.get("data_simulada", "")
    
    if request.method == "POST":
        data_str = request.form.get("data_simulada", "").strip()
        try:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
            # Redireciona para GET com data_simulada como query param
            return redirect(url_for("simulacao", data_simulada=data_str))
        except ValueError:
            flash("Formato de data inválido. Use YYYY-MM-DD.", "danger")
    
    # Carregar dados com data simulada
    info_simulacao = {
        "data_simulada": data_simulada,
        "data_real": date.today().isoformat(),
    }
    
    if data_simulada:
        try:
            data_obj = datetime.strptime(data_simulada, "%Y-%m-%d").date()
            info_simulacao["jogos_neste_dia"] = (
                Jogo.query
                .filter_by(data_jogo=data_obj)
                .order_by(Jogo.hora_et)
                .all()
            )
            
            # Jogos já realizados até essa data
            info_simulacao["jogos_realizados"] = (
                Jogo.query
                .filter(Jogo.data_jogo < data_obj)
                .count()
            )
            
            # Próximo jogo após essa data
            info_simulacao["proximo_jogo"] = (
                Jogo.query
                .filter(Jogo.data_jogo >= data_obj)
                .order_by(Jogo.data_jogo, Jogo.hora_et)
                .first()
            )
        except ValueError:
            pass
    
    return render_template("admin/simulacao.html", info=info_simulacao)
'''

# Encontra o ponto de inserção (antes de if __name__)
ponto_insercao = '''

if __name__ == "__main__":'''
if ponto_insercao in content:
    content = content.replace(ponto_insercao, nova_rota_simulacao + ponto_insercao)
    print('✓ Rota de simulação adicionada')
else:
    print('⚠ Ponto de inserção não encontrado')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n✓ Atualizações concluídas!')
