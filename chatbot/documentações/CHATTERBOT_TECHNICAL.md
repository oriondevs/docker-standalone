# Documentação Técnica do ChatterBot

## 1. Visão Geral
O ChatterBot é um framework de chatbot em Python que utiliza processamento de linguagem natural (NLP) para gerar respostas automáticas. Ele é projetado para aprender com exemplos de conversas e melhorar suas respostas ao longo do tempo.

## 2. Arquitetura Técnica

### 2.1 Componentes Principais
- **Storage Adapter**: Gerencia o armazenamento e recuperação de dados
- **Logic Adapter**: Processa a entrada e gera respostas
- **Trainer**: Responsável pelo treinamento do bot
- **Preprocessors**: Preparam o texto para processamento
- **Filters**: Filtram e refinam as respostas

### 2.2 Algoritmos Utilizados

#### 2.2.1 BestMatch Logic Adapter
- Utiliza o algoritmo de Levenshtein Distance para calcular a similaridade entre strings
- Implementa um sistema de pontuação para classificar as respostas mais adequadas
- Usa um threshold de similaridade (0.95) para garantir precisão nas respostas

#### 2.2.2 Processamento de Texto
- Tokenização: Divide o texto em tokens (palavras)
- Stemming: Reduz palavras à sua raiz
- Stop Words: Remove palavras comuns que não agregam significado
- Normalização: Padroniza o texto (minúsculas, acentos, etc.)

### 2.3 Armazenamento
- Utiliza MongoDB como banco de dados principal
- Estrutura de dados:
  ```json
  {
    "text": "texto da pergunta",
    "in_response_to": "texto da resposta",
    "confidence": 0.95,
    "created_at": "timestamp"
  }
  ```

## 3. Fluxo de Processamento

### 3.1 Recebimento da Mensagem
1. O texto é recebido via API
2. Passa pelos preprocessors
3. É tokenizado e normalizado

### 3.2 Geração de Resposta
1. O texto processado é comparado com a base de conhecimento
2. O BestMatch adapter calcula a similaridade
3. As respostas são classificadas por confiança
4. A resposta com maior confiança é selecionada

### 3.3 Treinamento
1. O bot é treinado com exemplos de conversas
2. A base de conhecimento é atualizada
3. Os parâmetros são ajustados com base no feedback

## 4. Configurações Técnicas

### 4.1 Parâmetros do ChatterBot
```python
chatbot = ChatBot(
    'CNJBot',
    storage_adapter='chatterbot.storage.MongoDatabaseAdapter',
    logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'maximum_similarity_threshold': 0.95,
            'default_response': 'Desculpe, não entendi sua pergunta.'
        }
    ]
)
```

### 4.2 Configurações do MongoDB
```python
mongo_config = {
    'database_uri': 'mongodb://localhost:27017/',
    'database': 'cnj-chatbot',
    'collection': 'conversations'
}
```

## 5. Métricas e Performance

### 5.1 Indicadores Técnicos
- **Precisão**: Medida pelo threshold de similaridade (0.95)
- **Tempo de Resposta**: Média de 100-200ms
- **Taxa de Acerto**: Baseada no feedback dos usuários
- **Uso de Memória**: ~100MB em operação normal

### 5.2 Limitações Técnicas
- Dependência da qualidade da base de conhecimento
- Sensibilidade a variações linguísticas
- Necessidade de retreinamento periódico
- Limitações do algoritmo de similaridade

## 6. Manutenção e Evolução

### 6.1 Atualizações
- Retreinamento semanal da base de conhecimento
- Ajuste de parâmetros baseado em métricas
- Atualização de dependências
- Backup automático do banco de dados

### 6.2 Monitoramento
- Logs de interação
- Métricas de performance
- Alertas de erro
- Relatórios de uso

## 7. Considerações de Segurança

### 7.1 Proteção de Dados
- Sanitização de entrada
- Validação de dados
- Logs de auditoria
- Backup criptografado

### 7.2 Boas Práticas
- Atualizações de segurança
- Controle de acesso
- Monitoramento de vulnerabilidades
- Documentação de incidentes

## 8. Processo de Aprendizado

### 8.1 Aprendizado Supervisionado
- O bot aprende através de exemplos de conversas fornecidos durante o treinamento
- Cada exemplo consiste em um par de pergunta e resposta
- O treinamento é feito em duas etapas:

  1. **Treinamento com Corpus em Português**:
  ```python
  from chatterbot.trainers import ChatterBotCorpusTrainer
  
  corpus_trainer = ChatterBotCorpusTrainer(chatbot)
  corpus_trainer.train("chatterbot.corpus.portuguese")
  ```
  Este treinamento fornece uma base linguística em português, incluindo:
  - Padrões de conversação básicos
  - Estruturas gramaticais comuns
  - Expressões idiomáticas
  - Saudações e despedidas

  2. **Treinamento com Dados Específicos**:
  ```python
  from chatterbot.trainers import ListTrainer
  
  trainer = ListTrainer(chatbot)
  trainer.train([
      "Como acessar o PREVJUD?",
      "Para acessar o PREVJUD, faça login no Marketplace da PDPJ através do endereço http://marketplace.pdpj.jus.br"
  ])
  ```

### 8.2 Aprendizado Contínuo
- O bot armazena cada interação no banco de dados
- Novas conversas são adicionadas à base de conhecimento
- O sistema mantém um histórico de confiança para cada resposta
- Respostas com baixa confiança são marcadas para revisão

### 8.3 Feedback e Ajustes
- Sistema de feedback para avaliar a qualidade das respostas
- Ajuste automático do threshold de similaridade
- Atualização da base de conhecimento baseada no feedback
- Identificação de padrões de perguntas frequentes

### 8.4 Processo de Melhoria
1. **Coleta de Dados**
   - Registro de todas as interações
   - Armazenamento de métricas de confiança
   - Coleta de feedback dos usuários

2. **Análise de Performance**
   - Identificação de respostas problemáticas
   - Análise de padrões de erro
   - Avaliação de taxa de acerto

3. **Atualização da Base**
   - Adição de novos exemplos
   - Correção de respostas incorretas
   - Remoção de exemplos obsoletos

4. **Retreinamento**
   - Processo automático semanal
   - Ajuste de parâmetros
   - Validação de novas respostas

### 8.5 Exemplo de Fluxo de Aprendizado
```python
# Exemplo de como o bot aprende com novas interações
def learn_from_interaction(question, answer, feedback):
    # Adiciona a nova interação ao banco de dados
    chatbot.storage.create(
        text=question,
        in_response_to=answer,
        confidence=feedback
    )
    
    # Se o feedback for positivo, adiciona ao conjunto de treinamento
    if feedback > 0.8:
        trainer.train([question, answer])
    
    # Ajusta o threshold de similaridade baseado no feedback
    if feedback < 0.5:
        chatbot.logic_adapters[0].maximum_similarity_threshold += 0.01
```

### 8.6 Métricas de Aprendizado
- **Taxa de Aprendizado**: Frequência de novas interações adicionadas
- **Qualidade do Aprendizado**: Medida pelo feedback dos usuários
- **Evolução da Base**: Número de exemplos únicos
- **Precisão Progressiva**: Melhoria na taxa de acerto ao longo do tempo 

## 9. Estrutura de Dados no MongoDB

### 9.1 Schema do Documento
Cada interação é armazenada em dois documentos relacionados:

1. **Documento da Pergunta**:
```json
{
  "_id": "ObjectId",
  "text": "Texto da pergunta",
  "search_text": "Texto processado para busca",
  "conversation": "ID da conversa",
  "persona": "",
  "tags": [],
  "in_response_to": null,
  "search_in_response_to": "",
  "created_at": "Timestamp"
}
```

2. **Documento da Resposta**:
```json
{
  "_id": "ObjectId",
  "text": "Texto da resposta",
  "search_text": "",
  "conversation": "ID da conversa",
  "persona": "bot:CNJBot",
  "tags": [],
  "in_response_to": "Texto da pergunta original",
  "search_in_response_to": "",
  "created_at": "Timestamp"
}
```

### 9.2 Campos Importantes
- **text**: Texto original da pergunta ou resposta
- **search_text**: Versão processada do texto para busca (tokenizada e normalizada)
- **in_response_to**: Relacionamento entre pergunta e resposta
- **persona**: Identifica se é uma resposta do bot
- **created_at**: Timestamp para rastreamento temporal

### 9.3 Processo de Armazenamento
1. **Recebimento da Pergunta**:
   - O texto é processado e tokenizado
   - Um novo documento é criado com a pergunta
   - O `search_text` é gerado para otimizar buscas

2. **Geração da Resposta**:
   - O bot processa a pergunta e gera uma resposta
   - Um novo documento é criado com a resposta
   - O campo `in_response_to` é preenchido com a pergunta original

### 9.4 Uso no Treinamento
1. **Busca de Respostas**:
   ```python
   # Exemplo de como o bot busca respostas similares
   def find_similar_response(question):
       # Processa a pergunta
       search_text = process_text(question)
       
       # Busca no MongoDB
       similar_questions = collection.find({
           "search_text": {
               "$regex": search_text,
               "$options": "i"
           }
       })
       
       # Retorna a resposta mais similar
       return get_best_match(similar_questions)
   ```

2. **Atualização da Base**:
   - Novas interações são adicionadas automaticamente
   - O `search_text` é atualizado para melhorar a busca
   - Relacionamentos são mantidos através do `in_response_to`

### 9.5 Exemplo Real
```json
// Pergunta
{
  "_id": "68234fb9c76210cbd4fa0b5e",
  "text": "Qual o tempo mínimo para expedir uma guia no BNMP?",
  "search_text": "PROPN:o NOUN:tempo PROPN:mínimo PROPN:para PROPN:expedir PROPN:uma PROPN:guia PROPN:bnmp",
  "in_response_to": null
}

// Resposta
{
  "_id": "68234fb9c76210cbd4fa0b5f",
  "text": "O prazo mínimo atualmente estabelecido para expedição de uma Guia no BNMP 3.0 é de 12 meses...",
  "persona": "bot:CNJBot",
  "in_response_to": "Qual o tempo mínimo para expedir uma guia no BNMP?"
}
```

## 10. Sistema de Feedback

### 10.1 Estrutura do Feedback
```json
{
  "_id": "ObjectId",
  "question_id": "ID da pergunta",
  "response_id": "ID da resposta",
  "rating": 1,  // 1 (positivo) ou 0 (negativo)
  "user_id": "ID do usuário",
  "timestamp": "Data e hora do feedback",
  "comments": "Comentários opcionais do usuário"
}
```

### 10.2 Implementação do Feedback
```python
class FeedbackAdapter:
    def __init__(self):
        """Inicializa o adaptador de feedback"""
        # Configuração do MongoDB
        self.mongo_host = os.getenv('MONGO_HOST', 'mongodb')
        self.mongo_port = os.getenv('MONGO_PORT', '27017')
        self.mongo_db = os.getenv('MONGO_DB', 'cnj-chatbot')

        # URL de conexão completa
        self.mongo_uri = f"mongodb://{self.mongo_host}:{self.mongo_port}/{self.mongo_db}"

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.feedback_collection = self.db.feedback
        self.responses_collection = self.db.statements
        
        # Configura índices
        self._setup_indexes()
        
        logging.info("FeedbackAdapter inicializado com sucesso")

    def _setup_indexes(self):
        """Configura os índices necessários no MongoDB."""
        self.feedback_collection.create_index([("question_id", 1)])
        self.feedback_collection.create_index([("response_id", 1)])
        self.feedback_collection.create_index([("user_id", 1)])
        self.feedback_collection.create_index([("timestamp", 1)])

    def record_feedback(
        self,
        question_id: str,
        response_id: str,
        rating: int,
        user_id: Optional[str] = None,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra um feedback do usuário.
        
        Args:
            question_id: ID da pergunta
            response_id: ID da resposta
            rating: Avaliação (1 para positivo, 0 para negativo)
            user_id: ID do usuário (opcional)
            comments: Comentários adicionais (opcional)
            
        Returns:
            Dicionário com o feedback registrado
        """
        feedback = {
            "question_id": question_id,
            "response_id": response_id,
            "rating": rating,
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "comments": comments
        }
        
        result = self.feedback_collection.insert_one(feedback)
        feedback["_id"] = result.inserted_id
        
        # Atualiza a confiança da resposta
        self._update_response_confidence(response_id, 0.1 if rating == 1 else -0.1)
        
        logging.info(f"Feedback registrado: {feedback}")
        return feedback

    def _update_response_confidence(self, response_id: str, delta: float):
        """
        Atualiza a confiança de uma resposta.
        
        Args:
            response_id: ID da resposta
            delta: Valor a ser adicionado/subtraído da confiança
        """
        response = self.responses_collection.find_one({"_id": response_id})
        if response:
            current_confidence = response.get("confidence", 0.5)
            new_confidence = min(1.0, max(0.0, current_confidence + delta))
            
            self.responses_collection.update_one(
                {"_id": response_id},
                {"$set": {"confidence": new_confidence}}
            )
            
            logging.info(f"Confiança da resposta {response_id} atualizada para {new_confidence}")

    def get_feedback_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de feedback.
        
        Returns:
            Dicionário com estatísticas de feedback
        """
        total = self.feedback_collection.count_documents({})
        positive = self.feedback_collection.count_documents({"rating": 1})
        negative = self.feedback_collection.count_documents({"rating": 0})
        
        return {
            "total_feedback": total,
            "positive_feedback": positive,
            "negative_feedback": negative,
            "satisfaction_rate": (positive / total * 100) if total > 0 else 0,
            "recent_feedback": list(self.feedback_collection.find(
                {},
                {"_id": 0}
            ).sort("timestamp", -1).limit(10))
        }

### 10.3 Processo de Coleta
1. **Interface do Usuário**:
   - Botões de feedback (👍/👎) após cada resposta
   - Feedback visual imediato
   - Feedback anônimo para usuários não logados
   - Botões são desabilitados após o envio do feedback
   - Feedback é específico para cada mensagem no chat

2. **Armazenamento**:
   - Feedback é salvo no MongoDB
   - Relacionado com a pergunta e resposta
   - Inclui metadados (timestamp, user_id)
   - Índices otimizados para consultas frequentes

3. **Análise**:
   - Cálculo de taxa de satisfação
   - Identificação de padrões de erro
   - Agrupamento por tipo de pergunta
   - Histórico dos últimos 10 feedbacks

### 10.4 Uso do Feedback
1. **Ajuste de Confiança**:
   - Respostas com feedback positivo ganham confiança (+0.1)
   - Respostas com feedback negativo perdem confiança (-0.1)
   - Confiança é limitada entre 0.0 e 1.0
   - Atualização é feita em tempo real

2. **Métricas**:
   - Taxa de satisfação geral
   - Distribuição de feedback por tipo de pergunta
   - Tendências de satisfação ao longo do tempo
   - Feedback recente para análise rápida

### 10.5 Exemplo de Uso
```javascript
// Exemplo de como o feedback é processado no frontend
async function sendFeedback(questionId, responseId, rating, button) {
    // Encontra o container de feedback específico desta mensagem
    const feedbackContainer = button.closest('.chat-feedback');
    // Desabilita apenas os botões deste container
    const buttons = feedbackContainer.querySelectorAll('button');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
    });

    try {
        const response = await fetch('http://localhost:8000/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: questionId,
                response_id: responseId,
                rating: rating
            })
        });
        
        const data = await response.json();
        if (data.success) {
            // Atualiza o visual apenas dos botões deste container
            buttons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
        } else {
            // Se houver erro, reabilita apenas os botões deste container
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '';
                btn.style.cursor = '';
            });
        }
    } catch (err) {
        console.error('Erro ao enviar feedback:', err);
        // Em caso de erro, reabilita apenas os botões deste container
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '';
            btn.style.cursor = '';
        });
    }
}
```

### 10.6 Dashboard de Feedback
- Visualização em tempo real das métricas
- Análise de tendências
- Relatórios de satisfação
- Alertas para problemas recorrentes
- Histórico dos últimos feedbacks
- Taxa de satisfação por período

## 11. API Endpoints

### 11.1 Endpoints de Chat

#### POST /chat
Endpoint principal para interação com o chatbot.

**Request Body:**
```json
{
    "message": "string",
    "user_id": "string (opcional)"
}
```

**Response:**
```json
{
    "response": "string",
    "confidence": "float",
    "response_id": "string"
}
```

### 11.2 Endpoints de Feedback

#### POST /feedback
Endpoint para registrar feedback do usuário sobre uma resposta.

**Request Body:**
```json
{
    "question_id": "string",
    "response_id": "string",
    "rating": "integer (1-5)",
    "user_id": "string (opcional)",
    "comments": "string (opcional)"
}
```

**Response:**
```json
{
    "success": "boolean",
    "message": "string"
}
```

#### GET /feedback/stats
Endpoint para obter estatísticas de feedback.

**Response:**
```json
{
    "total_feedback": "integer",
    "positive_feedback": "integer",
    "negative_feedback": "integer",
    "satisfaction_rate": "float",
    "recent_feedback": [
        {
            "question_id": "string",
            "response_id": "string",
            "rating": "integer",
            "user_id": "string",
            "timestamp": "datetime",
            "comments": "string (opcional)"
        }
    ]
}
```

### 11.3 Exemplo de Uso

```python
import requests

# Enviar mensagem
response = requests.post("http://localhost:8000/chat", json={
    "message": "Olá, como posso ajudar?",
    "user_id": "user123"
})

# Registrar feedback
feedback = requests.post("http://localhost:8000/feedback", json={
    "question_id": response.json()["response_id"],
    "response_id": response.json()["response_id"],
    "rating": 5,
    "user_id": "user123",
    "comments": "Resposta muito útil!"
})

# Obter estatísticas
stats = requests.get("http://localhost:8000/feedback/stats")
```