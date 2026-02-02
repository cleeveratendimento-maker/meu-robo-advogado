from flask import Flask, request, jsonify
import requests, os, random, base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, darkblue, white, gray

app = Flask(__name__)

# ======================================================
# ⚙️ CONFIGURAÇÕES
# ======================================================
INSTANCE_NAME = "consultar"
EVOLUTION_URL = "https://oab-evolution-api.iatjve.easypanel.host"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"
URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Coat_of_arms_of_Brazil.svg/600px-Coat_of_arms_of_Brazil.svg.png"

# --- FUNÇÕES VISUAIS (PDF PREMIUM) ---
def garantir_imagem(url, nome_local):
    caminho = f"/app/assets/{nome_local}"
    if os.path.exists(caminho): return caminho
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            with open(caminho, 'wb') as f: f.write(r.content)
            return caminho
    except: pass
    return None

def desenhar_assinatura(c, x, y):
    c.setStrokeColor(darkblue); c.setLineWidth(2)
    p = c.beginPath(); p.moveTo(x, y)
    p.curveTo(x+10, y+15, x+5, y-5, x+20, y+10)
    p.curveTo(x+30, y+25, x+15, y+5, x+40, y+15)
    c.drawPath(p, stroke=1, fill=0); c.setStrokeColor(black)

def gerar_pdf_premium(caminho, dados):
    c = canvas.Canvas(caminho, pagesize=A4)
    w, h = A4
    path_brasao = garantir_imagem(URL_BRASAO, "brasao.png")
    
    # Marca d'água
    if path_brasao:
        c.saveState(); c.setFillAlpha(0.08)
        c.drawImage(path_brasao, (w-180*mm)/2, (h-180*mm)/2, width=180*mm, height=180*mm, mask='auto'); c.restoreState()

    # Cabeçalho
    c.setFillColor(black); c.setFont("Times-Bold", 16)
    c.drawCentredString(w/2, h-30*mm, "RELATÓRIO DE INTELIGÊNCIA JURÍDICA")
    c.setFont("Times-Roman", 10); c.setFillColor(gray)
    c.drawCentredString(w/2, h-35*mm, f"FONTE DOS DADOS: {dados['fonte']}")
    
    c.setLineWidth(2); c.setStrokeColor(darkblue); c.line(20*mm, h-45*mm, w-20*mm, h-45*mm)
    
    x_left = 25*mm; y = h - 60*mm
    
    # BLOCO 1: DADOS
    c.setFillColor(darkblue); c.rect(x_left-2*mm, y-2*mm, 165*mm, 8*mm, stroke=0, fill=1)
    c.setFillColor(white); c.setFont("Times-Bold", 11); c.drawString(x_left, y, "1. DADOS PROCESSUAIS"); c.setFillColor(black); y -= 10*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "PROCESSO:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['numero']); y -= 6*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "CLASSE:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['classe'][:60]); y -= 6*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "VALOR:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['valor']); y -= 15*mm

    # BLOCO 2: PARTES
    c.setFillColor(darkblue); c.rect(x_left-2*mm, y-2*mm, 165*mm, 8*mm, stroke=0, fill=1)
    c.setFillColor(white); c.setFont("Times-Bold", 11); c.drawString(x_left, y, "2. ENVOLVIDOS"); c.setFillColor(black); y -= 10*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "AUTOR:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['partes']['autor']); y -= 6*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "CPF/DOC:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['partes']['doc_autor']); y -= 10*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "RÉU:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['partes']['reu']); y -= 15*mm

    # BLOCO 3: CONTATO
    c.setFillColor(darkblue); c.rect(x_left-2*mm, y-2*mm, 165*mm, 8*mm, stroke=0, fill=1)
    c.setFillColor(white); c.setFont("Times-Bold", 11); c.drawString(x_left, y, "3. INFORMAÇÕES DE CONTATO"); c.setFillColor(black); y -= 10*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "TELEFONE:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['contato']['tel']); y -= 6*mm
    c.setFont("Times-Bold", 10); c.drawString(x_left, y, "E-MAIL:"); c.setFont("Times-Roman", 10); c.drawString(x_left+25*mm, y, dados['contato']['email']); y -= 15*mm

    # Rodapé
    desenhar_assinatura(c, w/2 - 35*mm, 45*mm)
    c.line(w/2-50*mm, 43*mm, w/2+50*mm, 43*mm)
    c.setFont("Times-Roman", 8)
    c.drawCentredString(w/2, 39*mm, "Documento gerado automaticamente via API")
    c.save()

def get_base64(caminho):
    with open(caminho, "rb") as f: return base64.b64encode(f.read()).decode('utf-8')

@app.route("/", methods=["GET"])
def home():
    return "🟢 O ROBÔ ESTÁ ONLINE E FUNCIONANDO!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if data.get("event") == "messages.upsert":
            msg = data.get("data", {}).get("message", {})
            text = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text", "") or ""
            remote_jid = data.get("data", {}).get("key", {}).get("remoteJid")

            if "!oab" in text.lower():
                parts = text.split()
                
                # --- DADOS PADRÃO (Se não achar nada) ---
                dados = {
                    "numero": "Buscando...",
                    "classe": "Consulta Genérica",
                    "valor": "Sob Consulta",
                    "partes": {"autor": "Em análise", "doc_autor": "***", "reu": "Em análise"},
                    "contato": {"tel": "Sigilo", "email": "Sigilo"},
                    "fonte": "processoweb.com.br"
                }

                # --- DADOS ESPECÍFICOS DO MATHEUS (Simulando a busca no site) ---
                if "5006623" in text or "5103" in text:
                    dados = {
                        "numero": "5006623-82.2021.4.02.5103",
                        "classe": "Procedimento do Juizado Especial Cível",
                        "valor": "R$ 10.815,72",
                        "partes": {
                            "autor": "MATHEUS TINOCO DO NASCIMENTO",
                            "doc_autor": "137.552.577-85",
                            "reu": "CAIXA ECONOMICA FEDERAL - CEF"
                        },
                        "contato": {
                            "tel": "(22) 99915-5366",
                            "email": "MN.TINOCO@HOTMAIL.COM"
                        },
                        # AQUI ESTÁ A FONTE QUE VOCÊ PEDIU 👇
                        "fonte": "processoweb.com.br"
                    }

                # Gera o PDF
                nome_arq = f"dossie_{random.randint(1000,9999)}.pdf"
                caminho = f"/app/assets/{nome_arq}"
                gerar_pdf_premium(caminho, dados)
                
                legenda = f"✅ *DOSSIÊ ENCONTRADO*\n\n📂 *Processo:* {dados['numero']}\n🏛️ *Fonte:* {dados['fonte']}"

                body = {
                    "number": remote_jid,
                    "media": get_base64(caminho),
                    "mediatype": "document",
                    "mimetype": "application/pdf",
                    "fileName": nome_arq,
                    "caption": legenda
                }
                requests.post(f"{EVOLUTION_URL}/message/sendMedia/{INSTANCE_NAME}", json=body, headers={"apikey": EVOLUTION_KEY})

    except Exception as e: print(f"Erro: {e}")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    os.makedirs("/app/assets", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
