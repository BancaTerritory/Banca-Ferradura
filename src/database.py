# src/database.py
# Centralized data storage to avoid circular imports

# User database: stores user information
users_db = {}

# Transaction database: stores all transactions (recharges and withdrawals)
transactions_db = []

# Admin credentials
admin_credentials = {
    "username": "admin",
    "password": "admin123"
}
