FROM python:3.12-slim

WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar arquivos de configuração
COPY pyproject.toml .

# Criar e ativar ambiente virtual
RUN uv venv

COPY .env .

# Copiar o resto dos arquivos
COPY . .

# Instalar dependências usando uv
RUN uv sync

RUN uv run spacy download en_core_web_sm

# Expor a porta
EXPOSE 8000

# Comando para iniciar a aplicação usando uv run
CMD ["uv", "run", "main.py", "--mode", "api", "--host", "0.0.0.0", "--port", "8000"]