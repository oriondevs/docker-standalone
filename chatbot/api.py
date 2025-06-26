from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from main import create_and_train_bot, setup_services
from adapters.telegram_adapter import TelegramAdapter
import logging
import uuid

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

# Cache para armazenar session_ids por user_id
session_cache = {}

logging.info("Chatbot inicializado com sucesso")

# Função para processar mensagens do Telegram
def handle_telegram_message(chat_id: str, message: str):
    # Processa a mensagem com o chatbot
    service_response, continue_service = service_manager.handle_message(chat_id, message)
    
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
    return session_cache[user_id]

def determine_response_status(response_text: str, response_id: str = "") -> int:
    """
    Determina o status da resposta baseado no conteúdo e ID da resposta
    
    Returns:
        - 200: Resposta normal do chatbot
        - 204: Conversa finalizada pelo bot
        - 205: Transferência para atendente humano
    """
    response_lower = response_text.lower()
    
    # Verifica se é transferência para atendente humano
    human_transfer_keywords = [
        "conectar você a um atendente",
        "acesse o link",
        "sala de atendimento",
        "atendente entrará na sala",
        "reuniao.com"
    ]
    
    if any(keyword in response_lower for keyword in human_transfer_keywords) or response_id == "human_transfer":
        return 205
    
    # Verifica se é finalização da conversa
    end_conversation_keywords = [
        "até logo",
        "obrigado por utilizar",
        "tchau",
        "até a próxima",
        "encerrando",
        "finalizando"
    ]
    
    if any(keyword in response_lower for keyword in end_conversation_keywords) or response_id == "conversation_end":
        return 204
    
    # Resposta normal
    return 200

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint para enviar mensagens ao chatbot e receber respostas
    
    Status codes:
    - 200: Resposta normal do chatbot
    - 204: Conversa finalizada pelo bot
    - 205: Transferência para atendente humano
    """
    try:
        # Gera um ID de usuário se não foi fornecido
        user_id = request.user_id or "default_user"
        
        # Obtém ou cria o session_id para o usuário
        session_id = get_or_create_session_id(user_id)
        
        # Primeiro, tenta processar com os serviços
        service_response, continue_service = service_manager.handle_message(user_id, request.message)
        
        if service_response:
            # Determina o status baseado na resposta do serviço
            status = determine_response_status(service_response)
            
            # Define o response_id baseado no status
            if status == 205:
                response_id = "human_transfer"
                question_id = "human_transfer_request"
            elif status == 204:
                response_id = "conversation_end"
                question_id = "conversation_end"
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
        status = determine_response_status(str(response), response_id)
            
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