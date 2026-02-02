FROM python:3.10-slim

# ESSA LINHA OBRIGA O SERVIDOR A ATUALIZAR (TIPO UM CHUTE)
ENV FORCE_UPDATE=123

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN pip install flask requests gunicorn reportlab Pillow certifi

COPY . .

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
