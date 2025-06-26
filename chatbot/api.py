from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from main import create_and_train_bot, setup_services
from adapters.telegram_adapter import TelegramAdapter
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

# Inicializa o chatbot, o gerenciador de serviços e o adaptador do Telegram
chatbot = create_and_train_bot()
service_manager = setup_services(chatbot)
telegram = TelegramAdapter()

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

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar se a API está funcionando
    """
    return {"status": "healthy"} 