# Dockerfile simplificado para EasyPane
FROM python:3.11-slim

# Variáveis de ambiente
ENV INSTANCE_NAME="consultar"
ENV EVOLUTION_URL="https://oab-evolution-api.iatjve.easypanel.host"
ENV EVOLUTION_KEY="429683C4C977415CAAFCCE10F7D57E11"
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instalar apenas dependências essenciais
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg2 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome de forma mais simples
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver (versão fixa compatível)
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app.py .

# Criar usuário (opcional para EasyPane)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Porta da aplicação
EXPOSE 8080

# Comando de inicialização
CMD ["python", "app.py"]
