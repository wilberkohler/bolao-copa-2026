#!/usr/bin/env python3
"""Adicionar link de Simulação ao menu Admin"""

with open('templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Adicionar link de simulação no menu admin
old = '''              <li><a class="dropdown-item" href="{{ url_for('listar_grupos') }}"><i class="bi bi-collection"></i> Grupos</a></li>
            </ul>'''

new = '''              <li><a class="dropdown-item" href="{{ url_for('listar_grupos') }}"><i class="bi bi-collection"></i> Grupos</a></li>
              <li><hr class="dropdown-divider"></li>
              <li><a class="dropdown-item" href="{{ url_for('simulacao') }}"><i class="bi bi-clock-history"></i> Simulação</a></li>
            </ul>'''

if old in content:
    content = content.replace(old, new)
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Link de simulação adicionado ao menu admin')
else:
    print('⚠ Padrão não encontrado')
