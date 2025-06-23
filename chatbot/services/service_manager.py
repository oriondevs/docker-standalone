from typing import List, Tuple
from .base_service import BaseService

class ServiceManager:
    """Gerencia todos os serviços disponíveis no chatbot"""
    
    def __init__(self):
        self.services: List[BaseService] = []
        self.lhc_service = None  # Serviço LHC será configurado separadamente
    
    def register_service(self, service: BaseService):
        """Registra um novo serviço"""
        self.services.append(service)
    
    def register_lhc_service(self, lhc_service):
        """Registra o serviço LHC separadamente"""
        self.lhc_service = lhc_service
    
    def handle_message(self, user_id: str, text: str) -> Tuple[str, bool]:
        """
        Processa a mensagem através de todos os serviços registrados
        Retorna a primeira resposta não vazia ou uma resposta vazia se nenhum serviço puder lidar
        """
        for service in self.services:
            if service.can_handle(text):
                response, continue_conversation = service.handle(user_id, text)
                if response:
                    return response, continue_conversation
        
        return "", False
    
    def handle_lhc_webhook(self, data: dict) -> bool:
        """
        Processa webhooks do LHC
        
        Args:
            data: Dados do webhook
            
        Returns:
            bool: True se processado com sucesso
        """
        if self.lhc_service:
            return self.lhc_service.handle_webhook(data)
        return False
    
    def get_lhc_service(self):
        """Retorna o serviço LHC"""
        return self.lhc_service 