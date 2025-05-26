from typing import Tuple

from dotenv import load_dotenv
from .base_service import BaseService
from .jitsi_service import JitsiService
import os

# Carrega variáveis de ambiente
load_dotenv(override=True)

class HumanService(BaseService):
    """Serviço para transferência para atendente humano"""
    
    def __init__(self):
        super().__init__()
        # Inicializa o serviço do Jitsi
        self.jitsi_service = JitsiService(
            domain=os.getenv("JITSI_DOMAIN", "meet.jus.br"),
            api_key=os.getenv("JITSI_API_KEY")
        )
        # Palavras-chave para identificar solicitações de atendente humano
        self.keywords = [
            'falar com atendente',
            'falar com humano',
            'atendente humano',
            'atendente real',
            'pessoa real',
            'transferir para atendente',
            'quero falar com alguém',
            'preciso de ajuda humana',
            'não estou conseguindo',
            'não entendi',
            'quero falar com uma pessoa',
            'quero falar com uma humano'
        ]
    
    def can_handle(self, text: str) -> bool:
        """Verifica se o texto é uma solicitação de atendente humano"""
        # Verifica se está em uma conversa de transferência
        if self._is_in_transfer_conversation():
            return True
        # Verifica se contém palavras-chave de transferência
        return any(keyword in text.lower() for keyword in self.keywords)
    
    def handle(self, user_id: str, text: str) -> Tuple[str, bool]:
        """Processa a solicitação de atendente humano"""
        state = self.get_user_state(user_id)
        
        # Se já está esperando confirmação
        if state.get("waiting_for_confirmation"):
            if self._is_affirmative(text):
                try:
                    # Criar sala no Jitsi
                    meeting = self.jitsi_service.create_meeting_room(
                        user_id=user_id,
                        subject=state.get("subject", "Atendimento CNJ")
                    )
                    
                    # Limpar estado
                    self.clear_user_state(user_id)
                    
                    return (
                        f"Entendi! Vou conectar você a um atendente. "
                        f"Por favor, acesse o link: {meeting['room_url']}\n"
                        f"Um atendente entrará na sala em instantes.\n\n"
                        f"Dicas:\n"
                        f"- Use fones de ouvido para melhor qualidade de áudio\n"
                        f"- Verifique se sua câmera e microfone estão funcionando\n"
                        f"- Aguarde o atendente entrar na sala",
                        True
                    )
                except Exception as e:
                    return (
                        f"Desculpe, tivemos um problema ao criar a sala de atendimento. "
                        f"Por favor, tente novamente em alguns minutos.",
                        False
                    )
            elif self._is_negative(text):
                # Limpa o estado da conversa
                self.clear_user_state(user_id)
                return (
                    "Ok, vou continuar te ajudando. Como posso ser útil?",
                    False
                )
            else:
                return (
                    "Desculpe, não entendi. Você gostaria de falar com um atendente humano? "
                    "Por favor, responda com 'sim' ou 'não'.",
                    True
                )
        
        # Se é uma nova solicitação de atendente
        if self._is_transfer_request(text):
            state["waiting_for_confirmation"] = True
            state["subject"] = text  # Guarda o assunto para usar na criação da sala
            return (
                "Entendi que você gostaria de falar com um atendente humano. "
                "Antes de transferir, gostaria de confirmar: você realmente precisa falar com um atendente? "
                "Posso tentar te ajudar primeiro.",
                True
            )
        
        return "", False
    
    def _is_transfer_request(self, text: str) -> bool:
        """Verifica se o texto é uma solicitação de transferência"""
        return any(keyword in text.lower() for keyword in self.keywords)
    
    def _is_affirmative(self, text: str) -> bool:
        """Verifica se a resposta é afirmativa"""
        affirmatives = ['sim', 's', 'yes', 'y', 'claro', 'por favor', 'quero']
        return text.lower() in affirmatives
    
    def _is_negative(self, text: str) -> bool:
        """Verifica se a resposta é negativa"""
        negatives = ['não', 'nao', 'n', 'no', 'não quero', 'nao quero']
        return text.lower() in negatives
    
    def _is_in_transfer_conversation(self) -> bool:
        """Verifica se está em uma conversa de transferência"""
        return any(state.get("waiting_for_confirmation", False) 
                  for state in self.conversation_state.values()) 