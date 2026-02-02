FROM python:3.10-slim

# --- COMANDO DE ATUALIZAÇÃO FORÇADA ---
# Mude o número abaixo sempre que precisar forçar uma atualização
ENV ATUALIZAR_AGORA=99999

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala as ferramentas
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Copia tudo (incluindo o app.py novo com /tmp)
COPY . .

# Inicia o servidor
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
