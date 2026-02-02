FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala bibliotecas Python
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Instala navegador
RUN playwright install chromium

COPY . .

# Inicia o robô
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
