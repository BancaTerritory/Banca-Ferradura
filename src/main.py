from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-super-segura-aqui-2024')
    
    # Configurar CORS
    CORS(app)
    
    # Importar apenas as rotas que funcionavam antes
    from routes.auth_routes import auth_blueprint
    from routes.game_routes import game_blueprint
    
    # Registrar blueprints
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(game_blueprint)
    
    @app.route('/')
    def index():
        """Página principal - Dashboard"""
        if not session.get("user_phone"):
            return redirect(url_for("auth.login_page"))
        
        # Dados do usuário para o dashboard
        user_data = {
            'phone': session.get("user_phone"),
            'credits': session.get("user_credits", 0.0),
            'name': session.get("user_name", "Usuário")
        }
        
        return render_template('index.html', user=user_data)
    
    @app.route('/dashboard')
    def dashboard():
        """Redirecionar para página principal"""
        return redirect(url_for("index"))
    
    return app

# Criar aplicação
app = create_app()

# Para desenvolvimento local
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
