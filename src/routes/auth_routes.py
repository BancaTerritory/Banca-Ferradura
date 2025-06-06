import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # DON'T CHANGE THIS !!!

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import random
import string
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenciais do Twilio a partir de variáveis de ambiente
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'ACb43a431fa025e2cc4ca995ae474a52c9')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '63817bea093d6f189aa5f4cac963a318')
TWILIO_VERIFY_SERVICE_ID = os.getenv('TWILIO_VERIFY_SERVICE_ID', 'VAe357d2ce1d153201d31c423d830deb6e')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+12189750606')

# For a prototype, we'll use a simple in-memory dictionary to store users and their passwords.
# In a real application, you would use a database.
# { "phone_number_complete": { "name": "User Name", "password": "xxxx", "credits": 0.0, "verified": False, "verification_code": "yyyy" } }
users_db = {}

# Administrador - Login por e-mail
admin_credentials = {
    "email": "admin@bancaferradura.com",
    "password": "admin123",
    "name": "Administrador Principal"
}

auth_bp = Blueprint("auth", __name__)


def generate_short_code(length=4):
    return "".join(random.choices(string.digits, k=length))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        ddd = request.form.get("ddd")
        phone_number_part = request.form.get("phone_number")

        if not name or not ddd or not phone_number_part:
            flash("Nome, DDD e número de celular são obrigatórios.", "error")
            return redirect(url_for("auth.register"))
        
        if not ddd.isdigit() or len(ddd) != 2:
            flash("DDD inválido. Deve conter 2 dígitos.", "error")
            return redirect(url_for("auth.register"))

        if not phone_number_part.isdigit() or not (8 <= len(phone_number_part) <= 9):
            flash("Número de celular inválido. Deve conter 8 ou 9 dígitos.", "error")
            return redirect(url_for("auth.register"))

        full_phone_number = ddd + phone_number_part

        if full_phone_number in users_db:
            flash("Este número de celular (DDD + Número) já está cadastrado. Tente fazer login.", "error")
            return redirect(url_for("auth.register"))

        # Armazenar dados do usuário temporariamente
        users_db[full_phone_number] = {
            "name": name,
            "password": None, 
            "credits": 0.0,
            "verified": False,
            "is_admin": False # Jogadores nunca são admin por este fluxo
        }
        
        session["registering_phone"] = full_phone_number
        
        # Formatando o número para o padrão internacional exigido pelo Twilio
        international_phone = "+55" + full_phone_number
        
        try:
            # Inicializar cliente Twilio
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
            # Gerar código de verificação
            verification_code = generate_short_code(4)
            users_db[full_phone_number]["verification_code"] = verification_code
            
            # Enviar código de verificação via SMS direto
            message = client.messages.create(
                body=f"Banca Ferradura: Seu código de verificação é {verification_code}",
                from_=TWILIO_PHONE_NUMBER,
                to=international_phone
            )
            
            flash(f"Um código de verificação foi enviado para o número {full_phone_number}. Por favor, insira o código recebido por SMS para ativar sua conta.", "info")
            return redirect(url_for("auth.verify_code_page"))
        except Exception as e:
            # Em caso de erro, informamos o usuário e removemos o cadastro temporário
            users_db.pop(full_phone_number, None)
            session.pop("registering_phone", None)
            flash(f"Não foi possível enviar o SMS: {str(e)}. Por favor, verifique se o número está correto e tente novamente.", "error")
            return redirect(url_for("auth.register"))

    return render_template("register.html")

@auth_bp.route("/verify-code", methods=["GET", "POST"])
def verify_code_page():
    registering_phone = session.get("registering_phone")
    if not registering_phone or registering_phone not in users_db or users_db[registering_phone].get("verified", False):
        flash("Não há processo de registro pendente ou usuário já verificado.", "warning")
        return redirect(url_for("auth.register"))

    user_data_pending = users_db[registering_phone]

    if request.method == "POST":
        code_entered = request.form.get("verification_code")
        if not code_entered:
            flash("Código de verificação é obrigatório.", "error")
            return render_template("verify_code.html", phone=registering_phone, name=user_data_pending.get("name"))

        # Formatando o número para o padrão internacional exigido pelo Twilio
        international_phone = "+55" + registering_phone
        
        try:
            # Verificar o código inserido pelo usuário comparando com o código armazenado
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            stored_code = users_db[registering_phone].get("verification_code")
            
            if stored_code and code_entered == stored_code:
                # Código correto, ativar a conta e gerar senha
                final_password = generate_short_code(6)  # Senha de 6 dígitos para maior segurança
                users_db[registering_phone]["password"] = final_password
                users_db[registering_phone]["verified"] = True
                
                try:
                    # Enviar senha via SMS direto
                    message = client.messages.create(
                        body=f"Banca Ferradura: Sua senha de acesso é {final_password}. Guarde-a com segurança!",
                        from_=TWILIO_PHONE_NUMBER,
                        to=international_phone
                    )
                    
                    session.pop("registering_phone", None)
                    # Logar o usuário automaticamente após verificação bem-sucedida
                    session["user_phone"] = registering_phone
                    session["user_name"] = user_data_pending.get("name")
                    session["user_credits"] = user_data_pending.get("credits", 0.0)
                    session["is_admin"] = False # Garante que é um jogador
                    flash(f"Cadastro de {user_data_pending.get('name')} confirmado! Sua senha de acesso foi enviada por SMS. Você já está logado.", "success")
                    return redirect(url_for("main.index")) # Redireciona para o dashboard do jogador
                except Exception as e:
                    # Em caso de erro no envio da senha, informamos o usuário
                    flash(f"Seu cadastro foi confirmado, mas não foi possível enviar a senha por SMS: {str(e)}. Por favor, entre em contato com o suporte.", "error")
                    return redirect(url_for("main.index"))
            else:
                flash("Código de verificação inválido. Tente novamente.", "error")
                return render_template("verify_code.html", phone=registering_phone, name=user_data_pending.get("name"))
        except Exception as e:
            flash(f"Erro na verificação: {str(e)}. Por favor, tente novamente ou entre em contato com o suporte.", "error")
            return render_template("verify_code.html", phone=registering_phone, name=user_data_pending.get("name"))

    return render_template("verify_code.html", phone=registering_phone, name=user_data_pending.get("name"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page(): 
    if request.method == "POST":
        ddd = request.form.get("ddd")
        phone_number_part = request.form.get("phone_number")
        password = request.form.get("password")

        if not ddd or not phone_number_part or not password:
            flash("DDD, número de celular e senha são obrigatórios.", "error")
            return redirect(url_for("auth.login_page"))
        
        full_phone_number = ddd + phone_number_part
        user = users_db.get(full_phone_number)

        if user and user.get("verified") and user["password"] == password and not user.get("is_admin"):
            session["user_phone"] = full_phone_number
            session["user_name"] = user.get("name")
            session["user_credits"] = user.get("credits", 0.0)
            session["is_admin"] = False
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("main.index")) # Dashboard do jogador
        elif user and not user.get("verified"):
            flash("Sua conta ainda não foi verificada. Por favor, complete o processo de verificação.", "warning")
            session["registering_phone"] = full_phone_number 
            return redirect(url_for("auth.verify_code_page"))
        else:
            flash("DDD/Número de celular ou senha inválidos.", "error")
            return redirect(url_for("auth.login_page"))
    return render_template("login.html")

@auth_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("E-mail e senha são obrigatórios.", "error")
            return redirect(url_for("auth.admin_login_page"))

        if email == admin_credentials["email"] and password == admin_credentials["password"]:
            session["admin_logged_in"] = True
            session["admin_name"] = admin_credentials["name"]
            session["is_admin"] = True # Definindo explicitamente que é um admin na sessão
            # Limpar qualquer sessão de jogador que possa existir
            session.pop("user_phone", None)
            session.pop("user_name", None)
            session.pop("user_credits", None)
            flash("Login de administrador realizado com sucesso!", "success")
            # Futuramente redirecionar para url_for('admin.dashboard') ou similar
            return redirect(url_for("main.index")) # Por enquanto, redireciona para o index principal
        else:
            flash("E-mail ou senha de administrador inválidos.", "error")
            return redirect(url_for("auth.admin_login_page"))
    return render_template("admin_login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user_phone", None)
    session.pop("user_name", None)
    session.pop("user_credits", None)
    session.pop("is_admin", None)
    session.pop("registering_phone", None)
    session.pop("admin_logged_in", None) # Limpar sessão de admin
    session.pop("admin_name", None)
    flash("Você foi desconectado.", "success")
    return redirect(url_for("main.index"))
