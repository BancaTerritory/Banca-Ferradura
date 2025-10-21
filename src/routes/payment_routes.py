from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import os
from dotenv import load_dotenv
from api.contapay import ContaPayAPI
import qrcode
import io
import base64
from datetime import datetime
import uuid

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa a API da ContaPay com o token
contapay_token = os.getenv("CONTAPAY_TOKEN")
contapay_api = ContaPayAPI(token=contapay_token)

# Banco de dados de transações em memória (para protótipo)
# Em produção, usar banco de dados real
transactions_db = []

payment_bp = Blueprint('payment', __name__)

# Rota para adicionar créditos (recarga)
@payment_bp.route('/add_credits')
def add_credits():
    if 'user_phone' not in session:
        flash('Você precisa estar logado para adicionar créditos.')
        return redirect(url_for('auth.login_page'))
    
    return render_template('add_credits.html')

# Rota para processar a recarga via PIX
@payment_bp.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_phone' not in session:
        flash('Você precisa estar logado para adicionar créditos.')
        return redirect(url_for('auth.login_page'))
    
    amount = request.form.get('amount')
    
    try:
        # Converte para float e valida o valor
        amount_float = float(amount.replace('R$', '').replace(',', '.').strip())
        
        if amount_float <= 0:
            flash('O valor deve ser maior que zero.')
            return redirect(url_for('payment.add_credits'))
        
        # Gera um pagamento PIX via ContaPay
        payment_data = contapay_api.generate_payment(
            amount=amount_float,
            description=f"Recarga de créditos - Usuário {session.get('user_phone')}"
        )
        
        # Gera QR Code
        qr_code_base64 = generate_qr_code(payment_data.get('pix_code', ''))
        
        # Salva o ID do pagamento na sessão para verificação posterior
        session['pending_payment'] = {
            'payment_id': payment_data.get('id'),
            'amount': amount_float
        }
        
        # Registra a transação no banco de dados
        transaction = {
            'id': str(uuid.uuid4()),
            'payment_id': payment_data.get('id'),
            'user_phone': session.get('user_phone'),
            'type': 'recharge',
            'amount': amount_float,
            'status': 'pending',
            'timestamp': datetime.now().isoformat(),
            'pix_code': payment_data.get('pix_code')
        }
        transactions_db.append(transaction)
        
        # Retorna para a página com o código PIX e QR Code
        return render_template('recarga_pix.html', 
                              pix_code=payment_data.get('pix_code'),
                              qr_code_base64=qr_code_base64,
                              amount=amount_float)
        
    except ValueError:
        flash('Valor inválido. Por favor, insira um valor numérico.')
        return redirect(url_for('payment.add_credits'))
    except Exception as e:
        flash(f'Erro ao processar pagamento: {str(e)}')
        return redirect(url_for('payment.add_credits'))

# Função para gerar QR Code
def generate_qr_code(pix_code):
    """Gera QR Code em base64 a partir do código PIX"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(pix_code)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converte para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
    except Exception as e:
        print(f"Erro ao gerar QR Code: {str(e)}")
        return None

# Rota para verificar status do pagamento
@payment_bp.route('/check_payment_status')
def check_payment_status():
    """Verifica se o pagamento foi confirmado"""
    if 'pending_payment' not in session:
        return jsonify({'status': 'NO_PAYMENT'})
    
    payment_id = session['pending_payment'].get('payment_id')
    
    try:
        # Consulta status na ContaPay
        payment_status = contapay_api.get_payment_status(payment_id)
        
        if payment_status.get('status') == 'PAID':
            # Pagamento confirmado - adiciona créditos
            amount = session['pending_payment'].get('amount')
            payment_id = session['pending_payment'].get('payment_id')
            
            # Atualiza status da transação no banco de dados
            for tx in transactions_db:
                if tx.get('payment_id') == payment_id:
                    tx['status'] = 'completed'
                    tx['completed_at'] = datetime.now().isoformat()
                    break
            
            # Atualiza sessão
            current_credits = session.get('user_credits', 0.0)
            session['user_credits'] = current_credits + amount
            
            # Remove pagamento pendente
            session.pop('pending_payment', None)
            
            return jsonify({'status': 'PAID', 'amount': amount})
        
        return jsonify({'status': payment_status.get('status', 'PENDING')})
        
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)})

# Rota para receber notificações da ContaPay (Webhook)
@payment_bp.route('/webhook/contapay', methods=['POST'])
def contapay_webhook():
    """Recebe notificações de pagamento da ContaPay"""
    data = request.json
    
    try:
        # Verifica se é uma notificação de pagamento
        if data.get('event') == 'payment.status_update':
            payment_id = data.get('payment_id')
            status = data.get('status')
            
            # Aqui você deve buscar o usuário associado a este pagamento
            # Em um sistema real, você teria uma tabela de pagamentos com user_id
            
            if status == 'PAID':
                # Pagamento confirmado - adiciona créditos ao usuário
                # Implementar lógica de adicionar créditos ao banco de dados
                pass
            elif status in ['OVERDUE', 'CANCELED']:
                # Pagamento expirado ou cancelado
                # Implementar lógica para notificar o usuário
                pass
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# Rota para solicitar saque
@payment_bp.route('/request_withdrawal')
def request_withdrawal():
    if 'user_phone' not in session:
        flash('Você precisa estar logado para solicitar um saque.')
        return redirect(url_for('auth.login_page'))
    
    return render_template('request_withdrawal.html')

# Rota para processar o saque
@payment_bp.route('/process_withdrawal', methods=['POST'])
def process_withdrawal():
    if 'user_phone' not in session:
        flash('Você precisa estar logado para solicitar um saque.')
        return redirect(url_for('auth.login_page'))
    
    amount = request.form.get('amount')
    pix_key = request.form.get('pix_key')
    
    try:
        # Converte para float e valida o valor
        amount_float = float(amount.replace('R$', '').replace(',', '.').strip())
        
        if amount_float <= 0:
            flash('O valor deve ser maior que zero.')
            return redirect(url_for('payment.request_withdrawal'))
        
        # Verifica se o usuário tem saldo suficiente
        current_credits = session.get('user_credits', 0.0)
        if amount_float > current_credits:
            flash('Saldo insuficiente.')
            return redirect(url_for('payment.request_withdrawal'))
        
        # Registra a transação de saque
        transaction = {
            'id': str(uuid.uuid4()),
            'user_phone': session.get('user_phone'),
            'type': 'withdrawal',
            'amount': amount_float,
            'pix_key': pix_key,
            'status': 'pending_approval',
            'timestamp': datetime.now().isoformat()
        }
        transactions_db.append(transaction)
        
        # Desconta o valor do saldo do usuário (reserva)
        session['user_credits'] = current_credits - amount_float
        
        flash('Saque solicitado com sucesso! Aguarde a aprovação do administrador.')
        return redirect(url_for('main.index'))
        
    except ValueError:
        flash('Valor inválido. Por favor, insira um valor numérico.')
        return redirect(url_for('payment.request_withdrawal'))
    except Exception as e:
        flash(f'Erro ao processar saque: {str(e)}')
        return redirect(url_for('payment.request_withdrawal'))
