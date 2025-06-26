from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from main import create_and_train_bot, setup_services
from adapters.telegram_adapter import TelegramAdapter
import logging
import uuid
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv(override=True)

app = FastAPI(
    title="CNJ Chatbot API",
    description="API para interagir com o chatbot do CNJ",
    version="1.0.0"
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #TODO : Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o chatbot, o gerenciador de serviços e o adaptador do Telegram
chatbot = create_and_train_bot()
service_manager = setup_services(chatbot)
telegram = TelegramAdapter()

# Cache para armazenar session_ids e timestamps por user_id
session_cache = {}
session_timestamps = {}

# Configuração do timeout (em minutos)
SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '15'))

logging.info(f"Chatbot inicializado com timeout de sessão: {SESSION_TIMEOUT_MINUTES} minutos")

# Função para processar mensagens do Telegram
def handle_telegram_message(chat_id: str, message: str):
    # Processa a mensagem com o chatbot
    service_response, continue_service, status = service_manager.handle_message(chat_id, message)
    
    if service_response:
        # Envia a resposta via Telegram
        telegram.send_message(chat_id, service_response)
    else:
        # Se nenhum serviço respondeu, usa o ChatterBot
        response = chatbot.get_response(message)
        telegram.send_message(chat_id, str(response))

# Inicia o polling do Telegram
telegram.start_polling(handle_telegram_message)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: float
    response_id: str
    question_id: str
    status: int
    session_id: str

def get_or_create_session_id(user_id: str) -> str:
    """
    Obtém ou cria um session_id para o user_id
    """
    if user_id not in session_cache:
        session_cache[user_id] = str(uuid.uuid4())
        session_timestamps[user_id] = datetime.now()
    else:
        # Atualiza o timestamp da sessão
        session_timestamps[user_id] = datetime.now()
    return session_cache[user_id]

def check_session_timeout(user_id: str) -> bool:
    """
    Verifica se a sessão do usuário expirou por timeout
    """
    if user_id not in session_timestamps:
        return False
    
    last_activity = session_timestamps[user_id]
    timeout_threshold = datetime.now() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    return last_activity < timeout_threshold

def clear_session(user_id: str):
    """
    Limpa a sessão do usuário
    """
    if user_id in session_cache:
        del session_cache[user_id]
    if user_id in session_timestamps:
        del session_timestamps[user_id]

def determine_chatterbot_status(response_text: str) -> int:
    """
    Determina o status para respostas do ChatterBot
    """
    response_lower = response_text.lower()
    
    # Verifica se é finalização da conversa
    end_conversation_keywords = [
        "até logo",
        "obrigado por utilizar",
        "tchau",
        "até a próxima",
        "encerrando",
        "finalizando"
    ]
    
    if any(keyword in response_lower for keyword in end_conversation_keywords):
        return 204
    
    # Resposta normal
    return 200

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint para enviar mensagens ao chatbot e receber respostas
    
    Status codes:
    - 200: Resposta normal do chatbot
    - 204: Conversa finalizada pelo bot (timeout ou comando de saída)
    - 205: Transferência para atendente humano
    """
    try:
        # Gera um ID de usuário se não foi fornecido
        user_id = request.user_id or "default_user"
        
        # Verifica se a sessão expirou por timeout
        if check_session_timeout(user_id):
            # Limpa a sessão expirada
            clear_session(user_id)
            return ChatResponse(
                response="Sua sessão expirou por inatividade. Para continuar, envie uma nova mensagem.",
                confidence=1.0,
                response_id="session_timeout",
                question_id="session_timeout",
                status=204,  # Conversa finalizada por timeout
                session_id=""
            )
        
        # Obtém ou cria o session_id para o usuário
        session_id = get_or_create_session_id(user_id)
        
        # Primeiro, tenta processar com os serviços
        service_response, continue_service, status = service_manager.handle_message(user_id, request.message)
        
        if service_response:
            # Define o response_id baseado no status
            if status == 205:
                response_id = "human_transfer"
                question_id = "human_transfer_request"
            elif status == 204:
                response_id = "conversation_end"
                question_id = "conversation_end"
                # Limpa a sessão quando a conversa é finalizada
                clear_session(user_id)
            else:
                response_id = "service_response"
                question_id = "unknown_question"
            
            return ChatResponse(
                response=service_response,
                confidence=1.0 if not continue_service else 0.8,
                response_id=response_id,
                question_id=question_id,
                status=status,
                session_id=session_id
            )
        
        # Se nenhum serviço respondeu, usa o ChatterBot
        response = chatbot.get_response(request.message)
        
        # Obtém o ID da pergunta (statement da pergunta do usuário)
        question_statements = list(chatbot.storage.filter(text=request.message))
        question_id = str(question_statements[0].id) if question_statements else "unknown_question"
        
        # Obtém o ID da resposta
        response_statements = list(chatbot.storage.filter(text=str(response)))
        response_id = str(response_statements[0].id) if response_statements else "unknown_response"
        
        # Determina o status baseado na resposta do ChatterBot
        status = determine_chatterbot_status(str(response))
        
        # Se a conversa foi finalizada, limpa a sessão
        if status == 204:
            clear_session(user_id)
            
        return ChatResponse(
            response=str(response),
            confidence=float(response.confidence),
            response_id=response_id,
            question_id=question_id,
            status=status,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar se a API está funcionando
    """
    return {"status": "healthy"} 