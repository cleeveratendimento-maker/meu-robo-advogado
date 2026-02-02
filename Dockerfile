# Usa a imagem da Microsoft que JÁ TEM o navegador e o Python prontos
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Instala apenas as bibliotecas do seu código
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Copia seus arquivos
COPY . .

# Comando de Início (Garante a porta 5000)
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
