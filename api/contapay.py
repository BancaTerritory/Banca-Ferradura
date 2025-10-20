import requests
import os
from typing import Dict, Optional

class ContaPayAPI:
    """Classe para integração com a API da ContaPay"""
    
    BASE_URL = "https://api.contapay.com.br/v1"
    
    def __init__(self, token: str ):
        """
        Inicializa a API da ContaPay
        
        Args:
            token: Token de autenticação da API
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def generate_payment(self, amount: float, description: str) -> Dict:
        """
        Gera uma cobrança PIX
        
        Args:
            amount: Valor da cobrança em reais
            description: Descrição da cobrança
            
        Returns:
            Dicionário com dados do pagamento (id, pix_code, qr_code, etc)
        """
        endpoint = f"{self.BASE_URL}/charges"
        
        payload = {
            "value": amount,
            "description": description,
            "payment_method": "pix"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao gerar pagamento: {str(e)}")
    
    def get_payment_status(self, payment_id: str) -> Dict:
        """
        Consulta o status de um pagamento
        
        Args:
            payment_id: ID do pagamento
            
        Returns:
            Dicionário com status do pagamento
        """
        endpoint = f"{self.BASE_URL}/charges/{payment_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao consultar pagamento: {str(e)}")
    
    def request_withdrawal(self, amount: float, pix_key: str, pix_key_type: str = "random") -> Dict:
        """
        Solicita um saque via PIX
        
        Args:
            amount: Valor do saque em reais
            pix_key: Chave PIX de destino
            pix_key_type: Tipo da chave (cpf, cnpj, email, phone, random)
            
        Returns:
            Dicionário com dados do saque
        """
        endpoint = f"{self.BASE_URL}/withdrawals"
        
        payload = {
            "value": amount,
            "pix_key": pix_key,
            "pix_key_type": pix_key_type
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao solicitar saque: {str(e)}")
