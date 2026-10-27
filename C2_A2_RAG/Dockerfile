FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servicos ./servicos
COPY documentos ./documentos
COPY tests ./tests
COPY scripts ./scripts
RUN mkdir -p /app/dados
EXPOSE 8001 8002 8003
