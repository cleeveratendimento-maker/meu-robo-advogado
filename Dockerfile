# Dockerfile MÍNIMO para EasyPane
FROM python:3.11-slim

# Instalar dependências mínimas
RUN apt-get update && apt-get install -y wget curl

# Instalar Chrome simplificado
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Diretório de trabalho
WORKDIR /app

# Copiar código
COPY app.py .

# Instalar Python packages
RUN pip install selenium==4.15.2

# Comando
CMD ["python", "app.py"]
