FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# 1. Instala apenas o básico para o sistema não travar
RUN apt-get update && apt-get install -y wget gnupg && rm -rf /var/lib/apt/lists/*

# 2. Instala o Python e o Playwright
RUN pip install flask requests gunicorn reportlab Pillow certifi playwright

# 3. O PULO DO GATO: Instala o Chrome E as peças do Linux automaticamente
# (O --with-deps descobre sozinho o que falta e corrige o erro)
RUN playwright install --with-deps chromium

# 4. Copia seus arquivos
COPY . .

# 5. Roda o robô
CMD ["gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]
