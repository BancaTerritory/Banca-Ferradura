from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-super-segura-aqui-2024')
    
    # Configurar CORS para permitir requisições de qualquer origem
    CORS(app)
    
    # Importar blueprints
    from routes.auth_routes import auth_blueprint
    from routes.game_routes import game_blueprint
    from routes.pix_routes import pix_blueprint
    
    # Registrar blueprints
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(game_blueprint)
    app.register_blueprint(pix_blueprint)
    
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
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Página de erro 404"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Página de erro 500"""
        return render_template('500.html'), 500
    
    return app

# Criar aplicação
app = create_app()

# Para desenvolvimento local
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
