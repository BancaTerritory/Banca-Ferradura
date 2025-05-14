import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # DON'T CHANGE THIS !!!

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import datetime

# Import shared data stores (NOT ideal for production, but used in this prototype)
from src.routes.payment_routes import transactions_db # List of transaction dicts
from src.routes.auth_routes import users_db # Dict of user dicts

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")

# --- Utility / Decorator for admin routes ---
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in") or not session.get("is_admin"):
            flash("Acesso restrito a administradores.", "error")
            return redirect(url_for("auth.admin_login_page"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__ # Preserve original function name for Flask
    return decorated_function

# --- Jinja2 Filter for Datetime Formatting ---
@admin_bp.app_template_filter()
def format_datetime(value, format="%d/%m/%Y %H:%M:%S"):
    if value is None:
        return ""
    try:
        # Assuming value is an ISO format string as stored
        dt_object = datetime.datetime.fromisoformat(value)
        return dt_object.strftime(format)
    except (ValueError, TypeError):
        return value # Return original if parsing fails

# --- Admin Routes ---
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    recharges = sorted([tx for tx in transactions_db if tx["type"] == "recharge"], key=lambda x: x["timestamp"], reverse=True)
    withdrawals = sorted([tx for tx in transactions_db if tx["type"] == "withdrawal"], key=lambda x: x["timestamp"], reverse=True)
    return render_template("dashboard.html", transactions_recharge=recharges, transactions_withdrawal=withdrawals)

@admin_bp.route("/approve_withdrawal/<transaction_id>", methods=["POST"])
@admin_required
def approve_withdrawal(transaction_id):
    transaction_to_approve = None
    for tx in transactions_db:
        if tx["id"] == transaction_id and tx["type"] == "withdrawal" and tx["status"] == "pending_approval":
            transaction_to_approve = tx
            break
    
    if transaction_to_approve:
        transaction_to_approve["status"] = "completed"
        # Note: The amount was already deducted from user's balance upon request.
        # If it wasn't, this is where you'd deduct it.
        flash(f"Saque ID {transaction_id[:8]}... aprovado e marcado como concluído.", "success")
    else:
        flash(f"Saque ID {transaction_id[:8]}... não encontrado ou já processado.", "error")
    
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/reject_withdrawal/<transaction_id>", methods=["POST"])
@admin_required
def reject_withdrawal(transaction_id):
    transaction_to_reject = None
    for tx in transactions_db:
        if tx["id"] == transaction_id and tx["type"] == "withdrawal" and tx["status"] == "pending_approval":
            transaction_to_reject = tx
            break
            
    if transaction_to_reject:
        transaction_to_reject["status"] = "rejected"
        # IMPORTANT: Credit the amount back to the user's balance
        user_phone = transaction_to_reject["user_phone"]
        amount_to_credit_back = transaction_to_reject["amount"]
        if user_phone in users_db:
            users_db[user_phone]["credits"] = users_db[user_phone].get("credits", 0.0) + amount_to_credit_back
            # Update session if the admin is somehow also this user (unlikely, but good practice)
            if session.get("user_phone") == user_phone:
                 session["user_credits"] = users_db[user_phone]["credits"]
            flash(f"Saque ID {transaction_id[:8]}... rejeitado. R$ {amount_to_credit_back:.2f} estornado para o usuário {user_phone}.", "success")
        else:
            flash(f"Saque ID {transaction_id[:8]}... rejeitado, mas houve um erro ao estornar o valor para o usuário {user_phone}. Verifique manualmente.", "error")
    else:
        flash(f"Saque ID {transaction_id[:8]}... não encontrado ou já processado.", "error")
        
    return redirect(url_for("admin.dashboard"))


