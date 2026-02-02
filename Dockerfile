FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala apenas o necessário para o PDF e o Site (Sem Navegador Pesado)
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Copia os arquivos
COPY . .

# Comando de início na porta 5000
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
