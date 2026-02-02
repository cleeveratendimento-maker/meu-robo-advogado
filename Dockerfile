FROM python:3.10-slim

# MUDANÇA FORÇADA: Mude o número abaixo para obrigar o servidor a atualizar
ENV VERSAO_DO_ROBO=2.0_FINAL

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala as ferramentas
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Copia os arquivos novos (com a correção do /tmp)
COPY . .

# Inicia o robô na porta 5000
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
