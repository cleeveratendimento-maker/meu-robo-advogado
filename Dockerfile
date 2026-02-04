FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV VERSAO_BOT=17.1_MENU_HIBRIDO

RUN pip install flask requests gunicorn jira

COPY app.py /app/app.py

CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
