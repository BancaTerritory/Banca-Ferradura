from src.main import app

# Handler para Vercel
def handler(request, response):
    return app(request.environ, response)

# Exportar app para Vercel
app = app
