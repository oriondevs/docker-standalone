from abc import ABC, abstractmethod
from typing import Tuple, Optional

class BaseService(ABC):
    """Classe base para todos os serviços do chatbot"""
    
    def __init__(self):
        self.conversation_state = {}
    
    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """
        Verifica se este serviço pode lidar com a mensagem
        """
        pass
    
    @abstractmethod
    def handle(self, user_id: str, text: str) -> Tuple[str, bool]:
        """
        Processa a mensagem e retorna (resposta, se_continua_conversa)
        """
        pass
    
    def get_user_state(self, user_id: str) -> dict:
        """Obtém o estado da conversa do usuário"""
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {}
        return self.conversation_state[user_id]
    
    def clear_user_state(self, user_id: str):
        """Limpa o estado da conversa do usuário"""
        if user_id in self.conversation_state:
            del self.conversation_state[user_id] 