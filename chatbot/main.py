from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
import logging
import argparse
import uvicorn
from handle_conversations import get_all_conversations
from services.service_manager import ServiceManager
from services.process_service import ProcessService
from services.human_service import HumanService
import uuid
import os
from dotenv import load_dotenv

# Disable logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('chatterbot').setLevel(logging.INFO)

# Carrega variáveis de ambiente
load_dotenv(override=True)

def create_and_train_bot(force_training=True):
    # Configuração do MongoDB
    mongo_host = os.getenv('MONGO_HOST', 'mongodb')
    mongo_port = os.getenv('MONGO_PORT', '27017')
    mongo_db = os.getenv('MONGO_DB', 'cnj-chatbot')
    logging.info(f"MongoDB host: {mongo_host}, port: {mongo_port}, db: {mongo_db}")

    # URL de conexão completa
    mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"

    # Configuração do MongoDB
    mongo_config = {
        'import_path': 'chatterbot.storage.MongoDatabaseAdapter',
        'database_uri': mongo_uri,
        'serverSelectionTimeoutMS': 5000,
        'connectTimeoutMS': 5000,
        'retryWrites': True,
        'retryReads': True,
        'w': 'majority',
        'readPreference': 'primary',
        'maxPoolSize': 10,
        'minPoolSize': 1
    }

    try:
        # Create a new chatbot
        chatbot = ChatBot(
            'CNJBot',
            storage_adapter=mongo_config,
            logic_adapters=[
                {
                    'import_path': 'chatterbot.logic.BestMatch',
                    'default_response': 'Desculpe, não entendi sua pergunta. Poderia reformular sua pergunta?',
                    'maximum_similarity_threshold': 0.95
                }
            ],
            read_only=False # Is this read only training?
        )

        # Verifica se precisa treinar
        if force_training:
            logging.info("Forçando treinamento do chatbot...")
            _train_chatbot(chatbot)
        else:
            # Verifica se já existem dados treinados
            statement_count = chatbot.storage.count()
            if statement_count < 100:  # Número arbitrário, ajuste conforme necessário
                logging.info(f"Poucos dados encontrados ({statement_count}). Iniciando treinamento...")
                _train_chatbot(chatbot)
            else:
                logging.info(f"Chatbot já treinado com {statement_count} exemplos. Pulando treinamento.")

        return chatbot
    except Exception as e:
        logging.error(f"Erro ao criar chatbot: {str(e)}")
        raise

def _train_chatbot(chatbot):
    """Função auxiliar para treinar o chatbot"""
    # Create trainers
    corpus_trainer = ChatterBotCorpusTrainer(chatbot)
    list_trainer = ListTrainer(chatbot)

    # Train with Portuguese corpus
    corpus_trainer.train("chatterbot.corpus.portuguese")

    # Get all conversations from our organized file
    legal_conversations = get_all_conversations()

    # Train with specific conversations
    list_trainer.train(legal_conversations)

def setup_services(chatbot: ChatBot) -> ServiceManager:
    """Configura e retorna o gerenciador de serviços"""
    service_manager = ServiceManager()
    
    # Registra os serviços disponíveis
    service_manager.register_service(ProcessService())
    service_manager.register_service(HumanService())
    
    # Aqui você pode registrar outros serviços
    # service_manager.register_service(CertificateService())
    # service_manager.register_service(DeadlineService())
    # etc...
    
    return service_manager

def run_cli():
    """Executa o chatbot no modo CLI"""
    print("Inicializando chatbot do Poder Judiciário...")
    chatbot = create_and_train_bot()
    service_manager = setup_services(chatbot)
    print("Chatbot está pronto! Digite 'sair' para encerrar.")
    print("Como eu posso ajudar você hoje?")
    
    # Gera um ID único para o usuário da CLI
    user_id = str(uuid.uuid4())
    
    while True:
        user_input = input("Você: ")
        if user_input.lower() == 'sair':
            print("Até logo! Obrigado por utilizar nossos serviços.")
            break
            
        try:
            # Primeiro, tenta processar com os serviços
            service_response, continue_service, status = service_manager.handle_message(user_id, user_input)
            
            if service_response:
                print(f"Bot: {service_response}")
                if not continue_service:
                    continue
            
            # Se nenhum serviço respondeu, usa o ChatterBot
            response = chatbot.get_response(user_input)
            print(f"Bot: {response}")
        except Exception as e:
            print(f"Bot: Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde.")

def run_api(host: str = "127.0.0.1", port: int = 8000):
    """Executa o chatbot no modo API"""
    uvicorn.run("api:app", host=host, port=port, reload=True)

def main():
    parser = argparse.ArgumentParser(description="Chatbot do CNJ")
    parser.add_argument(
        "--mode",
        choices=["cli", "api"],
        default="cli",
        help="Modo de execução: cli (interface de linha de comando) ou api (servidor web)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host para o servidor API (apenas no modo api)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta para o servidor API (apenas no modo api)"
    )
    parser.add_argument(
        "--cluster",
        choices=["local", "kubernetes"],
        default="local",
        help="Modo de execução: local (localhost) ou kubernetes (Kubernetes)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        run_cli()
    else:
        run_api(args.host, args.port)

if __name__ == "__main__":
    main()
