from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import os
from dotenv import load_dotenv
from api.contapay import ContaPayAPI

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa a API da ContaPay com o token
contapay_token = os.getenv("CONTAPAY_TOKEN", "441e3114e87449b4c744a2a6f483c52e1598bb3a1aa18bcf1125b9e466e3a67e")
contapay_api = ContaPayAPI(token=contapay_token)

payment_bp = Blueprint('payment', __name__)

# Rota para adicionar créditos (recarga)
@payment_bp.route('/add_credits')
def add_credits():
    return render_template('payments/add_credits.html')

# Rota para processar a recarga via PIX
@payment_bp.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        flash('Você precisa estar logado para adicionar créditos.')
        return redirect(url_for('auth.login'))
    
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
            description=f"Recarga de créditos - Usuário {session['user_id']}"
        )
        
        # Salva o ID do pagamento na sessão para verificação posterior
        session['pending_payment'] = {
            'payment_id': payment_data['id'],
            'amount': amount_float
        }
        
        # Retorna para a página com o código PIX
        return render_template('payments/payment_code.html', 
                              pix_code=payment_data['pix_code'],
                              amount=amount_float)
        
    except ValueError:
        flash('Valor inválido. Por favor, insira um valor numérico.')
        return redirect(url_for('payment.add_credits'))
    except Exception as e:
        flash(f'Erro ao processar pagamento: {str(e)}')
        return redirect(url_for('payment.add_credits'))

# Rota para receber notificações da ContaPay
@payment_bp.route('/webhook/contapay', methods=['POST'])
def contapay_webhook():
    data = request.json
    
    # Verifica se é uma notificação de pagamento
    if data['event'] == 'payment.status_update':
        payment_id = data['payment_id']
        status = data['status']
        
        # Busca o usuário associado a este pagamento (implementação simplificada)
        # Em um sistema real, você teria uma tabela de pagamentos com user_id
        
        if status == 'PAID':
            # Pagamento confirmado, adiciona créditos ao usuário
            # Aqui você implementaria a lógica para adicionar créditos ao saldo do usuário
            pass
        elif status in ['OVERDUE', 'CANCELED']:
            # Pagamento expirado ou cancelado
            # Aqui você implementaria a lógica para notificar o usuário
            pass
    
    return jsonify({'status': 'success'})

# Rota para solicitar saque
@payment_bp.route('/request_withdrawal')
def request_withdrawal():
    if 'user_id' not in session:
        flash('Você precisa estar logado para solicitar um saque.')
        return redirect(url_for('auth.login'))
    
    return render_template('payments/request_withdrawal.html')

# Rota para processar o saque
@payment_bp.route('/process_withdrawal', methods=['POST'])
def process_withdrawal():
    if 'user_id' not in session:
        flash('Você precisa estar logado para solicitar um saque.')
        return redirect(url_for('auth.login'))
    
    amount = request.form.get('amount')
    pix_key = request.form.get('pix_key')
    
    try:
        # Converte para float e valida o valor
        amount_float = float(amount.replace('R$', '').replace(',', '.').strip())
        
        if amount_float <= 0:
            flash('O valor deve ser maior que zero.')
            return redirect(url_for('payment.request_withdrawal'))
        
        # Verifica se o usuário tem saldo suficiente
        # Aqui você implementaria a verificação do saldo do usuário
        
        # Solicita o saque via ContaPay
        withdrawal_data = contapay_api.request_withdrawal(
            amount=amount_float,
            pix_key=pix_key
        )
        
        # Salva o ID do saque na sessão para verificação posterior
        session['pending_withdrawal'] = {
            'withdrawal_id': withdrawal_data['id'],
            'amount': amount_float
        }
        
        # Desconta o valor do saldo do usuário
        # Aqui você implementaria a lógica para descontar do saldo
        
        flash('Saque solicitado com sucesso! O valor será transferido para sua chave PIX em breve.')
        return redirect(url_for('user.dashboard'))
        
    except ValueError:
        flash('Valor inválido. Por favor, insira um valor numérico.')
        return redirect(url_for('payment.request_withdrawal'))
    except Exception as e:
        flash(f'Erro ao processar saque: {str(e)}')
        return redirect(url_for('payment.request_withdrawal'))
