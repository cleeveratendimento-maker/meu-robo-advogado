# Usa uma versão leve do Python
FROM python:3.10-slim

# Cria a pasta do app
WORKDIR /app

# Instala as bibliotecas necessárias
RUN pip install flask requests gunicorn jira

# Copia os arquivos do GitHub para dentro do robô
COPY . .

# Inicia o robô com 1 Worker (Memória Única para não esquecer a conversa)
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
