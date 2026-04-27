#!/usr/bin/env python3
"""Script para adicionar configurações de sessão persistente ao app.py"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Adicionar config de sessão logo após SQLALCHEMY_TRACK_MODIFICATIONS
old_config = 'app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False\n\ndb.init_app(app)'
new_config = '''app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 30  # 30 dias

db.init_app(app)'''

if old_config in content:
    content = content.replace(old_config, new_config)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Config de sessão atualizada em app.py')
else:
    print('⚠ Config já existe ou padrão diferente')
