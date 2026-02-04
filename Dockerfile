FROM python:3.10-slim

# --- CONFIGURAÇÃO DO AMBIENTE ---
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV VERSAO_BOT=15.0_NOVA_BUTTONS_PRO

# 1. Instalação das bibliotecas
RUN pip install flask requests gunicorn jira

# 2. ESCREVENDO O CÓDIGO PYTHON (ATUALIZADO COM BOTÕES)
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
# Token Jira (Mantido do seu código original)
JIRA_TOKEN = "ATATT3xFfGF0gTvEQie0CsNToWBMT5sgW-kXIwm5HH4vkEqRFl_M2s1peiP0GtjsoBWe5wk_mnLOsTByWxR_RXQXa3Qxa8-bQj3uTB2WPBC12nwtFW59FD2K5xpGbOjFnLQ7ngz2v69_Vn8XZ5iOmO6O5AlGfQIZE7YnJ99RnRAftvd9RiOQ9tc=F9128AAA"

EMAIL_DESTINO_TOMTICKET = "chamados.ti@pillowtex.com.br"

# 👇👇👇 DADOS DE ENVIO (GMAIL) 👇👇👇
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "seu.email@gmail.com"      # 🔴 SEU GMAIL AQUI
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"  # 🔴 SENHA DE APP AQUI

# Dados da Evolution API
INSTANCE_NAME = "Chatboot"
EVOLUTION_URL = "https://chatboot-evolution-api.iatjve.easypanel.host"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"

estados_usuarios = {}

# ======================================================
# 🎨 MOTOR VISUAL N.O.V.A. (COM BOTÕES)
# ======================================================

def reagir(numero, emoji):
    try:
        requests.post(f"{EVOLUTION_URL}/message/sendReaction/{INSTANCE_NAME}", 
                      json={"number": numero, "reaction": emoji}, headers={"apikey": EVOLUTION_KEY})
    except: pass

def digitando(numero):
    try:
        requests.post(f"{EVOLUTION_URL}/chat/sendPresence/{INSTANCE_NAME}", 
                      json={"number": numero, "presence": "composing", "delay": 1200}, headers={"apikey": EVOLUTION_KEY})
    except: pass

def enviar_msg(numero, texto):
    digitando(numero)
    requests.post(f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}", 
                  json={"number": numero, "text": texto}, headers={"apikey": EVOLUTION_KEY})

def apresentar_interface_ai(numero):
    try:
        reagir(numero, "💠")
        digitando(numero)
        
        # --- AQUI ESTÁ A MUDANÇA PARA BOTÕES ---
        payload = {
            "number": numero,
            "title": "💠 SYSTEM ONLINE v15.0",
            "description": "Olá! Sou a N.O.V.A. Escolha uma opção abaixo:",
            "footer": "Pillowtex TI",
            "buttons": [
                {"id": "1", "displayText": "📝 ABRIR CHAMADO"},
                {"id": "2", "displayText": "🔍 RASTREAR SDB"},
                {"id": "3", "displayText": "👤 FALA C/ HUMANO"}
            ]
        }
        
        requests.post(f"{EVOLUTION_URL}/message/sendButtons/{INSTANCE_NAME}", 
                      json=payload, 
                      headers={"apikey": EVOLUTION_KEY})

    except Exception as e: print(e)

# ======================================================
# 🔧 NÚCLEO LÓGICO (JIRA + EMAIL)
# ======================================================
def consultar_jira(ticket_id):
    try:
        jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL_LOGIN, JIRA_TOKEN))
        issue = jira.issue(ticket_id)
        return {
            "resumo": issue.fields.summary,
            "status": issue.fields.status.name.upper(),
            "responsavel": issue.fields.assignee.displayName if issue.fields.assignee else "Fila Automática",
            "data": datetime.datetime.strptime(issue.fields.created, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y"),
            "link": f"{JIRA_SERVER}/browse/{ticket_id}"
        }
    except: return None

def enviar_email(nome, email_user, problema):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_DESTINO_TOMTICKET
        msg['Subject'] = f"[NOVA AI] Ticket: {nome}"
        msg.add_header('Reply-To', email_user)
        
        corpo = f"RELATÓRIO DE INCIDENTE\n======================\n\nUSUÁRIO: {nome}\nEMAIL: {email_user}\n\nDESCRIÇÃO:\n{problema}\n\n--\nProcessado por N.O.V.A. v15.0"
        msg.attach(MIMEText(corpo, 'plain'))

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
        
        # --- PARSER ATUALIZADO (IMPORTANTE) ---
        # Agora ele lê: Texto Normal OU Resposta de Botão
        texto = (
            msg.get("conversation") or 
            msg.get("extendedTextMessage", {}).get("text") or
            msg.get("buttonsResponseMessage", {}).get("selectedButtonId") or 
            ""
        )
        
        remetente = data.get("data", {}).get("key", {}).get("remoteJid")
        
        if not texto or not remetente: return "OK", 200
        texto_lower = texto.lower().strip()
        
        # === COMANDOS DE RESET ===
        if texto_lower in ["sair", "cancelar", "reset", "menu"]:
            if remetente in estados_usuarios: del estados_usuarios[remetente]
            apresentar_interface_ai(remetente)
            return "OK", 200

        # === GATILHOS INICIAIS ===
        gatilhos = ["oi", "ola", "bom dia", "ajuda", "ti", "suporte", "nova", "inicio"]
        
        if remetente not in estados_usuarios:
            if "sdb" in texto_lower: pass
            elif not any(x in texto_lower for x in gatilhos) and texto_lower not in ["1", "2", "3"]: 
                return "OK", 200
            
            # Se não é comando direto, mostra menu
            if not "sdb" in texto_lower and texto_lower not in ["1", "2", "3"]:
                 apresentar_interface_ai(remetente)
                 return "OK", 200

        # === ROTEADOR DE OPÇÕES ===
        acao = ""
        if texto_lower == "1": acao = "abrir"
        elif texto_lower == "2": acao = "status"
        elif texto_lower == "3": acao = "falar"

        if acao == "abrir":
            reagir(remetente, "📝")
            estados_usuarios[remetente] = {"passo": "aguardando_nome", "dados": {}}
            enviar_msg(remetente, "📝 *PROTOCOLO DE ABERTURA*\n\nPor favor, digite seu *Nome Completo*:")
            return "OK", 200

        if acao == "status":
             reagir(remetente, "🔍")
             enviar_msg(remetente, "🔍 *RASTREIO SDB*\n\nInforme o código do protocolo (Ex: SDB 90609):")
             return "OK", 200
             
        if acao == "falar":
             reagir(remetente, "👤")
             enviar_msg(remetente, "✅ Transferindo para analista humano...\nAguarde um instante.")
             return "OK", 200

        # === FLUXO DE ABERTURA (ETAPAS) ===
        if remetente in estados_usuarios:
            passo = estados_usuarios[remetente]["passo"]
            
            if passo == "aguardando_nome":
                estados_usuarios[remetente]["dados"]["nome"] = texto
                estados_usuarios[remetente]["passo"] = "aguardando_email"
                enviar_msg(remetente, f"Ok, *{texto}*.\nAgora digite seu *E-mail Corporativo*:")
            
            elif passo == "aguardando_email":
                estados_usuarios[remetente]["dados"]["email"] = texto
                estados_usuarios[remetente]["passo"] = "aguardando_problema"
                enviar_msg(remetente, "📝 *Descrição do Problema*\nRelate o que está acontecendo:")
            
            elif passo == "aguardando_problema":
                enviar_msg(remetente, "⏳ Registrando chamado...")
                sucesso = enviar_email(estados_usuarios[remetente]["dados"]["nome"], estados_usuarios[remetente]["dados"]["email"], texto)
                
                if sucesso:
                    msg_final = "✅ *CHAMADO ABERTO COM SUCESSO*\nVerifique seu e-mail para acompanhar."
                    enviar_msg(remetente, msg_final)
                else:
                    reagir(remetente, "❌")
                    enviar_msg(remetente, "⚠️ Erro no servidor de e-mail. Tente mais tarde.")
                
                del estados_usuarios[remetente]
            return "OK", 200

        # === CONSULTA SDB ===
        if "sdb" in texto_lower:
            num = "".join([c for c in texto if c.isdigit()])
            chave = f"SDB-{num}"
            enviar_msg(remetente, f"🔄 Buscando {chave}...")
            
            d = consultar_jira(chave)
            if d:
                resp = f"📂 *{chave}*\nStatus: {d['status']}\nResp: {d['responsavel']}\n🔗 {d['link']}"
            else:
                resp = f"🚫 Chamado {chave} não encontrado."
            enviar_msg(remetente, resp)

    except Exception as e: print(e)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

# 3. Execução
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
