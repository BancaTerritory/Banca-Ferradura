import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # DON'T CHANGE THIS !!!

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import uuid # For generating a unique (but still simulated) PIX code
import datetime # For timestamping transactions

# This would normally come from auth_routes or a shared user model/db access layer
# For simplicity in this prototype, we'll access the global users_db from auth_routes
# This is NOT good practice for a real application but simplifies the prototype.
from src.routes.auth_routes import users_db 

payment_bp = Blueprint("payments", __name__)

# In-memory list to store transactions (recharges and later, withdrawals)
# Each transaction: {"id": "uuid", "user_phone": "phone", "user_name": "name", "type": "recharge"/"withdrawal", "amount": float, "pix_key": "string (for withdrawals)", "timestamp": "datetime", "status": "simulated_pending_confirmation"/"pending_approval"/"completed"/"rejected"}
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
            
            generated_pix_code = f"00020126330014BR.GOV.BCB.PIX0111{user_phone.replace("(", "").replace(")", "").replace("-", "")}5204000053039865802BR5913BancaFerradura6009SAO PAULO62070503***6304{str(uuid.uuid4())[:4].upper()}"
            session["pix_code_to_display"] = generated_pix_code

            transaction_id = str(uuid.uuid4())
            new_recharge_transaction = {
                "id": transaction_id,
                "user_phone": user_phone,
                "user_name": session.get("user_name", "N/A"),
                "type": "recharge",
                "amount": amount,
                "pix_key": None, # Not applicable for recharges
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "simulated_completed" # Assuming PIX is paid and auto-confirmed for simulation
            }
            transactions_db.append(new_recharge_transaction)

            if user_phone in users_db:
                users_db[user_phone]["credits"] = users_db[user_phone].get("credits", 0.0) + amount
                session["user_credits"] = users_db[user_phone]["credits"]
                flash(f"PIX Copia e Cola gerado para R$ {amount:.2f}. Seu saldo foi atualizado (simulação).", "success")
            else:
                flash("Erro ao encontrar usuário para creditar (simulação).", "error")

            return redirect(url_for("payments.add_credits_page"))
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
    session["user_credits"] = current_balance # Ensure session is up to date

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

            # Deduct amount from user's balance
            users_db[user_phone]["credits"] -= amount
            session["user_credits"] = users_db[user_phone]["credits"]

            # Record the withdrawal transaction
            transaction_id = str(uuid.uuid4())
            new_withdrawal_transaction = {
                "id": transaction_id,
                "user_phone": user_phone,
                "user_name": session.get("user_name", "N/A"),
                "type": "withdrawal",
                "amount": amount,
                "pix_key": pix_key,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "pending_approval" # Admin needs to approve and process this
            }
            transactions_db.append(new_withdrawal_transaction)

            flash(f"Solicitação de saque de R$ {amount:.2f} para a chave PIX '{pix_key}' recebida. Será processada em até 24 horas.", "success")
            return redirect(url_for("main.index")) # Redirect to player dashboard

        except ValueError:
            flash("Valor de saque inválido.", "error")
            return redirect(url_for("payments.request_withdrawal_page"))

    return render_template("payments/request_withdrawal.html")


