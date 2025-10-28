"""
Banco de dados em memória para protótipo.
Em produção, substituir por banco de dados real (PostgreSQL, MySQL, etc.)
"""

# Banco de dados de usuários
# Estrutura: { "phone_number": { "name": str, "password": str, "credits": float, "verified": bool, "is_admin": bool } }
users_db = {}

# Banco de dados de transações
# Estrutura: [ { "id": str, "user_phone": str, "type": str, "amount": float, "status": str, "timestamp": str, ... } ]
transactions_db = []

# Credenciais de administrador
admin_credentials = {
    "email": "admin@bancaferradura.com",
    "password": "admin123",
    "name": "Administrador"
}
