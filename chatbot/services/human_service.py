from typing import Tuple, Dict, List
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from .base_service import BaseService
from .jitsi_service import JitsiService

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
            'quero falar com uma pessoa'
        ]
        
        # Carrega dados dos tribunais
        self.tribunals = self._load_tribunals()
        
    def _load_tribunals(self) -> Dict:
        """Carrega dados dos tribunais dos arquivos JSON"""
        tribunals = {}
        config_dir = Path("config/tribunals")
        
        if not config_dir.exists():
            print(f"Diretório de configuração não encontrado: {config_dir}")
            return tribunals
            
        for json_file in config_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    tribunal_data = json.load(f)
                    tribunals[tribunal_data['code']] = tribunal_data
            except Exception as e:
                print(f"Erro ao carregar arquivo {json_file}: {str(e)}")
                
        return tribunals
    
    def _get_tribunal_from_text(self, text: str) -> Tuple[str, str]:
        """
        Identifica qual tribunal e unidade foram mencionados no texto
        Returns: (tribunal_code, unit_code) ou ("", "") se não encontrado
        """
        text = text.lower()
        
        for tribunal_code, tribunal_data in self.tribunals.items():
            # Verifica palavras-chave do tribunal
            if any(keyword in text for keyword in tribunal_data['keywords'].get(tribunal_code, [])):
                # Verifica palavras-chave das unidades
                for unit_code, keywords in tribunal_data['keywords'].items():
                    if unit_code != tribunal_code and any(keyword in text for keyword in keywords):
                        return tribunal_code, unit_code
                return tribunal_code, ""
                
        return "", ""
    
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
        
        # Se já está esperando confirmação de tribunal
        if state.get("waiting_for_tribunal"):
            tribunal_code, unit_code = self._get_tribunal_from_text(text)
            if tribunal_code:
                state["tribunal_code"] = tribunal_code
                state["unit_code"] = unit_code
                state["waiting_for_tribunal"] = False
                state["waiting_for_confirmation"] = True
                
                tribunal_data = self.tribunals[tribunal_code]
                unit_data = tribunal_data['units'].get(unit_code, {})
                
                return (
                    f"Entendi que você quer falar com um atendente da {unit_data.get('name', tribunal_data['name'])}.\n"
                    f"Horário de atendimento: {unit_data.get('schedule', 'Não especificado')}\n\n"
                    "Antes de transferir, gostaria de confirmar: você realmente precisa falar com um atendente? "
                    "Posso tentar te ajudar primeiro.",
                    True
                )
            else:
                # Lista tribunais disponíveis
                tribunals_list = "\n".join([f"- {data['name']}" for data in self.tribunals.values()])
                return (
                    "Desculpe, não identifiquei qual tribunal você deseja. "
                    "Por favor, escolha um dos seguintes tribunais:\n"
                    f"{tribunals_list}",
                    True
                )
        
        # Se já está esperando confirmação
        if state.get("waiting_for_confirmation"):
            if self._is_affirmative(text):
                try:
                    # Criar sala no Jitsi
                    tribunal_data = self.tribunals[state["tribunal_code"]]
                    unit_data = tribunal_data['units'].get(state["unit_code"], {})
                    subject = f"Atendimento {unit_data.get('name', tribunal_data['name'])}"
                    
                    # meeting = self.jitsi_service.create_meeting_room(
                    #     user_id=user_id,
                    #     subject=subject
                    # )
                    
                    # Limpar estado
                    self.clear_user_state(user_id)
                    
                    return (
                        f"Entendi! Vou conectar você a um atendente da {unit_data.get('name', tribunal_data['name'])}. "
                        # f"Por favor, acesse o link: {meeting['room_url']}\n"
                        f"Por favor, acesse o link: https://reuniao.com/saz-keci-icq\n"
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
            # Verifica se mencionou algum tribunal específico
            tribunal_code, unit_code = self._get_tribunal_from_text(text)
            if tribunal_code:
                state["tribunal_code"] = tribunal_code
                state["unit_code"] = unit_code
                state["waiting_for_confirmation"] = True
                
                tribunal_data = self.tribunals[tribunal_code]
                unit_data = tribunal_data['units'].get(unit_code, {})
                
                return (
                    f"Entendi que você quer falar com um atendente da {unit_data.get('name', tribunal_data['name'])}.\n"
                    f"Horário de atendimento: {unit_data.get('schedule', 'Não especificado')}\n\n"
                    "Antes de transferir, gostaria de confirmar: você realmente precisa falar com um atendente? "
                    "Posso tentar te ajudar primeiro.",
                    True
                )
            else:
                state["waiting_for_tribunal"] = True
                # Lista tribunais disponíveis
                tribunals_list = "\n".join([f"- {data['name']}" for data in self.tribunals.values()])
                return (
                    "Entendi que você gostaria de falar com um atendente humano. "
                    "Por favor, qual tribunal você deseja falar?:\n",
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
        return any(state.get("waiting_for_confirmation", False) or state.get("waiting_for_tribunal", False)
                  for state in self.conversation_state.values()) 