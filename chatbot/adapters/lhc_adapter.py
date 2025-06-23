import requests
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv(override=True)

class LHCAdapter:
    """
    Adaptador para integração com o Live Helper Chat (LHC)
    Permite enviar mensagens para chats do LHC e receber notificações
    """
    
    def __init__(self):
        """Inicializa o adaptador LHC"""
        self.lhc_url = os.getenv('LHC_URL', 'http://localhost:8081')
        self.lhc_api_key = os.getenv('LHC_API_KEY', '')
        self.lhc_secret_hash = os.getenv('LHC_SECRET_HASH', '')
        
        # Headers padrão para requisições
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.lhc_api_key
        }
        
        logging.info(f"LHCAdapter inicializado - URL: {self.lhc_url}")

    def send_message_to_chat(self, chat_id: int, message: str, user_id: Optional[int] = None) -> bool:
        """
        Envia uma mensagem para um chat específico do LHC
        
        Args:
            chat_id: ID do chat no LHC
            message: Mensagem a ser enviada
            user_id: ID do usuário que está enviando (opcional)
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        try:
            url = f"{self.lhc_url}/restapi/msg/addmsguser"
            
            data = {
                "chat_id": chat_id,
                "msg": message,
                "user_id": user_id or 0
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('error') == False:
                logging.info(f"Mensagem enviada para chat {chat_id}: {message}")
                return True
            else:
                logging.error(f"Erro ao enviar mensagem para chat {chat_id}: {result.get('msg', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem para LHC: {str(e)}")
            return False

    def get_chat_info(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um chat específico
        
        Args:
            chat_id: ID do chat no LHC
            
        Returns:
            Dict com informações do chat ou None se erro
        """
        try:
            url = f"{self.lhc_url}/restapi/chat/getchat"
            
            data = {
                "chat_id": chat_id
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('error') == False:
                return result.get('result', {})
            else:
                logging.error(f"Erro ao obter chat {chat_id}: {result.get('msg', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            logging.error(f"Erro ao obter chat do LHC: {str(e)}")
            return None

    def get_pending_chats(self) -> list:
        """
        Obtém lista de chats pendentes
        
        Returns:
            Lista de chats pendentes
        """
        try:
            url = f"{self.lhc_url}/restapi/chat/getpendingchats"
            
            response = requests.post(url, json={}, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('error') == False:
                return result.get('result', [])
            else:
                logging.error(f"Erro ao obter chats pendentes: {result.get('msg', 'Erro desconhecido')}")
                return []
                
        except Exception as e:
            logging.error(f"Erro ao obter chats pendentes do LHC: {str(e)}")
            return []

    def close_chat(self, chat_id: int, reason: str = "Chat encerrado pelo sistema") -> bool:
        """
        Fecha um chat específico
        
        Args:
            chat_id: ID do chat no LHC
            reason: Motivo do fechamento
            
        Returns:
            bool: True se o chat foi fechado com sucesso
        """
        try:
            url = f"{self.lhc_url}/restapi/chat/closechat"
            
            data = {
                "chat_id": chat_id,
                "reason": reason
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('error') == False:
                logging.info(f"Chat {chat_id} fechado: {reason}")
                return True
            else:
                logging.error(f"Erro ao fechar chat {chat_id}: {result.get('msg', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao fechar chat no LHC: {str(e)}")
            return False

    def transfer_chat(self, chat_id: int, department_id: int) -> bool:
        """
        Transfere um chat para outro departamento
        
        Args:
            chat_id: ID do chat no LHC
            department_id: ID do departamento de destino
            
        Returns:
            bool: True se o chat foi transferido com sucesso
        """
        try:
            url = f"{self.lhc_url}/restapi/chat/transferchat"
            
            data = {
                "chat_id": chat_id,
                "department_id": department_id
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('error') == False:
                logging.info(f"Chat {chat_id} transferido para departamento {department_id}")
                return True
            else:
                logging.error(f"Erro ao transferir chat {chat_id}: {result.get('msg', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao transferir chat no LHC: {str(e)}")
            return False

    def get_departments(self) -> list:
        """
        Obtém lista de departamentos
        
        Returns:
            Lista de departamentos
        """
        try:
            url = f"{self.lhc_url}/restapi/department/getdepartments"
            
            response = requests.post(url, json={}, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get('error') == False:
                return result.get('result', [])
            else:
                logging.error(f"Erro ao obter departamentos: {result.get('msg', 'Erro desconhecido')}")
                return []
                
        except Exception as e:
            logging.error(f"Erro ao obter departamentos do LHC: {str(e)}")
            return []

    def handle_webhook(self, data: dict) -> Optional[tuple[int, str, str]]:
        """
        Processa webhooks recebidos do LHC
        Retorna: (chat_id, user_message, user_id) ou None se não for uma mensagem válida
        
        Args:
            data: Dados do webhook do LHC
            
        Returns:
            Tuple com (chat_id, mensagem, user_id) ou None
        """
        try:
            # Verifica se é uma mensagem de chat
            if "chat_id" in data and "msg" in data:
                chat_id = int(data["chat_id"])
                message = data["msg"]
                user_id = data.get("user_id", "0")
                
                # Ignora mensagens do sistema ou operadores
                if data.get("user_type") == "operator":
                    return None
                    
                return (chat_id, message, user_id)
            return None
            
        except Exception as e:
            logging.error(f"Erro ao processar webhook LHC: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """
        Testa a conexão com o LHC
        
        Returns:
            bool: True se a conexão está funcionando
        """
        try:
            url = f"{self.lhc_url}/restapi/system/getstatus"
            
            response = requests.post(url, json={}, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('error') == False
            
        except Exception as e:
            logging.error(f"Erro ao testar conexão com LHC: {str(e)}")
            return False 