import os
import requests
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

class WhatsAppAdapter:
    """Adaptador para integração com a API oficial do WhatsApp Business"""
    
    def __init__(self):
        # Carrega as variáveis de ambiente do arquivo .env
        load_dotenv(override=True)
        
        # Obtém as configurações do WhatsApp
        self.api_url = os.getenv("WHATSAPP_API_URL")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        
        # Valida as configurações
        if not self.api_url:
            raise ValueError("WHATSAPP_API_URL não configurado no arquivo .env")
        if not self.phone_number_id:
            raise ValueError("WHATSAPP_PHONE_NUMBER_ID não configurado no arquivo .env")
        if not self.access_token:
            raise ValueError("WHATSAPP_ACCESS_TOKEN não configurado no arquivo .env")
    
    def send_message(self, to: str, message: str) -> bool:
        """
        Envia uma mensagem via WhatsApp Business API
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
            return False
    
    def handle_webhook(self, data: dict) -> Optional[tuple[str, str]]:
        """
        Processa webhooks recebidos do WhatsApp
        Retorna: (número_remetente, mensagem) ou None se não for uma mensagem válida
        """
        try:
            # Verifica se é uma mensagem de texto
            if "entry" in data and data["entry"]:
                entry = data["entry"][0]
                if "changes" in entry and entry["changes"]:
                    change = entry["changes"][0]
                    if "value" in change and "messages" in change["value"]:
                        message = change["value"]["messages"][0]
                        if message["type"] == "text":
                            return (
                                message["from"],
                                message["text"]["body"]
                            )
            return None
        except Exception as e:
            print(f"Erro ao processar webhook WhatsApp: {str(e)}")
            return None 