import csv
import os
from pathlib import Path

def read_conversations_from_csv(file_path):
    """
    Lê conversas de um arquivo CSV.
    O arquivo deve ter duas colunas: pergunta e resposta.
    Usa ponto e vírgula (;) como separador.
    """
    conversations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)  # Pula o cabeçalho
            for row in reader:
                if len(row) >= 2:  # Verifica se tem pelo menos duas colunas
                    question, answer = row[0], row[1]
                    conversations.append((question, answer))
    except Exception as e:
        print(f"Erro ao ler o arquivo {file_path}: {str(e)}")
    return conversations

def get_all_conversations():
    """
    Retorna todas as conversas em um formato plano para treinamento,
    lendo todos os arquivos CSV da pasta conversations/csv/
    """
    all_conversations = []
    csv_dir = Path("conversations/csv")
    
    # Garante que o diretório existe
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    # Lista todos os arquivos CSV no diretório
    csv_files = list(csv_dir.glob("*.csv"))
    
    if not csv_files:
        print("Aviso: Nenhum arquivo CSV encontrado em conversations/csv/")
        return all_conversations
    
    # Lê cada arquivo CSV encontrado
    for csv_file in csv_files:
        print(f"Lendo arquivo: {csv_file.name}")
        conversations = read_conversations_from_csv(csv_file)
        for question, answer in conversations:
            all_conversations.append(question)
            all_conversations.append(answer)
    
    return all_conversations 