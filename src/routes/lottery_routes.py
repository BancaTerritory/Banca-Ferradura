from flask import render_template, redirect, url_for, request, flash, session, jsonify
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
lottery_bp = Blueprint('lottery', __name__)

# Lista de modalidades do jogo do bicho
MODALIDADES = {
    'GRUPO': {
        'descricao': 'Apostar em um grupo de animais',
        'variantes': ['GRUPO SIMPLES', 'GRUPO COMBINADO', 'GRUPO FIXO']
    },
    'DEZENA': {
        'descricao': 'Apostar em uma dezena específica',
        'variantes': ['DEZENA SIMPLES', 'DEZENA COMBINADA', 'DEZENA FIXA']
    },
    'CENTENA': {
        'descricao': 'Apostar em uma centena específica',
        'variantes': ['CENTENA SIMPLES', 'CENTENA COMBINADA', 'CENTENA FIXA']
    },
    'MILHAR': {
        'descricao': 'Apostar em uma milhar específica',
        'variantes': ['MILHAR SIMPLES', 'MILHAR COMBINADA', 'MILHAR FIXA']
    }
}

# Mapeamento de grupos de animais
GRUPOS_ANIMAIS = {
    1: 'AVESTRUZ', 2: 'ÁGUIA', 3: 'BURRO', 4: 'BORBOLETA',
    5: 'CACHORRO', 6: 'CABRA', 7: 'CARNEIRO', 8: 'CAMELO',
    9: 'COBRA', 10: 'COELHO', 11: 'CAVALO', 12: 'ELEFANTE',
    13: 'GALO', 14: 'GATO', 15: 'JACARÉ', 16: 'LEÃO',
    17: 'MACACO', 18: 'PORCO', 19: 'PAVÃO', 20: 'PERU',
    21: 'TOURO', 22: 'TIGRE', 23: 'URSO', 24: 'VEADO',
    25: 'VACA'
}

# Colocações disponíveis
COLOCACOES = ['1º PRÊMIO', '2º PRÊMIO', '3º PRÊMIO', '4º PRÊMIO', '5º PRÊMIO']

# Importamos o blueprint diretamente do main.py
# from src.main import lottery_bp


# Rota principal da loteria
@lottery_bp.route('/')
def index():
    return render_template('lottery/index.html')

# Rota para seleção de modalidade
@lottery_bp.route('/modalidade')
def modalidade():
    # Limpa dados de apostas anteriores
    if 'aposta' in session:
        session.pop('aposta')
    
    # Inicializa a sessão de aposta
    session['aposta'] = {
        'modalidade': None,
        'colocacao': None,
        'numeros': None,
        'valor': None
    }
    
    # Prepara todas as modalidades para exibição
    todas_modalidades = []
    for tipo, info in MODALIDADES.items():
        for variante in info['variantes']:
            todas_modalidades.append({
                'tipo': tipo,
                'nome': variante,
                'descricao': info['descricao']
            })
    
    return render_template('lottery/modalidades.html', modalidades=todas_modalidades)

# Rota para seleção de colocação
@lottery_bp.route('/colocacao/<modalidade>')
def colocacao(modalidade):
    # Salva a modalidade selecionada
    if 'aposta' not in session:
        session['aposta'] = {}
    
    session['aposta']['modalidade'] = modalidade
    session.modified = True
    
    return render_template('lottery/colocacao.html', colocacoes=COLOCACOES)

# Rota para inserção de números
@lottery_bp.route('/numeros/<colocacao>')
def numeros(colocacao):
    # Salva a colocação selecionada
    if 'aposta' not in session:
        return redirect(url_for('lottery.modalidade'))
    
    session['aposta']['colocacao'] = colocacao
    session.modified = True
    
    modalidade = session['aposta']['modalidade']
    tipo_modalidade = next((tipo for tipo, info in MODALIDADES.items() 
                          if modalidade in info['variantes']), None)
    
    # Determina o tipo de entrada baseado na modalidade
    if 'GRUPO' in modalidade:
        return render_template('lottery/numeros_grupo.html', grupos=GRUPOS_ANIMAIS)
    elif 'DEZENA' in modalidade:
        return render_template('lottery/numeros_dezena.html')
    elif 'CENTENA' in modalidade:
        return render_template('lottery/numeros_centena.html')
    elif 'MILHAR' in modalidade:
        return render_template('lottery/numeros_milhar.html')
    else:
        return redirect(url_for('lottery.modalidade'))

# Rota para processar os números inseridos
@lottery_bp.route('/processar_numeros', methods=['POST'])
def processar_numeros():
    if 'aposta' not in session:
        return redirect(url_for('lottery.modalidade'))
    
    numeros = request.form.get('numeros')
    session['aposta']['numeros'] = numeros
    session.modified = True
    
    return redirect(url_for('lottery.valor'))

# Rota para definição de valor
@lottery_bp.route('/valor')
def valor():
    if 'aposta' not in session or not session['aposta'].get('numeros'):
        return redirect(url_for('lottery.modalidade'))
    
    return render_template('lottery/valor.html')

# Rota para processar o valor inserido
@lottery_bp.route('/processar_valor', methods=['POST'])
def processar_valor():
    if 'aposta' not in session:
        return redirect(url_for('lottery.modalidade'))
    
    valor = request.form.get('valor')
    try:
        valor_float = float(valor.replace('R$', '').replace(',', '.').strip())
        session['aposta']['valor'] = valor_float
        session.modified = True
        return redirect(url_for('lottery.confirmar'))
    except ValueError:
        flash('Valor inválido. Por favor, insira um valor numérico.')
        return redirect(url_for('lottery.valor'))

# Rota para confirmação de aposta
@lottery_bp.route('/confirmar')
def confirmar():
    if 'aposta' not in session or not all(session['aposta'].get(k) for k in ['modalidade', 'colocacao', 'numeros', 'valor']):
        return redirect(url_for('lottery.modalidade'))
    
    return render_template('lottery/confirmar.html', aposta=session['aposta'])

# Rota para finalizar a aposta
@lottery_bp.route('/finalizar', methods=['POST'])
def finalizar():
    if 'aposta' not in session:
        return redirect(url_for('lottery.modalidade'))
    
    # Aqui seria implementada a lógica para salvar a aposta no banco de dados
    # e descontar o valor do saldo do usuário
    
    # Simulação de desconto do saldo
    valor_aposta = session['aposta']['valor']
    
    # Limpa os dados da aposta da sessão
    aposta_realizada = session.pop('aposta', None)
    
    flash(f'Aposta realizada com sucesso! Valor: R$ {valor_aposta:.2f}')
    return redirect(url_for('lottery.historico'))

# Rota para histórico de apostas
@lottery_bp.route('/historico')
def historico():
    # Aqui seria implementada a lógica para buscar o histórico de apostas do usuário
    # Por enquanto, retornamos uma página vazia
    return render_template('lottery/historico.html', apostas=[])

# Rota para buscar modalidades (API)
@lottery_bp.route('/api/modalidades')
def api_modalidades():
    return jsonify(MODALIDADES)

# Rota para buscar grupos de animais (API)
@lottery_bp.route('/api/grupos')
def api_grupos():
    return jsonify(GRUPOS_ANIMAIS)
