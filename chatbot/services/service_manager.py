from typing import List, Tuple
from .base_service import BaseService

class ServiceManager:
    """Gerencia todos os serviços disponíveis no chatbot"""
    
    def __init__(self):
        self.services: List[BaseService] = []
    
    def register_service(self, service: BaseService):
        """Registra um novo serviço"""
        self.services.append(service)
        
    def handle_message(self, user_id: str, text: str) -> Tuple[str, bool, int]:
        """
        Processa a mensagem através de todos os serviços registrados
        Retorna a primeira resposta não vazia ou uma resposta vazia se nenhum serviço puder lidar
        """
        for service in self.services:
            if service.can_handle(text):
                response, continue_conversation, status = service.handle(user_id, text)
                if response:
                    return response, continue_conversation, status
        
        return "", False, 200