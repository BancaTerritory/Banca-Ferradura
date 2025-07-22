from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'sua-chave-secreta-super-segura-aqui-2024')
    
    # Configurar CORS para permitir requisições de qualquer origem
    CORS(app)
    
    # Importar e registrar blueprints com tratamento de erro
    try:
        from routes.auth_routes import auth_blueprint
        app.register_blueprint(auth_blueprint)
    except ImportError as e:
        print(f"Erro ao importar auth_routes: {e}")
    
    try:
        from routes.game_routes import game_blueprint
        app.register_blueprint(game_blueprint)
    except ImportError as e:
        print(f"Erro ao importar game_routes: {e}")
    
    try:
        from routes.pix_routes import pix_blueprint
        app.register_blueprint(pix_blueprint)
    except ImportError as e:
        print(f"Erro ao importar pix_routes: {e}")
    
    @app.route('/')
    def index():
        """Página principal - Dashboard"""
        try:
            if not session.get("user_phone"):
                return redirect(url_for("auth.login_page"))
            
            # Dados do usuário para o dashboard
            user_data = {
                'phone': session.get("user_phone"),
                'credits': session.get("user_credits", 0.0),
                'name': session.get("user_name", "Usuário")
            }
            
            return render_template('index.html', user=user_data)
        except Exception as e:
            print(f"Erro na rota index: {e}")
            return f"Erro interno: {str(e)}", 500
    
    @app.route('/dashboard')
    def dashboard():
        """Redirecionar para página principal"""
        return redirect(url_for("index"))
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Página de erro 404"""
        return f"Página não encontrada: {str(e)}", 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Página de erro 500"""
        return f"Erro interno do servidor: {str(e)}", 500
    
    # Rota de teste para verificar se o app está funcionando
    @app.route('/test')
    def test():
        return "App funcionando corretamente!"
    
    return app

# Criar aplicação
app = create_app()

# Para Vercel (importante!)
def handler(event, context):
    return app

# Para desenvolvimento local
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
