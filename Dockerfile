# Usa a imagem oficial do Playwright (Já vem com o Linux configurado)
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# 1. Instala o Flask e as ferramentas de PDF
RUN pip install flask requests gunicorn reportlab Pillow certifi

# 2. Instala o Navegador Chromium (Sem erros de sistema)
RUN playwright install chromium

# 3. Copia seus arquivos
COPY . .

# 4. Coloca o robô para rodar
CMD ["gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]
