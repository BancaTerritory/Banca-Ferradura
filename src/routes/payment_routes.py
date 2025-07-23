import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import uuid
import datetime

from src.routes.auth_routes import users_db

payment_bp = Blueprint("payments", __name__)

# In-memory list to store transactions
transactions_db = []

@payment_bp.route("/add_credits", methods=["GET", "POST"])
def add_credits_page():
    if "user_phone" not in session:
        flash("Você precisa estar logado para adicionar créditos.", "error")
        return redirect(url_for("auth.login_page"))
    
    pix_code_to_display = session.pop("pix_code_to_display", None)
    
    if request.method == "POST":
        try:
            amount_str = request.form.get("amount")
            if not amount_str:
                flash("Por favor, insira um valor.", "error")
                return redirect(url_for("payments.add_credits_page"))
            
            amount = float(amount_str)
            
            if amount <= 0:
                flash("O valor da recarga deve ser positivo.", "error")
                return redirect(url_for("payments.add_credits_page"))
            
            user_phone = session["user_phone"]
            
            # Gerar código PIX simulado
            transaction_id = str(uuid.uuid4())
            pix_code = f"00020126580014BR.GOV.BCB.PIX0136{user_phone}@pix.com.br52040000530398654{amount:.2f}5802BR5925BANCA FERRADURA LTDA6009SAO PAULO62{len(transaction_id):02d}{transaction_id}6304"
            
            # Calcular dígito verificador simples
            checksum = sum(ord(c) for c in pix_code) % 100
            pix_code += f"{checksum:02d}"
            
            new_recharge_transaction = {
                "id": transaction_id,
                "user_phone": user_phone,
                "user_name": session.get("user_name", "N/A"),
                "type": "recharge",
                "amount": amount,
                "pix_key": None,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "simulated_completed"
            }
            transactions_db.append(new_recharge_transaction)
            
            if user_phone in users_db:
                users_db[user_phone]["credits"] = users_db[user_phone].get("credits", 0.0) + amount
                session["user_credits"] = users_db[user_phone]["credits"]
                flash(f"PIX Copia e Cola gerado para R$ {amount:.2f}. Seu saldo foi atualizado (simulação).", "success")
            else:
                flash("Erro ao encontrar usuário para creditar (simulação).", "error")
            
            return render_template("payments/add_credits.html", pix_code=pix_code)
            
        except ValueError:
            flash("Valor inválido para recarga.", "error")
            return redirect(url_for("payments.add_credits_page"))
    
    return render_template("payments/add_credits.html", pix_code=pix_code_to_display)

@payment_bp.route("/request_withdrawal", methods=["GET", "POST"])
def request_withdrawal_page():
    if "user_phone" not in session:
        flash("Você precisa estar logado para solicitar um saque.", "error")
        return redirect(url_for("auth.login_page"))
    
    user_phone = session["user_phone"]
    current_balance = users_db.get(user_phone, {}).get("credits", 0.0)
    session["user_credits"] = current_balance
    
    if request.method == "POST":
        try:
            amount_str = request.form.get("amount")
            pix_key = request.form.get("pix_key")
            
            if not amount_str or not pix_key:
                flash("Valor do saque e chave PIX são obrigatórios.", "error")
                return redirect(url_for("payments.request_withdrawal_page"))
            
            amount = float(amount_str)
            
            if amount <= 0:
                flash("O valor do saque deve ser positivo.", "error")
                return redirect(url_for("payments.request_withdrawal_page"))
            
            if amount > current_balance:
                flash(f"Saldo insuficiente para sacar R$ {amount:.2f}. Seu saldo é R$ {current_balance:.2f}.", "error")
                return redirect(url_for("payments.request_withdrawal_page"))
            
            # Deduzir valor do saldo
            users_db[user_phone]["credits"] -= amount
            session["user_credits"] = users_db[user_phone]["credits"]
            
            # Registrar transação de saque
            transaction_id = str(uuid.uuid4())
            new_withdrawal_transaction = {
                "id": transaction_id,
                "user_phone": user_phone,
                "user_name": session.get("user_name", "N/A"),
                "type": "withdrawal",
                "amount": amount,
                "pix_key": pix_key,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "pending_approval"
            }
            transactions_db.append(new_withdrawal_transaction)
            
            flash(f"Solicitação de saque de R$ {amount:.2f} para a chave PIX '{pix_key}' recebida. Será processada em até 24 horas.", "success")
            return redirect(url_for("main.index"))
            
        except ValueError:
            flash("Valor de saque inválido.", "error")
            return redirect(url_for("payments.request_withdrawal_page"))
    
    return render_template("payments/request_withdrawal.html")
