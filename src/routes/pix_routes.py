from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
import random
import string
import time
from datetime import datetime, timedelta

pix_blueprint = Blueprint('pix', __name__)

# Simulação de transações PIX (em produção seria banco de dados)
transacoes_pix = {}

@pix_blueprint.route('/recarga')
def recarga_page():
    """Página de recarga PIX"""
    if not session.get("user_phone"):
        flash("Você precisa estar logado para acessar esta página.", "error")
        return redirect(url_for("auth.login_page"))
    
    return render_template('recarga_pix.html')

@pix_blueprint.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    """Gerar código PIX para pagamento"""
    if not session.get("user_phone"):
        return jsonify({"error": "Usuário não logado"}), 401
    
    try:
        data = request.get_json()
        valor = float(data.get('valor', 0))
        
        if valor < 10:
            return jsonify({"error": "Valor mínimo é R$ 10,00"}), 400
        
        if valor > 5000:
            return jsonify({"error": "Valor máximo é R$ 5.000,00"}), 400
        
        # Gerar ID único para a transação
        transaction_id = gerar_id_transacao()
        
        # Calcular bônus
        bonus_percent = calcular_bonus(valor)
        valor_bonus = valor * (bonus_percent / 100)
        valor_total = valor + valor_bonus
        
        # Gerar código PIX (simulado - em produção seria API do PodBank)
        codigo_pix = gerar_codigo_pix_real(valor, transaction_id)
        
        # Salvar transação
        transacoes_pix[transaction_id] = {
            'user_phone': session.get("user_phone"),
            'valor_original': valor,
            'bonus_percent': bonus_percent,
            'valor_bonus': valor_bonus,
            'valor_total': valor_total,
            'codigo_pix': codigo_pix,
            'status': 'pendente',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=15)
        }
        
        return jsonify({
            "success": True,
            "transaction_id": transaction_id,
            "codigo_pix": codigo_pix,
            "valor_original": valor,
            "bonus_percent": bonus_percent,
            "valor_bonus": valor_bonus,
            "valor_total": valor_total,
            "expires_in": 900  # 15 minutos em segundos
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pix_blueprint.route('/verificar-pagamento', methods=['POST'])
def verificar_pagamento():
    """Verificar se o pagamento PIX foi processado"""
    if not session.get("user_phone"):
        return jsonify({"error": "Usuário não logado"}), 401
    
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        
        if not transaction_id or transaction_id not in transacoes_pix:
            return jsonify({"error": "Transação não encontrada"}), 404
        
        transacao = transacoes_pix[transaction_id]
        
        # Verificar se a transação pertence ao usuário
        if transacao['user_phone'] != session.get("user_phone"):
            return jsonify({"error": "Transação não autorizada"}), 403
        
        # Verificar se não expirou
        if datetime.now() > transacao['expires_at']:
            transacao['status'] = 'expirado'
            return jsonify({
                "success": False,
                "status": "expirado",
                "message": "PIX expirado. Gere um novo código."
            })
        
        # Simular verificação de pagamento (em produção seria webhook do PodBank)
        # Para demonstração, vamos simular 30% de chance de estar pago
        if transacao['status'] == 'pendente':
            # Simular delay de processamento
            if random.random() > 0.7:  # 30% chance
                transacao['status'] = 'pago'
                transacao['paid_at'] = datetime.now()
                
                # Adicionar créditos ao usuário
                creditos_atuais = session.get("user_credits", 0.0)
                novos_creditos = creditos_atuais + transacao['valor_total']
                session["user_credits"] = novos_creditos
                
                return jsonify({
                    "success": True,
                    "status": "pago",
                    "message": f"Pagamento confirmado! R$ {transacao['valor_total']:.2f} adicionados ao seu saldo.",
                    "valor_creditado": transacao['valor_total'],
                    "novo_saldo": novos_creditos
                })
        
        return jsonify({
            "success": False,
            "status": transacao['status'],
            "message": "Pagamento ainda não identificado. Aguarde alguns instantes e tente novamente."
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pix_blueprint.route('/historico-pix')
def historico_pix():
    """Histórico de transações PIX do usuário"""
    if not session.get("user_phone"):
        return jsonify({"error": "Usuário não logado"}), 401
    
    user_phone = session.get("user_phone")
    historico = []
    
    for tid, transacao in transacoes_pix.items():
        if transacao['user_phone'] == user_phone:
            historico.append({
                'id': tid,
                'valor_original': transacao['valor_original'],
                'valor_total': transacao['valor_total'],
                'bonus_percent': transacao['bonus_percent'],
                'status': transacao['status'],
                'created_at': transacao['created_at'].strftime('%d/%m/%Y %H:%M'),
                'paid_at': transacao.get('paid_at', '').strftime('%d/%m/%Y %H:%M') if transacao.get('paid_at') else ''
            })
    
    # Ordenar por data (mais recente primeiro)
    historico.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({"historico": historico})

def gerar_id_transacao():
    """Gerar ID único para transação"""
    timestamp = str(int(time.time()))
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PIX{timestamp}{random_chars}"

def calcular_bonus(valor):
    """Calcular percentual de bônus baseado no valor"""
    if valor >= 500:
        return 20  # 20% para valores acima de R$ 500
    elif valor >= 200:
        return 15  # 15% para valores acima de R$ 200
    elif valor >= 100:
        return 10  # 10% para valores acima de R$ 100
    elif valor >= 50:
        return 5   # 5% para valores acima de R$ 50
    else:
        return 0   # Sem bônus para valores menores

def gerar_codigo_pix_real(valor, transaction_id):
    """Gerar código PIX real (simulado - em produção seria API do PodBank)"""
    
    # Estrutura básica do PIX
    payload = "00020126"  # Payload Format Indicator
    
    # Merchant Account Information
    merchant_info = "0014BR.GOV.BCB.PIX"
    
    # Chave PIX (simulada - seria sua chave real)
    chave_pix = "bancaferradura@podbank.com.br"
    merchant_info += f"01{len(chave_pix):02d}{chave_pix}"
    
    # Adicionar informações da transação
    merchant_info += f"02{len(transaction_id):02d}{transaction_id}"
    
    payload += f"26{len(merchant_info):02d}{merchant_info}"
    
    # Merchant Category Code
    payload += "52040000"
    
    # Transaction Currency (BRL)
    payload += "5303986"
    
    # Transaction Amount
    valor_str = f"{valor:.2f}"
    payload += f"54{len(valor_str):02d}{valor_str}"
    
    # Country Code
    payload += "5802BR"
    
    # Merchant Name
    merchant_name = "BANCA FERRADURA"
    payload += f"59{len(merchant_name):02d}{merchant_name}"
    
    # Merchant City
    merchant_city = "SAO PAULO"
    payload += f"60{len(merchant_city):02d}{merchant_city}"
    
    # Additional Data Field
    additional_data = f"05{len(transaction_id):02d}{transaction_id}"
    payload += f"62{len(additional_data):02d}{additional_data}"
    
    # CRC16 (simulado - em produção seria calculado corretamente)
    payload += "6304"
    crc = f"{random.randint(1000, 9999)}"
    payload += crc
    
    return payload

# Webhook para receber notificações do PodBank (em produção)
@pix_blueprint.route('/webhook/podbank', methods=['POST'])
def webhook_podbank():
    """Webhook para receber notificações de pagamento do PodBank"""
    try:
        data = request.get_json()
        
        # Verificar assinatura do webhook (em produção)
        # if not verificar_assinatura_webhook(data):
        #     return jsonify({"error": "Assinatura inválida"}), 401
        
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        
        if transaction_id in transacoes_pix:
            transacao = transacoes_pix[transaction_id]
            
            if status == 'approved':
                transacao['status'] = 'pago'
                transacao['paid_at'] = datetime.now()
                
                # Aqui você adicionaria os créditos ao banco de dados real
                # Em produção, seria algo como:
                # user = User.query.filter_by(phone=transacao['user_phone']).first()
                # user.credits += transacao['valor_total']
                # db.session.commit()
                
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
