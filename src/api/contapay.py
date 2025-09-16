import requests
import json

class ContaPayAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.contapay.me/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def generate_payment(self, amount, description ):
        """Gera um código PIX para pagamento"""
        endpoint = f"{self.base_url}/payments"
        payload = {
            "amount": amount,
            "description": description,
            "type": "pix"
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        return response.json()
    
    def check_payment_status(self, payment_id):
        """Verifica o status de um pagamento"""
        endpoint = f"{self.base_url}/payments/{payment_id}"
        response = requests.get(endpoint, headers=self.headers)
        return response.json()
    
    def request_withdrawal(self, amount, pix_key):
        """Solicita um saque para uma chave PIX"""
        endpoint = f"{self.base_url}/withdrawals"
        payload = {
            "amount": amount,
            "pix_key": pix_key
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        return response.json()
