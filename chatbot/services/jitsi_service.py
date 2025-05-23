import secrets
import datetime
import logging
from typing import Dict, Optional
import requests
from urllib.parse import urljoin

class JitsiService:
    """Serviço para integração com o Jitsi Meet"""
    
    def __init__(self, domain: str = "meet.jus.br", api_key: Optional[str] = None):
        self.domain = domain
        self.api_key = api_key
        self.base_url = f"https://{domain}"
        self.logger = logging.getLogger(__name__)
        
    def create_meeting_room(self, user_id: str, subject: str) -> Dict[str, str]:
        """
        Cria uma nova sala de reunião no Jitsi Meet
        
        Args:
            user_id: ID do usuário
            subject: Assunto da reunião
            
        Returns:
            Dict com informações da sala criada
        """
        try:
            # Gerar nome único para a sala
            room_name = f"atendimento-{user_id}-{secrets.token_hex(4)}"
            
            # Configurar a sala
            room_config = {
                "room_name": room_name,
                "subject": subject,
                "start_time": datetime.datetime.now().isoformat(),
                "duration": 30,  # minutos
                "max_participants": 2,  # usuário e atendente
                "settings": {
                    "start_with_audio_muted": True,
                    "start_with_video_muted": True,
                    "enable_chat": True,
                    "enable_recording": False
                }
            }
            
            # Criar a sala via API do Jitsi
            response = requests.post(
                urljoin(self.base_url, "/api/v1/meetings"),
                json=room_config,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            response.raise_for_status()
            
            meeting_data = response.json()
            
            return {
                "room_url": f"{self.base_url}/{room_name}",
                "room_name": room_name,
                "moderator_token": meeting_data.get("moderator_token"),
                "meeting_id": meeting_data.get("meeting_id")
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao criar sala no Jitsi: {str(e)}")
            raise Exception("Não foi possível criar a sala de atendimento. Por favor, tente novamente mais tarde.")
    
    def get_meeting_info(self, meeting_id: str) -> Dict:
        """
        Obtém informações sobre uma reunião específica
        
        Args:
            meeting_id: ID da reunião
            
        Returns:
            Dict com informações da reunião
        """
        try:
            response = requests.get(
                urljoin(self.base_url, f"/api/v1/meetings/{meeting_id}"),
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao obter informações da reunião: {str(e)}")
            raise Exception("Não foi possível obter informações da reunião.")
    
    def end_meeting(self, meeting_id: str) -> bool:
        """
        Encerra uma reunião específica
        
        Args:
            meeting_id: ID da reunião
            
        Returns:
            bool indicando sucesso da operação
        """
        try:
            response = requests.post(
                urljoin(self.base_url, f"/api/v1/meetings/{meeting_id}/end"),
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao encerrar reunião: {str(e)}")
            return False 