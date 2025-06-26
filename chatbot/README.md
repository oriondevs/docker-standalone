# Chatbot do Poder Judiciário

Um chatbot especializado em fornecer informações sobre os sistemas do CNJ (Conselho Nacional de Justiça) e processos judiciais, implementado usando a biblioteca ChatterBot.

## Estrutura do Projeto

```
.
├── conversations/
│   └── csv/
│       ├── processos.csv     # Conversas sobre processos
│       ├── certidoes.csv     # Conversas sobre certidões
│       ├── prazos.csv        # Conversas sobre prazos
│       ├── sistemas.csv      # Conversas sobre sistemas do CNJ
│       └── geral.csv         # Conversas gerais
├── main.py                   # Arquivo principal do chatbot
├── api.py                    # API REST do chatbot
├── handle_conversations.py   # Gerenciador de conversas
├── pyproject.toml           # Configuração do projeto e dependências
└── README.md                # Este arquivo
```

## Requisitos

- Python 3.12 ou superior
- MongoDB 4.4 ou superior
- Redis (para controle de polling do Telegram)
- Navegador web atualizado

## Configuração

1. Clone o repositório:
   ```bash
   git clone [URL_DO_REPOSITÓRIO]
   cd [NOME_DO_DIRETÓRIO]
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -e .
   ```

4. Configure o MongoDB:
   ```bash
   # Usando Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest

   # Ou instale localmente seguindo as instruções em:
   # https://www.mongodb.com/docs/manual/installation/
   ```

5. Configure as variáveis de ambiente:
   Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   TELEGRAM_API_URL=https://api.telegram.org/bot
   TELEGRAM_BOT_TOKEN=seu_token_aqui
   
   MONGO_HOST=localhost
   MONGO_PORT=27017
   MONGO_DB=cnj-chatbot
   
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=password
   
   # Configuração de timeout de sessão (em minutos)
   SESSION_TIMEOUT_MINUTES=15
   ```

6. Baixe os modelos necessários do spaCy:
   ```bash
   # Modelo
   python -m spacy download en-core-web-sm
   ```

## Uso

### Modo CLI
1. Execute o chatbot no modo CLI:
   ```bash
   python main.py --mode cli
   ```

2. O chatbot irá inicializar e treinar-se usando as conversas dos arquivos CSV.

3. Digite 'sair' para encerrar a conversa.

### Modo API
1. Execute o chatbot no modo API:
   ```bash
   python main.py --mode api --host 0.0.0.0 --port 8000
   ```

2. A API estará disponível em `http://localhost:8000`

3. Acesse a documentação automática em `http://localhost:8000/docs`

## API REST

### Endpoint `/chat`

**POST** `/chat`

Envia uma mensagem ao chatbot e recebe uma resposta.

**Request Body:**
```json
{
  "message": "Olá, como posso consultar um processo?",
  "user_id": "user123"  // opcional
}
```

**Response:**
```json
{
  "response": "Para consultar um processo, você precisa informar o número do processo no formato CNJ.",
  "confidence": 0.95,
  "response_id": "response_123",
  "question_id": "question_456",
  "status": 200,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Códigos de Status

O campo `status` na resposta indica o tipo de resposta:

- **200**: Resposta normal do chatbot
- **204**: Conversa finalizada pelo bot (timeout de inatividade ou comando de saída)
- **205**: Transferência para atendente humano

#### Session ID

O campo `session_id` contém um UUID único que identifica a sessão de conversa do usuário. O mesmo `session_id` será retornado para todas as mensagens do mesmo `user_id` durante a sessão.

#### Timeout de Sessão

O sistema possui um mecanismo de timeout que encerra automaticamente a sessão após um período de inatividade. Por padrão, o timeout é de 15 minutos, mas pode ser configurado através da variável de ambiente `SESSION_TIMEOUT_MINUTES`.

Quando uma sessão expira por timeout:
- O status retornado é **204** (conversa finalizada)
- A sessão é limpa automaticamente
- O usuário precisa enviar uma nova mensagem para iniciar uma nova sessão

### Endpoint `/health`

**GET** `/health`

Verifica se a API está funcionando.

**Response:**
```json
{
  "status": "healthy"
}
```

## Estrutura de Conversas

O projeto utiliza arquivos CSV para armazenar as conversas. Cada arquivo CSV deve seguir o seguinte formato:

```csv
pergunta,resposta
Como posso acessar o processo?,Para acessar o processo, você precisa informar o número do processo ou o CPF/CNPJ.
Qual é o status do processo?,Para verificar o status do processo, preciso do número do processo.
```

### Arquivos CSV Disponíveis

- `processos.csv`: Conversas sobre processos judiciais
- `certidoes.csv`: Conversas sobre certidões
- `prazos.csv`: Conversas sobre prazos processuais
- `sistemas.csv`: Conversas sobre sistemas do CNJ
- `geral.csv`: Conversas gerais

### Como Adicionar Novas Conversas

1. Crie ou edite um arquivo CSV na pasta `conversations/csv/`
2. Adicione as conversas no formato:
   ```csv
   pergunta,resposta
   Sua pergunta?,Sua resposta.
   ```
3. Certifique-se de que o arquivo tem o cabeçalho correto (pergunta,resposta)
4. Use codificação UTF-8 para suportar caracteres especiais

## Dependências Principais

- chatterbot: Framework do chatbot
- spacy: Processamento de linguagem natural
- pytz: Manipulação de fusos horários
- pymongo: Driver MongoDB
- fastapi: Framework web para API
- uvicorn: Servidor ASGI
- python-dotenv: Gerenciamento de variáveis de ambiente
- redis: Cache e controle de polling

## Desenvolvimento Local

Para testar a aplicação localmente com o Jitsi Meet, você pode usar o Docker Compose:

1. Certifique-se de ter o Docker e o Docker Compose instalados
2. Execute o ambiente de desenvolvimento:
```bash
docker-compose up --build
```

Isso irá iniciar:
- O chatbot na porta 8000
- MongoDB na porta 27017
- Redis na porta 6379
- Jitsi Meet na porta 8443 (https://localhost:8443)

Para testar o chatbot com a integração do Jitsi:
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Quero falar com um atendente humano"}'
```

Observações:
- O Jitsi Meet estará disponível em https://localhost:8443
- As configurações do Jitsi estão em modo de desenvolvimento (sem autenticação)
- Os dados do MongoDB são persistidos em um volume Docker
- Para parar o ambiente: `docker-compose down`