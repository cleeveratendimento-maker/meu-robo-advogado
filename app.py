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
# ⚙️ CONFIGURAÇÕES (PREENCHA AQUI!)
# ======================================================
JIRA_SERVER = "[https://zonacriativa.atlassian.net](https://zonacriativa.atlassian.net)"
JIRA_EMAIL_LOGIN = "ti@pillowtex.com.br"
# 👇 SEU TOKEN JIRA
JIRA_TOKEN = "ATATT3xFfGF0gTvEQie0CsNToWBMT5sgW-kXIwm5HH4vkEqRFl_M2s1peiP0GtjsoBWe5wk_mnLOsTByWxR_RXQXa3Qxa8-bQj3uTB2WPBC12nwtFW59FD2K5xpGbOjFnLQ7ngz2v69_Vn8XZ5iOmO6O5AlGfQIZE7YnJ99RnRAftvd9RiOQ9tc=F9128AAA"

EMAIL_DESTINO_TOMTICKET = "chamados.ti@pillowtex.com.br"

# 👇 SEU GMAIL E SENHA DE APP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "ti.monitoriamento@gmail.com"      # 🔴 SEU GMAIL
SMTP_PASSWORD = "lvvg ragw eqry fgdz"  # 🔴 SUA SENHA DE APP

# 👇 DADOS DO EVOLUTION API
INSTANCE_NAME = "Chatboot"
EVOLUTION_URL = "[https://chatboot-evolution-api.iatjve.easypanel.host](https://chatboot-evolution-api.iatjve.easypanel.host)"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"

# GIF DE BOAS-VINDAS (Tech Blue)
BANNER_GIF = "[https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYmJmaG14cm14bnh6eGxhYm14bnh6eGxhYm14bnh6eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif](https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYmJmaG14cm14bnh6eGxhYm14bnh6eGxhYm14bnh6eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif)"

estados_usuarios = {}

# ======================================================
# 🎨 FUNÇÕES VISUAIS
# ======================================================

def reagir(numero, emoji):
    try:
        requests.post(f"{EVOLUTION_URL}/message/sendReaction/{INSTANCE_NAME}", 
                      json={"number": numero, "reaction": emoji}, headers={"apikey": EVOLUTION_KEY})
    except: pass

def digitando(numero):
    try:
        requests.post(f"{EVOLUTION_URL}/chat/sendPresence/{INSTANCE_NAME}", 
                      json={"number": numero, "presence": "composing", "delay": 2000}, headers={"apikey": EVOLUTION_KEY})
    except: pass

def enviar_msg(numero, texto):
    digitando(numero)
    requests.post(f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}", 
                  json={"number": numero, "text": texto}, headers={"apikey": EVOLUTION_KEY})

def apresentar_menu_principal(numero):
    try:
        reagir(numero, "💠")
        
        # 1. Envia o GIF
        requests.post(f"{EVOLUTION_URL}/message/sendMedia/{INSTANCE_NAME}", 
                      json={"number": numero, "media": BANNER_GIF, "mediatype": "video", "caption": "💠 *SISTEMA N.O.V.A. ONLINE*"}, 
                      headers={"apikey": EVOLUTION_KEY})
        
        time.sleep(2)
        digitando(numero)

        # 2. Envia o Menu
        menu = "╔════════════════════╗\n║   CENTRAL DE COMANDO   ║\n╚════════════════════╝\n\nOlá. Selecione o protocolo desejado:\n\n1️⃣  *INICIAR SUPORTE*\n      _Abrir novo chamado técnico_\n\n2️⃣  *RASTREAR SDB*\n      _Consultar status de protocolo_\n\n3️⃣  *ATENDENTE HUMANO*\n      _Conexão direta com analista_\n\n_> Digite apenas o número da opção:_"
        enviar_msg(numero, menu)

    except Exception as e: print(e)

# ======================================================
# 🔧 LÓGICA TÉCNICA
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
        msg['Subject'] = f"[BOT] Chamado: {nome}"
        msg.add_header('Reply-To', email_user)
        
        corpo = f"Solicitante: {nome}\nEmail: {email_user}\n\nRelato:\n{problema}\n\n--\nEnviado por N.O.V.A. System."
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
        texto = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text") or ""
        remetente = data.get("data", {}).get("key", {}).get("remoteJid")
        
        if not texto or not remetente: return "OK", 200
        texto_lower = texto.lower().strip()
        
        # === GATILHOS ===
        gatilhos = ["oi", "ola", "menu", "ajuda", "ti", "suporte", "nova", "inicio"]
        
        if remetente not in estados_usuarios:
            if "sdb" in texto_lower: pass 
            elif not any(x in texto_lower for x in gatilhos): return "OK", 200
            
            if not "sdb" in texto_lower and texto_lower not in ["1", "2", "3"]:
                 apresentar_menu_principal(remetente)
                 return "OK", 200

        # === COMANDOS ===
        acao = ""
        if texto_lower == "1": acao = "abrir"
        elif texto_lower == "2": acao = "status"
        elif texto_lower == "3": acao = "falar"

        if acao == "abrir":
            reagir(remetente, "📝")
            estados_usuarios[remetente] = {"passo": "aguardando_nome", "dados": {}}
            enviar_msg(remetente, "📝 *INICIANDO REGISTRO*\n\nPor favor, identifique-se com seu *Nome Completo*:")
            return "OK", 200

        if acao == "status":
             reagir(remetente, "🔍")
             enviar_msg(remetente, "🔍 *RASTREIO GLOBAL*\n\nInforme o código do protocolo (Ex: SDB 1234):")
             return "OK", 200
             
        if acao == "falar":
             reagir(remetente, "👤")
             enviar_msg(remetente, "✅ *CONECTANDO...*\nTransferindo conexão para um analista humano.")
             return "OK", 200

        # === FLUXO ===
        if remetente in estados_usuarios:
            passo = estados_usuarios[remetente]["passo"]
            
            if passo == "aguardando_nome":
                reagir(remetente, "👍")
                estados_usuarios[remetente]["dados"]["nome"] = texto
                estados_usuarios[remetente]["passo"] = "aguardando_email"
                enviar_msg(remetente, f"Certo, *{texto}*.\nAgora, informe seu *E-mail Corporativo*:")
            
            elif passo == "aguardando_email":
                reagir(remetente, "📧")
                estados_usuarios[remetente]["dados"]["email"] = texto
                estados_usuarios[remetente]["passo"] = "aguardando_problema"
                enviar_msg(remetente, "📝 *RELATÓRIO DO INCIDENTE*\nDescreva o problema detalhadamente para a equipe:")
            
            elif passo == "aguardando_problema":
                enviar_msg(remetente, "⏳ *PROCESSANDO DADOS...*")
                if enviar_email(estados_usuarios[remetente]["dados"]["nome"], estados_usuarios[remetente]["dados"]["email"], texto):
                    # 👇 AQUI ESTAVA O ERRO, AGORA ESTÁ CORRIGIDO COM \n
                    msg_final = "✅ *PROTOCOLO REGISTRADO*\n```\nSTATUS:  ATIVO\nDESTINO: SUPORTE TÉCNICO\nAVISO:   VERIFIQUE SEU EMAIL\n```"
                    enviar_msg(remetente, msg_final)
                else:
                    reagir(remetente, "❌")
                    enviar_msg(remetente, "⚠️ *FALHA DE SISTEMA*\nServidor de e-mail indisponível. Tente mais tarde.")
                del estados_usuarios[remetente]
            return "OK", 200

        # === SDB ===
        if "sdb" in texto_lower:
            num = "".join([c for c in texto if c.isdigit()])
            chave = f"SDB-{num}"
            reagir(remetente, "🔄")
            enviar_msg(remetente, f"🔄 *BUSCANDO {chave}...*")
            
            d = consultar_jira(chave)
            if d:
                reagir(remetente, "📂")
                # Outra correção preventiva aqui também
                resp = f"📂 *RELATÓRIO TÉCNICO | {chave}*\n━━━━━━━━━━━━━━━━━━\n_{d['resumo']}_\n\n```\nSTATUS: {d['status']}\nRESP:   {d['responsavel']}\nDATA:   {d['data']}\n```\n━━━━━━━━━━━━━━━━━━\n🔗 {d['link']}"
            else:
                reagir(remetente, "🚫")
                resp = f"🚫 *PROTOCOLO {chave} NÃO ENCONTRADO*"
            enviar_msg(remetente, resp)

    except Exception as e: print(e)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
