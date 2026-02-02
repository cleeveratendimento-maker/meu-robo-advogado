FROM python:3.10-slim

# --- O SEGREDO: ISSO FORÇA A ATUALIZAÇÃO ---
# (O servidor é obrigado a reconstruir tudo por causa dessa linha)
ENV FORCE_UPDATE=versao_final_corrigida

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Instala as ferramentas necessárias
RUN pip install flask requests gunicorn reportlab Pillow certifi

# Copia os arquivos novos (com a correção do /tmp)
COPY . .

# Inicia o robô na porta 5000
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
