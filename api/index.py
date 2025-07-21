from src.main import app

# Para Vercel - exportar a aplicação Flask
application = app

# Handler para Vercel
def handler(request):
    return app(request.environ, start_response)

# Exportar para Vercel
if __name__ == "__main__":
    app.run()
