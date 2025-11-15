from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-super-segura-aqui-2024')
    
    # Configurar CORS para permitir requisições de qualquer origem
    CORS(app)
    
    # Importar blueprints
    from src.routes.auth_routes import auth_bp
    from src.routes.game_routes import game_blueprint
    from src.routes.payment_routes import payment_bp
    from src.routes.admin_routes import admin_bp
    from src.routes.casino_routes import casino_bp
    from src.routes.lottery_routes import lottery_bp
    from src.routes.main_routes import main_bp
    from src.routes.user import user_bp
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_blueprint)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(casino_bp)
    app.register_blueprint(lottery_bp, url_prefix='/lottery')
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    
    # Rotas principais agora estão em main_routes.py
    # Removido para evitar conflito com main_bp
    
    return app

# Criar aplicação
app = create_app()

# Para desenvolvimento local
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

