import os
import requests
import threading
import time
from typing import Optional, Callable
from datetime import datetime
from dotenv import load_dotenv
import redis

class TelegramAdapter:
    """Adaptador para integração com a API do Telegram Bot"""
    
    def __init__(self):
        load_dotenv(override=True)
        
        # Obtém as configurações do Telegram
        self.api_url = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org/bot")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        self.last_update_id = 0
        self.message_handler = None
        self.polling_thread = None
        self.is_polling = False
        
        # Configuração do Redis para lock distribuído
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.lock_key = "telegram_polling_lock"
        self.lock_ttl = 30  # segundos
        
        # Valida as configurações
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado no arquivo .env")
    
    def start_polling(self, message_handler: Callable[[str, str], None]):
        """
        Inicia o polling de mensagens do Telegram
        message_handler: função que será chamada quando uma mensagem for recebida
        """
        self.message_handler = message_handler
        self.is_polling = True
        self.polling_thread = threading.Thread(target=self._poll_messages)
        self.polling_thread.daemon = True
        self.polling_thread.start()
        print("Bot do Telegram iniciado e aguardando mensagens...")
    
    def stop_polling(self):
        """Para o polling de mensagens"""
        self.is_polling = False
        if self.polling_thread:
            self.polling_thread.join()
    
    def _acquire_lock(self) -> bool:
        """Tenta adquirir o lock distribuído"""
        return self.redis_client.set(
            self.lock_key,
            "1",
            ex=self.lock_ttl,
            nx=True
        )
    
    def _release_lock(self):
        """Libera o lock distribuído"""
        self.redis_client.delete(self.lock_key)
    
    def _poll_messages(self):
        """Método interno para fazer polling de mensagens"""
        while self.is_polling:
            try:
                # Tenta adquirir o lock
                if not self._acquire_lock():
                    time.sleep(1)
                    continue
                
                try:
                    url = f"{self.api_url}{self.bot_token}/getUpdates"
                    params = {
                        "offset": self.last_update_id + 1,
                        "timeout": 10  # 10 segundos para o polling
                    }
                    
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    
                    updates = response.json().get("result", [])
                    
                    for update in updates:
                        self.last_update_id = update["update_id"]
                        
                        if "message" in update and "text" in update["message"]:
                            chat_id = str(update["message"]["chat"]["id"])
                            text = update["message"]["text"]
                            
                            if self.message_handler:
                                self.message_handler(chat_id, text)
                
                finally:
                    # Sempre libera o lock ao finalizar
                    self._release_lock()
                
            except Exception as e:
                print(f"Erro no polling do Telegram: {str(e)}")
                time.sleep(5)  # Espera 5 segundos antes de tentar novamente
    
    def send_message(self, chat_id: str, message: str) -> bool:
        """
        Envia uma mensagem via Telegram Bot API
        """
        try:
            url = f"{self.api_url}{self.bot_token}/sendMessage"
            
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Erro ao enviar mensagem Telegram: {str(e)}")
            return False
    
    def handle_webhook(self, data: dict) -> Optional[tuple[str, str]]:
        """
        Processa webhooks recebidos do Telegram
        Retorna: (chat_id, mensagem) ou None se não for uma mensagem válida
        """
        try:
            # Verifica se é uma mensagem de texto
            if "message" in data and "text" in data["message"]:
                return (
                    str(data["message"]["chat"]["id"]),
                    data["message"]["text"]
                )
            return None
        except Exception as e:
            print(f"Erro ao processar webhook Telegram: {str(e)}")
            return None 