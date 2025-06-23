import logging
from typing import Optional, Tuple
from adapters.lhc_adapter import LHCAdapter
from chatterbot import ChatBot

class LHCService:
    """
    Serviço para integração com o Live Helper Chat
    Gerencia a comunicação entre o chatbot e o LHC
    """
    
    def __init__(self, chatbot: ChatBot):
        """Inicializa o serviço LHC"""
        self.chatbot = chatbot
        self.lhc_adapter = LHCAdapter()
        self.active_chats = {}  # Cache de chats ativos
        
        logging.info("LHCService inicializado")

    def handle_lhc_message(self, chat_id: int, message: str, user_id: str) -> Optional[str]:
        """
        Processa uma mensagem recebida do LHC
        
        Args:
            chat_id: ID do chat no LHC
            message: Mensagem do usuário
            user_id: ID do usuário
            
        Returns:
            Resposta do chatbot ou None se não deve responder
        """
        try:
            # Verifica se o chat está ativo
            if chat_id not in self.active_chats:
                self.active_chats[chat_id] = {
                    'user_id': user_id,
                    'message_count': 0,
                    'last_message': None
                }
            
            # Atualiza contadores
            self.active_chats[chat_id]['message_count'] += 1
            self.active_chats[chat_id]['last_message'] = message
            
            # Processa a mensagem com o chatbot
            response = self.chatbot.get_response(message)
            
            # Envia a resposta para o LHC
            if response:
                success = self.lhc_adapter.send_message_to_chat(
                    chat_id=chat_id,
                    message=str(response),
                    user_id=0  # 0 = sistema/bot
                )
                
                if success:
                    logging.info(f"Resposta enviada para chat {chat_id}: {response}")
                    return str(response)
                else:
                    logging.error(f"Falha ao enviar resposta para chat {chat_id}")
                    return None
            
            return None
            
        except Exception as e:
            logging.error(f"Erro ao processar mensagem LHC: {str(e)}")
            return None

    def handle_webhook(self, data: dict) -> bool:
        """
        Processa webhooks do LHC
        
        Args:
            data: Dados do webhook
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            result = self.lhc_adapter.handle_webhook(data)
            if result:
                chat_id, message, user_id = result
                self.handle_lhc_message(chat_id, message, user_id)
                return True
            return False
            
        except Exception as e:
            logging.error(f"Erro ao processar webhook LHC: {str(e)}")
            return False

    def auto_close_inactive_chats(self, max_inactive_minutes: int = 30) -> int:
        """
        Fecha automaticamente chats inativos
        
        Args:
            max_inactive_minutes: Tempo máximo de inatividade em minutos
            
        Returns:
            int: Número de chats fechados
        """
        try:
            from datetime import datetime, timedelta
            
            closed_count = 0
            current_time = datetime.now()
            
            for chat_id, chat_info in list(self.active_chats.items()):
                if chat_info['last_message']:
                    # Calcula tempo desde última mensagem
                    last_message_time = chat_info['last_message']
                    if isinstance(last_message_time, str):
                        # Se for string, assume que é recente
                        continue
                    
                    time_diff = current_time - last_message_time
                    if time_diff > timedelta(minutes=max_inactive_minutes):
                        # Fecha o chat
                        if self.lhc_adapter.close_chat(chat_id, "Chat encerrado por inatividade"):
                            del self.active_chats[chat_id]
                            closed_count += 1
                            logging.info(f"Chat {chat_id} fechado por inatividade")
            
            return closed_count
            
        except Exception as e:
            logging.error(f"Erro ao fechar chats inativos: {str(e)}")
            return 0

    def transfer_to_human(self, chat_id: int, department_id: int = 1) -> bool:
        """
        Transfere um chat para atendimento humano
        
        Args:
            chat_id: ID do chat
            department_id: ID do departamento de atendimento humano
            
        Returns:
            bool: True se transferido com sucesso
        """
        try:
            # Envia mensagem informando a transferência
            transfer_message = "Estou transferindo você para um atendente humano. Aguarde um momento..."
            self.lhc_adapter.send_message_to_chat(chat_id, transfer_message)
            
            # Transfere o chat
            success = self.lhc_adapter.transfer_chat(chat_id, department_id)
            
            if success:
                # Remove do cache de chats ativos
                if chat_id in self.active_chats:
                    del self.active_chats[chat_id]
                
                logging.info(f"Chat {chat_id} transferido para atendimento humano")
                return True
            else:
                logging.error(f"Falha ao transferir chat {chat_id}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao transferir para humano: {str(e)}")
            return False

    def get_chat_stats(self) -> dict:
        """
        Obtém estatísticas dos chats
        
        Returns:
            dict: Estatísticas dos chats
        """
        try:
            return {
                'active_chats': len(self.active_chats),
                'total_messages': sum(chat['message_count'] for chat in self.active_chats.values()),
                'chat_details': self.active_chats
            }
        except Exception as e:
            logging.error(f"Erro ao obter estatísticas: {str(e)}")
            return {}

    def test_lhc_connection(self) -> bool:
        """
        Testa a conexão com o LHC
        
        Returns:
            bool: True se conectado
        """
        return self.lhc_adapter.test_connection()

    def get_pending_chats(self) -> list:
        """
        Obtém chats pendentes
        
        Returns:
            list: Lista de chats pendentes
        """
        return self.lhc_adapter.get_pending_chats()

    def should_transfer_to_human(self, chat_id: int, message: str) -> bool:
        """
        Determina se um chat deve ser transferido para humano
        
        Args:
            chat_id: ID do chat
            message: Mensagem do usuário
            
        Returns:
            bool: True se deve transferir
        """
        # Palavras-chave que indicam necessidade de atendimento humano
        human_keywords = [
            'humano', 'pessoa', 'atendente', 'operador', 'falar com alguém',
            'quero falar com alguém', 'atendimento humano', 'pessoa real',
            'falar com uma pessoa', 'quero uma pessoa', 'atendente real'
        ]
        
        message_lower = message.lower()
        
        # Verifica palavras-chave
        for keyword in human_keywords:
            if keyword in message_lower:
                return True
        
        # Verifica se é a terceira mensagem (pode indicar frustração)
        if chat_id in self.active_chats:
            if self.active_chats[chat_id]['message_count'] >= 3:
                # Verifica se a mensagem contém sinais de frustração
                frustration_words = ['não entendo', 'não funciona', 'problema', 'erro', 'bug']
                for word in frustration_words:
                    if word in message_lower:
                        return True
        
        return False 