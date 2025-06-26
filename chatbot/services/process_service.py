import re
from typing import Tuple
from .base_service import BaseService

class ProcessService(BaseService):
    """Serviço para consulta de processos judiciais"""
    
    def __init__(self):
        super().__init__()
        # Padrão para identificar números de processos no formato CNJ
        self.process_pattern = r'\d{20}'
        # Palavras-chave para identificar consultas de processo
        self.keywords = [
            'consultar processo',
            'processo número',
            'processo n°',
            'processo nº',
            'processo numero',
            'processo',
            'consulta processo'
        ]
        # Comandos para cancelar a consulta
        self.cancel_commands = [
            'cancelar',
            'sair',
            'não quero mais',
            'não quero',
            'quero sair',
            'sair da consulta',
            'cancelar consulta'
        ]
    
    def can_handle(self, text: str) -> bool:
        """Verifica se o texto é uma consulta de processo"""
        # Verifica se está em uma conversa de processo
        if self._is_in_process_conversation():
            return True
        # Verifica se contém palavras-chave de processo
        return any(keyword in text.lower() for keyword in self.keywords)
    
    def handle(self, user_id: str, text: str) -> Tuple[str, bool, int]:
        """Processa a consulta de processo"""
        state = self.get_user_state(user_id)
        
        # Se já está esperando o número do processo
        if state.get("waiting_for_process"):
            # Verifica se é um comando de cancelamento
            if self._is_cancel_command(text):
                self.clear_user_state(user_id)
                return "Consulta de processo cancelada. Como posso ajudar?", False, 200
                
            process_number = self._extract_process_number(text)
            if process_number and self._validate_process_number(process_number):
                # Limpa o estado da conversa
                self.clear_user_state(user_id)
                # Simula a consulta do processo
                process_info = self._get_process_info(process_number)
                return (
                    f"Processo encontrado!\n"
                    f"Número: {process_info['numero']}\n"
                    f"Classe: {process_info['classe']}\n"
                    f"Assunto: {process_info['assunto']}\n"
                    f"Status: {process_info['status']}\n"
                    f"Última movimentação: {process_info['ultima_movimentacao']}\n"
                    f"Tribunal: {process_info['tribunal']}",
                    False,
                    200
                )
            else:
                return (
                    "Desculpe, não consegui identificar um número de processo válido. "
                    "Por favor, informe o número do processo no formato: 0000000-00.0000.0.00.0000\n"
                    "Ou digite 'cancelar' ou 'sair' para sair da consulta.",
                    True,
                    200
                )
        
        # Se é uma nova consulta de processo
        if self._is_process_query(text):
            state["waiting_for_process"] = True
            return "Por favor, informe o número do processo que deseja consultar. Digite 'cancelar' ou 'sair' para sair da consulta.", True, 200
        
        return "", False, 200
    
    def _is_process_query(self, text: str) -> bool:
        """Verifica se o texto é uma consulta de processo"""
        return any(keyword in text.lower() for keyword in self.keywords)
    
    def _extract_process_number(self, text: str) -> str:
        """Extrai o número do processo do texto"""
        match = re.search(self.process_pattern, text)
        return match.group(0) if match else None
    
    def _validate_process_number(self, process_number: str) -> bool:
        """Valida se o número do processo está no formato correto"""
        if not process_number:
            return False
        # Verifica se tem 20 dígitos
        if not re.match(r'^\d{20}$', process_number):
            return False
        # Aqui você pode adicionar mais validações específicas do CNJ
        return True
    
    def _get_process_info(self, process_number: str) -> dict:
        """
        Simula a consulta de um processo.
        Em um cenário real, aqui você faria a integração com a API do CNJ
        """
        # Simulação de resposta
        return {
            "numero": process_number,
            "classe": "Procedimento Comum",
            "assunto": "Direito Civil",
            "status": "Em andamento",
            "ultima_movimentacao": "2024-03-20",
            "tribunal": "TJSP"
        }
    
    def _is_in_process_conversation(self) -> bool:
        """Verifica se está em uma conversa de processo"""
        return any(state.get("waiting_for_process", False) 
                  for state in self.conversation_state.values())
    
    def _is_cancel_command(self, text: str) -> bool:
        """Verifica se o texto é um comando de cancelamento"""
        return any(command in text.lower() for command in self.cancel_commands) 