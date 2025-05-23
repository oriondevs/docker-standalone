from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient
import logging
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv(override=True)

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