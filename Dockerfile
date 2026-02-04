FROM python:3.10-slim

# --- CONFIGURAÇÃO ---
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV VERSAO_BOT=17.0_NOVA_LIST_MENU

# Instala bibliotecas
RUN pip install flask requests gunicorn jira

# --- CÓDIGO PYTHON (COM MENU LISTA) ---
RUN cat <<'EOF' > app.py
# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from jira import JIRA
import requests
import smtplib
import datetime
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ======================================================
# ⚙️ SUAS CONFIGURAÇÕES
# ======================================================
JIRA_SERVER = "https://zonacriativa.atlassian.net"
JIRA_EMAIL_LOGIN = "ti@pillowtex.com.br"
JIRA_TOKEN = "ATATT3xFfGF0gTvEQie0CsNToWBMT5sgW-kXIwm5HH4vkEqRFl_M2s1peiP0GtjsoBWe5wk_mnLOsTByWxR_RXQXa3Qxa8-bQj3uTB2WPBC12nwtFW59FD2K5xpGbOjFnLQ7ngz2v69_Vn8XZ5iOmO6O5AlGfQIZE7YnJ99RnRAftvd9RiOQ9tc=F9128AAA"

EMAIL_DESTINO_TOMTICKET = "chamados.ti@pillowtex.com.br"

# SMTP (GMAIL)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "seu.email@gmail.com"      # 🔴 CONFIGURAR
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"  # 🔴 CONFIGURAR

# EVOLUTION API
INSTANCE_NAME = "Chatboot"
EVOLUTION_URL = "https://chatboot-evolution-api.iatjve.easypanel.host"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"

estados_usuarios = {}

# ======================================================
# 🎨 FUNÇÕES VISUAIS (LISTA)
# ======================================================

def enviar_msg(numero, texto):
    try:
        requests.post(f"{EVOLUTION_URL}/chat/sendPresence/{INSTANCE_NAME}", 
                      json={"number": numero, "presence": "composing", "delay": 1200}, headers={"apikey": EVOLUTION_KEY})
        
        requests.post(f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}", 
                      json={"number": numero, "text": texto}, headers={"apikey": EVOLUTION_KEY})
    except: pass

def apresentar_lista(numero):
    try:
        # Reage para dar feedback visual
        requests.post(f"{EVOLUTION_URL}/message/sendReaction/{INSTANCE_NAME}", 
                      json={"number": numero, "reaction": "💠"}, headers={"apikey": EVOLUTION_KEY})

        # --- ESTRUTURA DA LISTA (LIST MESSAGE) ---
        payload = {
            "number": numero,
            "title": "💠 SYSTEM ONLINE v17.0",
            "description": "Olá! Sou a N.O.V.A. Como posso ajudar você hoje?",
            "buttonText": "VER OPÇÕES",  # O texto do botão que abre a lista
            "footer": "Pillowtex TI",
            "sections": [
                {
                    "title": "Serviços Disponíveis",
                    "rows": [
                        {
                            "rowId": "1",
                            "title": "📝 Abrir Chamado",
                            "description": "Relatar problemas de TI"
                        },
                        {
                            "rowId": "2",
                            "title": "🔍 Rastrear SDB",
                            "description": "Consultar status no Jira"
                        },
                        {
                            "rowId": "3",
                            "title": "👤 Falar com Humano",
                            "description": "Transferir atendimento"
                        }
                    ]
                }
            ]
        }
        
        # Endpoint específico para listas
        requests.post(f"{EVOLUTION_URL}/message/sendList/{INSTANCE_NAME}", 
                      json=payload, 
                      headers={"apikey": EVOLUTION_KEY})

    except Exception as e: print(f"Erro lista: {e}")

# ======================================================
# 🔧 LÓGICA PRINCIPAL
# ======================================================
def consultar_jira(ticket_id):
    try:
        jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL_LOGIN, JIRA_TOKEN))
        issue = jira.issue(ticket_id)
        return {
            "resumo": issue.fields.summary,
            "status": issue.fields.status.name.upper(),
            "responsavel": issue.fields.assignee.displayName if issue.fields.assignee else "Automático",
            "link": f"{JIRA_SERVER}/browse/{ticket_id}"
        }
    except: return None

def enviar_email(nome, email_user, problema):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_DESTINO_TOMTICKET
        msg['Subject'] = f"[NOVA] Ticket: {nome}"
        msg.add_header('Reply-To', email_user)
        msg.attach(MIMEText(f"USUÁRIO: {nome}\nEMAIL: {email_user}\n\n{problema}", 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, EMAIL_DESTINO_TOMTICKET, msg.as_string())
        server.quit()
        return True
    except: return False

@app.route("/", methods=["POST"])
@app.route("/<path:path>", methods=["POST"])
def webhook(path=None):
    try:
        data = request.json
        if not data or data.get("event") != "messages.upsert": return "OK", 200
        
        msg = data.get("data", {}).get("message", {})
        remetente = data.get("data", {}).get("key", {}).get("remoteJid")
        
        # --- PARSER ATUALIZADO (SUPORTE A LISTA) ---
        # Captura texto normal, resposta de botão ou resposta de lista
        texto = (
            msg.get("conversation") or 
            msg.get("extendedTextMessage", {}).get("text") or
            msg.get("buttonsResponseMessage", {}).get("selectedButtonId") or
            msg.get("listResponseMessage", {}).get("singleSelectReply", {}).get("selectedRowId") or
            ""
        )
        
        if not texto or not remetente: return "OK", 200
        texto_lower = texto.lower().strip()

        # === 1. COMANDOS DE RESET ===
        if texto_lower in ["sair", "menu", "cancelar", "reset"]:
            if remetente in estados_usuarios: del estados_usuarios[remetente]
            apresentar_lista(remetente)
            return "OK", 200

        # === 2. FLUXO DE CADASTRO ===
        if remetente in estados_usuarios:
            passo = estados_usuarios[remetente]["passo"]
            
            if passo == "nome":
                estados_usuarios[remetente]["dados"]["nome"] = texto
                estados_usuarios[remetente]["passo"] = "email"
                enviar_msg(remetente, f"Ok, *{texto}*. Qual seu *E-mail*?")
            
            elif passo == "email":
                estados_usuarios[remetente]["dados"]["email"] = texto
                estados_usuarios[remetente]["passo"] = "problema"
                enviar_msg(remetente, "Descreva o *problema*:")
            
            elif passo == "problema":
                enviar_msg(remetente, "⏳ Registrando...")
                ok = enviar_email(estados_usuarios[remetente]["dados"]["nome"], estados_usuarios[remetente]["dados"]["email"], texto)
                if ok: enviar_msg(remetente, "✅ Chamado criado! Verifique seu e-mail.")
                else: enviar_msg(remetente, "❌ Erro no e-mail.")
                del estados_usuarios[remetente]
            
            return "OK", 200

        # === 3. MENU PRINCIPAL (Gatilhos) ===
        # Aceita tanto o número "1" digitado quanto o ID "1" clicado na lista
        if texto_lower == "1":
            estados_usuarios[remetente] = {"passo": "nome", "dados": {}}
            enviar_msg(remetente, "📝 Digite seu *Nome Completo*:")
            return "OK", 200
            
        if texto_lower == "2":
            enviar_msg(remetente, "🔍 Digite o chamado (Ex: SDB 12345):")
            return "OK", 200
            
        if texto_lower == "3":
            enviar_msg(remetente, "👤 Transferindo para humano...")
            return "OK", 200
            
        if "sdb" in texto_lower:
            num = "".join([c for c in texto if c.isdigit()])
            res = consultar_jira(f"SDB-{num}")
            if res: enviar_msg(remetente, f"📂 *SDB-{num}*\nStatus: {res['status']}\nResp: {res['responsavel']}")
            else: enviar_msg(remetente, f"🚫 SDB-{num} não encontrado.")
            return "OK", 200

        # === 4. SE NÃO ENTENDEU, MOSTRA A LISTA ===
        apresentar_lista(remetente)

    except Exception as e: print(e)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
