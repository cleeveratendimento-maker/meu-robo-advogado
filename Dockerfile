FROM python:3.10-slim

# ESSA LINHA AQUI OBRIGA O SERVIDOR A ATUALIZAR (TIPO UM CHUTE)
ENV FORCE_UPDATE=12345

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala as ferramentas
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Copia o código novo (com a pasta /tmp)
COPY . .

# Inicia o robô
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
