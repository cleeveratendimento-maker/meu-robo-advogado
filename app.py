# -*- coding: utf-8 -*-
from flask import Flask, request
from jira import JIRA
import requests
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ======================================================
# 🔐 VARIÁVEIS DE AMBIENTE (CONFIGURAR NO EASYPANEL)
# ======================================================
estados_usuarios = {}

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

# ======================================================
# 🧠 CONTROLE DE ESTADO / SESSÃO
# ======================================================

estados_usuarios = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutos

# ======================================================
# 📤 FUNÇÕES DE ENVIO
# ======================================================

def enviar_texto(numero, texto):
    requests.post(
        f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}",
        json={"number": numero, "text": texto},
        headers={"apikey": EVOLUTION_KEY}
    )

def apresentar_menu(numero):
    texto = (
        "╔════════════════════╗\n"
        "   💠 SYSTEM ONLINE v17.1\n"
        "╚════════════════════╝\n\n"
        "👋 Olá! Sou a *N.O.V.A* 🤖\n"
        "Como posso te ajudar hoje?\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 *1* — Abrir Chamado\n"
        "🔍 *2* — Rastrear SDB\n"
        "👤 *3* — Falar com Humano\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👉 *Digite o número da opção*"
    )
    enviar_texto(numero, texto)

# ======================================================
# 🔧 FUNÇÕES DE NEGÓCIO
# ======================================================

def consultar_jira(ticket):
    try:
        jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL_LOGIN, JIRA_TOKEN))
        issue = jira.issue(ticket)
        return (
            f"📂 *{ticket}*\n"
            f"Status: {issue.fields.status.name.upper()}\n"
            f"Responsável: {issue.fields.assignee.displayName if issue.fields.assignee else 'Automático'}"
        )
    except:
        return None

def enviar_email(nome, email_user, problema):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_DESTINO_TOMTICKET
        msg["Subject"] = f"[N.O.V.A] Chamado TI - {nome}"
        msg.add_header("Reply-To", email_user)

        corpo = f"USUÁRIO: {nome}\nEMAIL: {email_user}\n\nPROBLEMA:\n{problema}"
        msg.attach(MIMEText(corpo, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, EMAIL_DESTINO_TOMTICKET, msg.as_string())
        server.quit()
        return True
    except:
        return False

# ======================================================
# 🌐 WEBHOOK PRINCIPAL
# ======================================================

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    if not data or data.get("event") != "messages.upsert":
        return "OK", 200

    msg = data.get("data", {}).get("message", {})
    remetente = data.get("data", {}).get("key", {}).get("remoteJid")

    texto = (
        msg.get("conversation") or
        msg.get("extendedTextMessage", {}).get("text") or
        msg.get("buttonsResponseMessage", {}).get("selectedButtonId") or
        ""
    )

    if not texto or not remetente:
        return "OK", 200

    texto = texto.strip()
    texto_lower = texto.lower()
    agora = time.time()

    # ==================================================
    # ⏱️ CONTROLE DE TIMEOUT DE SESSÃO
    # ==================================================

    if remetente in estados_usuarios:
        sessao = estados_usuarios[remetente]

        # Sessão expirada
        if agora - sessao.get("ultimo_contato", agora) > SESSION_TIMEOUT:
            del estados_usuarios[remetente]
            apresentar_menu(remetente)
            return "OK", 200

        # Atualiza último contato
        sessao["ultimo_contato"] = agora

    # ==================================================
    # 🔄 RESET MANUAL
    # ==================================================

    if texto_lower in ["menu", "sair", "cancelar", "reset"]:
        estados_usuarios.pop(remetente, None)
        apresentar_menu(remetente)
        return "OK", 200

    # ==================================================
    # 🚫 NÃO INTERROMPE ATENDIMENTO
    # ==================================================

    if (
        remetente in estados_usuarios and
        estados_usuarios[remetente].get("modo") == "atendimento"
    ):
        return "OK", 200

    # ==================================================
    # 🧩 FLUXO DE ABERTURA DE CHAMADO
    # ==================================================

    if remetente in estados_usuarios:
        passo = estados_usuarios[remetente].get("passo")

        if passo == "nome":
            estados_usuarios[remetente]["dados"]["nome"] = texto
            estados_usuarios[remetente]["passo"] = "email"
            enviar_texto(remetente, "📧 Informe seu *e-mail*:")
            return "OK", 200

        if passo == "email":
            estados_usuarios[remetente]["dados"]["email"] = texto
            estados_usuarios[remetente]["passo"] = "problema"
            enviar_texto(remetente, "📝 Descreva o *problema*:")
            return "OK", 200

        if passo == "problema":
            dados = estados_usuarios[remetente]["dados"]
            ok = enviar_email(dados["nome"], dados["email"], texto)
            enviar_texto(
                remetente,
                "✅ Chamado criado com sucesso! Nossa equipe entrará em contato."
                if ok else
                "❌ Erro ao criar o chamado. Tente novamente."
            )
            del estados_usuarios[remetente]
            return "OK", 200

    # ==================================================
    # 📌 MENU PRINCIPAL
    # ==================================================

    if texto_lower == "1":
        estados_usuarios[remetente] = {
            "modo": "atendimento",
            "passo": "nome",
            "dados": {},
            "ultimo_contato": agora
        }
        enviar_texto(remetente, "📝 Digite seu *nome completo*:")
        return "OK", 200

    if texto_lower == "2":
        enviar_texto(remetente, "🔍 Digite o SDB (ex: SDB-12345):")
        return "OK", 200

    if texto_lower == "3":
        estados_usuarios[remetente] = {
            "modo": "atendimento",
            "ultimo_contato": agora
        }
        enviar_texto(
            remetente,
            "👤 Encaminhando para atendimento humano...\n"
            "Pode escrever normalmente, estou em silêncio 🙂"
        )
        return "OK", 200

    # ==================================================
    # 🔍 CONSULTA SDB
    # ==================================================

    if "sdb" in texto_lower:
        num = "".join(c for c in texto if c.isdigit())
        resposta = consultar_jira(f"SDB-{num}")
        enviar_texto(
            remetente,
            resposta if resposta else "🚫 Chamado não encontrado."
        )
        return "OK", 200

    # ==================================================
    # 📢 FALLBACK
    # ==================================================

    apresentar_menu(remetente)
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
