FROM python:3.10-slim

# --- CONFIGURAÇÃO DO AMBIENTE ---
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV VERSAO_BOT=13.0_NOVA_AI_PRO

# 1. Instalação das bibliotecas
RUN pip install flask requests gunicorn jira

# 2. ESCREVENDO O CÓDIGO PYTHON (BLINDADO)
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
# ⚙️ SUAS CONFIGURAÇÕES (PREENCHA COM ATENÇÃO)
# ======================================================
JIRA_SERVER = "https://zonacriativa.atlassian.net"
JIRA_EMAIL_LOGIN = "ti@pillowtex.com.br"
# Token Jira
JIRA_TOKEN = "ATATT3xFfGF0gTvEQie0CsNToWBMT5sgW-kXIwm5HH4vkEqRFl_M2s1peiP0GtjsoBWe5wk_mnLOsTByWxR_RXQXa3Qxa8-bQj3uTB2WPBC12nwtFW59FD2K5xpGbOjFnLQ7ngz2v69_Vn8XZ5iOmO6O5AlGfQIZE7YnJ99RnRAftvd9RiOQ9tc=F9128AAA"

EMAIL_DESTINO_TOMTICKET = "chamados.ti@pillowtex.com.br"

# 👇👇👇 DADOS DE ENVIO (GMAIL) 👇👇👇
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "seu.email@gmail.com"      # 🔴 SEU GMAIL AQUI
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"  # 🔴 SENHA DE APP AQUI

# Dados da Evolution API
INSTANCE_NAME = "Chatboot"
# Link limpo (sem colchetes)
EVOLUTION_URL = "https://chatboot-evolution-api.iatjve.easypanel.host"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"

# Banner GIF (Futurista)
BANNER_GIF = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYmJmaG14cm14bnh6eGxhYm14bnh6eGxhYm14bnh6eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif"

estados_usuarios = {}

# ======================================================
# 🎨 MOTOR VISUAL N.O.V.A.
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

def apresentar_interface_ai(numero):
    try:
        reagir(numero, "💠")
        
        # 1. GIF de Abertura
        requests.post(f"{EVOLUTION_URL}/message/sendMedia/{INSTANCE_NAME}", 
                      json={"number": numero, "media": BANNER_GIF, "mediatype": "video", "caption": "💠 *SYSTEM ONLINE v13.0*"}, 
                      headers={"apikey": EVOLUTION_KEY})
        
        time.sleep(1.5)
        digitando(numero)

        # 2. Menu Estilo "Card" (Texto Profissional)
        # Usamos \n para quebra de linha segura
        menu = "╔═══════ MENU OPERACIONAL ═══════╗\n║                                ║\n║  [ 1 ] 📝 ABRIR CHAMADO        ║\n║        _Relatar incidente_     ║\n║                                ║\n║  [ 2 ] 🔍 RASTREAR SDB         ║\n║        _Status de processo_    ║\n║                                ║\n║  [ 3 ] 👤 ATENDENTE HUMANO     ║\n║        _Transferir conexão_    ║\n║                                ║\n╚════════════════════════════════╝\n\n_Aguardando comando... Digite o número:_"
        enviar_msg(numero, menu)

    except Exception as e: print(e)

# ======================================================
# 🔧 NÚCLEO LÓGICO
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
        
        corpo = f"RELATÓRIO DE INCIDENTE\n======================\n\nUSUÁRIO: {nome}\nEMAIL: {email_user}\n\nDESCRIÇÃO:\n{problema}\n\n--\nProcessado por N.O.V.A. v13.0"
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
        
        # === COMANDOS DE RESET (Anti-Travamento) ===
        if texto_lower in ["sair", "cancelar", "reset", "menu"]:
            if remetente in estados_usuarios: del estados_usuarios[remetente]
            apresentar_interface_ai(remetente)
            return "OK", 200

        # === GATILHOS INICIAIS ===
        gatilhos = ["oi", "ola", "bom dia", "ajuda", "ti", "suporte", "nova", "inicio"]
        
        if remetente not in estados_usuarios:
            # Se for SDB direto, deixa passar
            if "sdb" in texto_lower: pass 
            # Se não falou palavra chave, ignora
            elif not any(x in texto_lower for x in gatilhos): return "OK", 200
            
            # Se não é escolha de menu, mostra o menu
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
            enviar_msg(remetente, "📝 *PROTOCOLO DE ABERTURA INICIADO*\n\nPara fins de registro, por favor, *identifique-se* (Nome Completo):")
            return "OK", 200

        if acao == "status":
             reagir(remetente, "🔍")
             enviar_msg(remetente, "🔍 *MÓDULO DE RASTREIO ATIVO*\n\nInforme o código do protocolo para busca.\n_Exemplo: SDB 90609_")
             return "OK", 200
             
        if acao == "falar":
             reagir(remetente, "👤")
             enviar_msg(remetente, "✅ *TRANSFERÊNCIA AUTORIZADA*\n\nConectando você a um analista humano.\n_Aguarde, você será atendido em breve._")
             return "OK", 200

        # === FLUXO DE ABERTURA (ETAPAS) ===
        if remetente in estados_usuarios:
            passo = estados_usuarios[remetente]["passo"]
            
            if passo == "aguardando_nome":
                reagir(remetente, "👍")
                estados_usuarios[remetente]["dados"]["nome"] = texto
                estados_usuarios[remetente]["passo"] = "aguardando_email"
                enviar_msg(remetente, f"Registro confirmado: *{texto}*.\n\nAgora, informe seu *E-mail Corporativo* para notificações:")
            
            elif passo == "aguardando_email":
                reagir(remetente, "📧")
                estados_usuarios[remetente]["dados"]["email"] = texto
                estados_usuarios[remetente]["passo"] = "aguardando_problema"
                enviar_msg(remetente, "📝 *DESCRIÇÃO TÉCNICA*\n\nPor favor, relate o problema ou solicitação detalhadamente:")
            
            elif passo == "aguardando_problema":
                enviar_msg(remetente, "⏳ *PROCESSANDO DADOS...*")
                
                sucesso = enviar_email(estados_usuarios[remetente]["dados"]["nome"], estados_usuarios[remetente]["dados"]["email"], texto)
                
                if sucesso:
                    # Mensagem estilo Recibo
                    msg_final = "✅ *CHAMADO REGISTRADO COM SUCESSO*\n\n```\nSTATUS:  EM FILA\nSISTEMA: TOMTICKET\nAVISO:   VERIFIQUE SEU E-MAIL\n```\n\n_O N.O.V.A. agradece o contato. Finalizando sessão._"
                    enviar_msg(remetente, msg_final)
                else:
                    reagir(remetente, "❌")
                    enviar_msg(remetente, "⚠️ *ERRO DE COMUNICAÇÃO*\nServidor de e-mail indisponível. Tente novamente mais tarde.")
                
                # Limpa o usuário para não travar
                del estados_usuarios[remetente]
            return "OK", 200

        # === CONSULTA SDB ===
        if "sdb" in texto_lower:
            num = "".join([c for c in texto if c.isdigit()])
            chave = f"SDB-{num}"
            reagir(remetente, "🔄")
            enviar_msg(remetente, f"🔄 *BUSCANDO DADOS: {chave}...*")
            
            d = consultar_jira(chave)
            if d:
                reagir(remetente, "📂")
                resp = f"📂 *FICHA TÉCNICA | {chave}*\n━━━━━━━━━━━━━━━━━━\n_{d['resumo']}_\n\n```\nSTATUS: {d['status']}\nRESP:   {d['responsavel']}\nDATA:   {d['data']}\n```\n━━━━━━━━━━━━━━━━━━\n🔗 {d['link']}"
            else:
                reagir(remetente, "🚫")
                resp = f"🚫 *PROTOCOLO {chave} INEXISTENTE*"
            enviar_msg(remetente, resp)

    except Exception as e: print(e)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

# 3. Execução (1 Worker para manter memória)
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
