from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from main import create_and_train_bot, setup_services
from adapters.whatsapp_adapter import WhatsAppAdapter
from adapters.telegram_adapter import TelegramAdapter
from adapters.feedback_adapter import FeedbackAdapter
from datetime import datetime, timedelta
import time
import logging

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

# Inicializa o chatbot, o gerenciador de serviços e os adaptadores
chatbot = create_and_train_bot()
service_manager = setup_services(chatbot)
whatsapp = WhatsAppAdapter()
telegram = TelegramAdapter()
feedback_adapter = FeedbackAdapter()

# Cache para controle de rate limiting
feedback_cache = {}

logging.info("Chatbot inicializado com sucesso")

def check_rate_limit(user_id: str, response_id: str) -> bool:
    """
    Verifica se o usuário já enviou feedback para esta resposta nos últimos 5 minutos
    """
    cache_key = f"{user_id}:{response_id}"
    if cache_key in feedback_cache:
        last_feedback_time = feedback_cache[cache_key]
        if datetime.now() - last_feedback_time < timedelta(minutes=5):
            return False
    return True

def update_rate_limit(user_id: str, response_id: str):
    """
    Atualiza o cache de rate limiting
    """
    cache_key = f"{user_id}:{response_id}"
    feedback_cache[cache_key] = datetime.now()

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

class FeedbackRequest(BaseModel):
    question_id: str
    response_id: str
    rating: int
    user_id: Optional[str] = None
    comments: Optional[str] = None

class FeedbackResponse(BaseModel):
    success: bool
    message: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint para enviar mensagens ao chatbot e receber respostas
    """
    try:
        # Gera um ID de usuário se não foi fornecido
        user_id = request.user_id or "default_user"
        
        # Primeiro, tenta processar com os serviços
        service_response, continue_service = service_manager.handle_message(user_id, request.message)
        
        if service_response:
            return ChatResponse(
                response=service_response,
                confidence=1.0 if not continue_service else 0.8,
                response_id="service_response",
                question_id="unknown_question"
            )
        
        # Se nenhum serviço respondeu, usa o ChatterBot
        response = chatbot.get_response(request.message)
        
        # Obtém o ID da pergunta (statement da pergunta do usuário)
        question_statements = list(chatbot.storage.filter(text=request.message))
        question_id = str(question_statements[0].id) if question_statements else "unknown_question"
        
        # Obtém o ID da resposta
        response_statements = list(chatbot.storage.filter(text=str(response)))
        response_id = str(response_statements[0].id) if response_statements else "unknown_response"
            
        return ChatResponse(
            response=str(response),
            confidence=float(response.confidence),
            response_id=response_id,
            question_id=question_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(request: FeedbackRequest):
    """
    Endpoint para registrar feedback do usuário
    """
    try:
        # Gera um ID de usuário se não foi fornecido
        user_id = request.user_id or "default_user"
        
        # Verifica rate limiting
        if not check_rate_limit(user_id, request.response_id):
            raise HTTPException(
                status_code=429,
                detail="Você já enviou feedback para esta resposta recentemente. Tente novamente em alguns minutos."
            )
        
        # Registra o feedback
        feedback_adapter.record_feedback(
            question_id=request.question_id,
            response_id=request.response_id,
            rating=request.rating,
            user_id=user_id,
            comments=request.comments
        )
        
        # Atualiza o cache de rate limiting
        update_rate_limit(user_id, request.response_id)
        
        return FeedbackResponse(
            success=True,
            message="Feedback registrado com sucesso"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feedback/stats")
async def feedback_stats():
    """
    Endpoint para obter estatísticas de feedback
    """
    try:
        return feedback_adapter.get_feedback_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint para receber webhooks do WhatsApp
    """
    try:
        data = await request.json()
        
        # Processa o webhook do WhatsApp
        result = whatsapp.handle_webhook(data)
        if not result:
            return {"status": "ignored"}
            
        # Extrai o número e a mensagem
        phone, message = result
        
        # Processa a mensagem com o chatbot
        service_response, continue_service = service_manager.handle_message(phone, message)
        
        if service_response:
            # Envia a resposta via WhatsApp
            whatsapp.send_message(phone, service_response)
        else:
            # Se nenhum serviço respondeu, usa o ChatterBot
            response = chatbot.get_response(message)
            whatsapp.send_message(phone, str(response))
            
        return {"status": "success"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar se a API está funcionando
    """
    return {"status": "healthy"} 