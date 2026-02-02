FROM python:3.10-slim

# ESSA LINHA OBRIGA A ATUALIZAR
ENV FORCE_UPDATE=v5_resolvido

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala as ferramentas
RUN pip install flask requests gunicorn reportlab Pillow certifi

# --- O TRUQUE DE MESTRE ---
# Criamos a pasta /app/assets na marra para o robô não reclamar
RUN mkdir -p /app/assets && chmod 777 /app/assets

# Copia os arquivos
COPY . .

# Inicia o robô
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
