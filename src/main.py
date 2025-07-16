import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# from flask_sqlalchemy import SQLAlchemy # Uncomment if using database

# Uncomment the following line if you need to use mysql, do not modify the SQLALCHEMY_DATABASE_URI configuration
# SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
# app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI # Uncomment if using database
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Uncomment if using database

# db = SQLAlchemy(app) # Uncomment if using database

# Import and register blueprints
from src.routes.main_routes import main_bp
from src.routes.auth_routes import auth_bp
# Importa o blueprint de loteria diretamente do arquivo
from flask import Blueprint


from src.routes.payment_routes import payment_bp
from src.routes.game_routes import game_blueprint
from src.routes.casino_routes import casino_bp
from src.routes.admin_routes import admin_bp # Importa o blueprint do admin
from src.routes.lottery_routes import lottery_bp # Importa o blueprint de loteria


app.register_blueprint(main_bp, url_prefix="/")
app.register_blueprint(auth_bp, url_prefix="/auth")
# Registra o blueprint de loteria
app.register_blueprint(lottery_bp, url_prefix="/lottery")

app.register_blueprint(payment_bp, url_prefix="/payments")
app.register_blueprint(game_blueprint, url_prefix="/games")
app.register_blueprint(casino_bp, url_prefix="/casino")
app.register_blueprint(admin_bp, url_prefix="/admin") # Registra o blueprint do admin
#app.register_blueprint(lottery_bp, url_prefix="/lottery") # Registra o blueprint de loteria

if __name__ == "__main__":
    # For development, ensure it runs on 0.0.0.0 to be accessible if exposed
    app.run(host="0.0.0.0", port=5000, debug=True)
