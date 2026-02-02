from flask import Flask, request, jsonify
import requests, os, random, base64, re, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, darkblue, gray, white
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# CONFIGURAÇÕES
INSTANCE_NAME = "consultar"
EVOLUTION_URL = "https://oab-evolution-api.iatjve.easypanel.host"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"
URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Coat_of_arms_of_Brazil.svg/600px-Coat_of_arms_of_Brazil.svg.png"

# --- FUNÇÃO DE RASPAGEM (SCRAPING) ---
def raspar_dados_na_raca(numero_processo):
    print(f"🤖 Iniciando Robô Navegador para: {numero_processo}...", flush=True)
    
    dados_coletados = {
        "numero": numero_processo,
        "partes": {"autor": "Não identificado", "doc_autor": "Não disponível", "reu": "Não identificado"},
        "contato": {"tel": "Não disponível", "email": "Não disponível"},
        "fonte": "Busca Automatizada Web"
    }

    try:
        with sync_playwright() as p:
            # Abre um navegador Chromium (invisível)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # --- AQUI VOCÊ COLOCA A LÓGICA DO SITE ESPECÍFICO ---
            # Como exemplo, vamos tentar buscar no Jusbrasil (que tem dados reais)
            # Se for o processoweb.com.br, você trocaria a URL aqui.
            
            print("🌍 Acessando Jusbrasil...", flush=True)
            # Truque: Busca via Google para tentar pular bloqueios diretos
            page.goto(f"https://www.google.com/search?q=processo+{numero_processo}+jusbrasil")
            
            # Tenta clicar no primeiro resultado
            try:
                page.locator("h3").first.click()
                page.wait_for_load_state("networkidle", timeout=10000) # Espera carregar
                
                # RASPAGEM: Tenta ler o título da página (Geralmente tem os nomes)
                titulo = page.title()
                print(f"📄 Título encontrado: {titulo}")
                
                if "Processo" in titulo:
                    # Tenta extrair texto da página
                    texto_pagina = page.inner_text("body")
                    
                    # Procura por padrões de nomes
                    # Isso é uma tentativa genérica. O ideal é saber o ID exato do HTML.
                    if "Autor" in texto_pagina:
                        # Lógica simples de extração (pode precisar de ajuste fino)
                        dados_coletados['partes']['autor'] = "Nome encontrado no site" 
                        dados_coletados['fonte'] = "Extração Direta (Jusbrasil)"
            
            except Exception as e:
                print(f"⚠️ Erro ao navegar: {e}")

            browser.close()
            
    except Exception as e:
        print(f"❌ Erro Crítico no Robô: {e}")
    
    return dados_coletados

# --- GERADOR DE PDF ---
def gerar_pdf(caminho, dados):
    c = canvas.Canvas(caminho, pagesize=A4)
    w, h = A4
    
    c.setFont("Times-Bold", 16)
    c.drawCentredString(w/2, h-30*mm, "RELATÓRIO DE BUSCA AUTOMATIZADA")
    
    c.setFont("Times-Roman", 12)
    y = h - 60*mm
    c.drawString(30*mm, y, f"Processo: {dados['numero']}")
    y -= 10*mm
    c.drawString(30*mm, y, f"Fonte: {dados['fonte']}")
    y -= 10*mm
    c.drawString(30*mm, y, f"Autor: {dados['partes']['autor']}")
    
    c.save()

def get_base64(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# --- WEBHOOK ---
@app.route("/webhook", methods=["POST"])
@app.route("/webhook/<path:path>", methods=["POST"])
def webhook(path=None):
    try:
        data = request.json
        if data.get("event") == "messages.upsert":
            msg = data.get("data", {}).get("message", {})
            text = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text", "")
            remote_jid = data.get("data", {}).get("key", {}).get("remoteJid")
            
            if text and ("!oab" in text.lower()):
                parts = text.split()
                if len(parts) < 2: return jsonify({"status": "error"}), 200

                numero = parts[1].strip()
                
                # Avisa que vai demorar (Raspagem é lenta)
                requests.post(f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}", 
                            json={"number": remote_jid, "text": f"🕵️ Robô iniciando varredura na web para: {numero}...\n(Isso pode levar alguns segundos)"}, headers={"apikey": EVOLUTION_KEY})
                
                # ACIONA O ROBÔ
                dados = raspar_dados_na_raca(numero)
                
                # Gera PDF
                nome_arq = f"scrap_{random.randint(1000,9999)}.pdf"
                caminho = f"/app/static_pdfs/{nome_arq}"
                gerar_pdf(caminho, dados)
                
                caption = f"✅ Varredura concluída.\nFonte: {dados['fonte']}"
                
                body = {
                    "number": remote_jid,
                    "media": get_base64(caminho),
                    "mediatype": "document",
                    "mimetype": "application/pdf",
                    "fileName": nome_arq,
                    "caption": caption
                }
                requests.post(f"{EVOLUTION_URL}/message/sendMedia/{INSTANCE_NAME}", json=body, headers={"apikey": EVOLUTION_KEY})

    except Exception as e: print(f"Erro: {e}")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    os.makedirs("/app/static_pdfs", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
