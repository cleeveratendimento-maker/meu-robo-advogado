FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# 1. Instala dependências do sistema para o Chrome rodar
RUN apt-get update && apt-get install -y \
    wget gnupg libgconf-2-4 libxss1 libnss3 libasound2 \
    libatk-bridge2.0-0 libgtk-3-0 fonts-liberation libappindicator3-1 \
    xdg-utils libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala Python e Playwright
RUN pip install flask requests gunicorn reportlab Pillow certifi playwright

# 3. Baixa o navegador Chromium
RUN playwright install --with-deps chromium

# Pastas e Permissões
RUN mkdir -p /app/static_pdfs /app/assets

# Copia o código
COPY app.py .

# Comando de Início
CMD ["gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]
