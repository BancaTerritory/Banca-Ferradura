import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # DON'T CHANGE THIS !!!

from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # Verificar se o usuário está autenticado
    if "user_phone" in session or "admin_logged_in" in session:
        # Se estiver autenticado, mostrar a dashboard
        return render_template("index.html")
    else:
        # Se não estiver autenticado, redirecionar para a página de cadastro/login
        return redirect(url_for("auth.register"))


