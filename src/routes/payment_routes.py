from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import os
from dotenv import load_dotenv
from api.contapay import ContaPayAPI
import qrcode
import io
import base64
from datetime import datetime
import uuid
from src.database import transactions_db

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa a API da ContaPay com o token
contapay_token = os.getenv("CONTAPAY_TOKEN")
contapay_api = ContaPayAPI(token=contapay_token)

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
        
        # Gera o QR Code PIX usando a API da ContaPay
        pix_response = contapay_api.create_pix_charge(
            amount=amount_float,
            description=f"Recarga de créditos - {session.get('user_name')}"
        )
        
        if pix_response and 'qr_code' in pix_response:
            # Registra a transação
            transaction = {
                'id': str(uuid.uuid4()),
                'user_phone': session.get('user_phone'),
                'type': 'recharge',
                'amount': amount_float,
                'status': 'pending',
                'pix_code': pix_response.get('qr_code'),
                'timestamp': datetime.now().isoformat()
            }
            transactions_db.append(transaction)
            
            # Gera o QR Code como imagem
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(pix_response['qr_code'])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converte a imagem para base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return render_template('payment_qrcode.html', 
                                   qr_code_img=img_str, 
                                   pix_code=pix_response['qr_code'],
                                   amount=amount_float)
        else:
            flash('Erro ao gerar QR Code PIX. Tente novamente.')
            return redirect(url_for('payment.add_credits'))
            
    except ValueError:
        flash('Valor inválido. Por favor, insira um valor numérico.')
        return redirect(url_for('payment.add_credits'))
    except Exception as e:
        flash(f'Erro ao processar pagamento: {str(e)}')
        return redirect(url_for('payment.add_credits'))

# Rota para confirmar o pagamento (webhook ou manual)
@payment_bp.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    # Esta rota seria chamada pelo webhook da ContaPay ou manualmente pelo admin
    transaction_id = request.form.get('transaction_id')
    
    # Encontra a transação
    transaction = next((t for t in transactions_db if t['id'] == transaction_id), None)
    
    if transaction and transaction['status'] == 'pending':
        # Atualiza o status da transação
        transaction['status'] = 'completed'
        
        # Adiciona os créditos ao usuário
        user_phone = transaction['user_phone']
        # Aqui você atualizaria o saldo no banco de dados
        # Por enquanto, apenas retorna sucesso
        
        return jsonify({'status': 'success', 'message': 'Pagamento confirmado'})
    
    return jsonify({'status': 'error', 'message': 'Transação não encontrada ou já processada'})

# Rota para solicitar saque
@payment_bp.route('/request_withdrawal', methods=['GET', 'POST'])
def request_withdrawal():
    if 'user_phone' not in session:
        flash('Você precisa estar logado para solicitar saque.')
        return redirect(url_for('auth.login_page'))
    
    if request.method == 'POST':
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
    
    return render_template('request_withdrawal.html')
