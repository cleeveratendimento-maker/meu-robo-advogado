#!/usr/bin/env python3
"""
🤖 ROBÔ ADVOGADO - Consulta de Processos
Tudo em um único arquivo: Selenium + Evolution API + EasyPane
"""

import asyncio
import aiohttp
import json
import re
import sys
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# ========== CONFIGURAÇÕES ==========
INSTANCE_NAME = "consultar"
EVOLUTION_URL = "https://oab-evolution-api.iatjve.easypanel.host"
EVOLUTION_KEY = "429683C4C977415CAAFCCE10F7D57E11"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CLASSE DO CONSULTOR ==========
class ProcessoWebConsultor:
    def __init__(self):
        self.base_url = "https://processoweb.com.br/"
        self.driver = None
        
    async def setup_driver(self):
        """Configura o driver do Chrome"""
        options = Options()
        
        # Opções para Docker/EasyPane
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # User Agent real
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        logger.info("✅ Chrome configurado")
        return self
    
    def _limpar_numero_processo(self, numero):
        """Limpa o número do processo"""
        return re.sub(r'[^\d\.\-]', '', numero)
    
    async def consultar_processo(self, numero_processo):
        """Consulta processo no site"""
        numero_limpo = self._limpar_numero_processo(numero_processo)
        dados = {
            "numero_processo": numero_limpo,
            "data_consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "processoweb.com.br"
        }
        
        try:
            logger.info(f"🌐 Acessando {self.base_url}")
            self.driver.get(self.base_url)
            await asyncio.sleep(2)
            
            # Tentar encontrar campo de busca
            campo_encontrado = False
            selectors = [
                "input[type='text']",
                "input[placeholder*='processo']",
                "input[placeholder*='número']",
                "input[name*='numero']",
                "input[name*='processo']",
                "input#numero",
                "input#processo"
            ]
            
            for selector in selectors:
                try:
                    campo = self.driver.find_element(By.CSS_SELECTOR, selector)
                    campo.clear()
                    campo.send_keys(numero_limpo)
                    campo_encontrado = True
                    logger.info(f"🔍 Número inserido: {numero_limpo}")
                    break
                except:
                    continue
            
            if not campo_encontrado:
                # Buscar qualquer input
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.get_attribute("type") in ["text", "search"]:
                        inp.send_keys(numero_limpo)
                        break
            
            # Procurar botão
            btn_selectors = [
                "button[type='submit']",
                "button:contains('Pesquisar')",
                "input[type='submit']",
                "button.pesquisar",
                "button.consultar"
            ]
            
            for selector in btn_selectors:
                try:
                    if "contains" in selector:
                        # Buscar por texto
                        botoes = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in botoes:
                            if "pesquisar" in btn.text.lower() or "consultar" in btn.text.lower():
                                btn.click()
                                break
                    else:
                        btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        btn.click()
                    logger.info("🔘 Botão clicado")
                    break
                except:
                    continue
            
            # Aguardar resultados
            await asyncio.sleep(3)
            
            # Extrair dados da página
            dados.update(self._extrair_dados())
            
            if not any(key in dados for key in ['assunto', 'classe', 'situacao']):
                logger.warning("⚠️ Poucos dados encontrados, tentando método alternativo...")
                dados.update(self._extrair_dados_alternativo())
            
            logger.info(f"✅ Consulta concluída: {len(dados)} campos encontrados")
            
        except Exception as e:
            logger.error(f"❌ Erro: {str(e)}")
            dados["error"] = True
            dados["message"] = str(e)
        
        return dados
    
    def _extrair_dados(self):
        """Extrai dados da página"""
        dados = {}
        
        try:
            # Procurar em tabelas
            tabelas = self.driver.find_elements(By.TAG_NAME, "table")
            for tabela in tabelas:
                linhas = tabela.find_elements(By.TAG_NAME, "tr")
                for linha in linhas:
                    cols = linha.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        chave = cols[0].text.strip().lower()
                        valor = cols[1].text.strip()
                        
                        if "processo" in chave:
                            dados["numero_completo"] = valor
                        elif "assunto" in chave:
                            dados["assunto"] = valor
                        elif "classe" in chave:
                            dados["classe"] = valor
                        elif "juiz" in chave:
                            dados["juiz"] = valor
                        elif "valor" in chave:
                            dados["valor_causa"] = valor
                        elif "situação" in chave:
                            dados["situacao"] = valor
            
            # Procurar em divs
            divs = self.driver.find_elements(By.CSS_SELECTOR, "div")
            for div in divs:
                texto = div.text.strip()
                if len(texto) > 10 and len(texto) < 500:
                    if "Processo:" in texto:
                        dados["numero_completo"] = texto.split("Processo:")[1].split("\n")[0].strip()
                    if "Assunto:" in texto:
                        dados["assunto"] = texto.split("Assunto:")[1].split("\n")[0].strip()
                    if "Valor:" in texto:
                        dados["valor_causa"] = texto.split("Valor:")[1].split("\n")[0].strip()
            
            # Extrair do HTML com regex
            html = self.driver.page_source
            padroes = {
                "numero_completo": r'Processo[:\s]*([\d\.\-/]+)',
                "assunto": r'Assunto[:\s]*(.+?)(?:\n|</)',
                "classe": r'Classe[:\s]*(.+?)(?:\n|</)',
                "valor_causa": r'Valor[:\s]*(R?\$?\s*[\d\.,]+)',
                "situacao": r'Situa[çc][ãa]o[:\s]*(.+?)(?:\n|</)'
            }
            
            for chave, padrao in padroes.items():
                match = re.search(padrao, html, re.IGNORECASE)
                if match and chave not in dados:
                    dados[chave] = match.group(1).strip()
                    
        except Exception as e:
            logger.error(f"Erro extração: {str(e)}")
        
        return dados
    
    def _extrair_dados_alternativo(self):
        """Método alternativo de extração"""
        dados = {}
        
        try:
            # Pegar todo o texto
            texto = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Procurar informações por contexto
            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                linha = linha.strip()
                
                if "Processo" in linha and len(linha) < 100:
                    dados["numero_completo"] = linha.replace("Processo", "").replace(":", "").strip()
                
                if "Assunto" in linha and i + 1 < len(linhas):
                    dados["assunto"] = linhas[i + 1].strip()
                
                if "Valor" in linha and i + 1 < len(linhas):
                    dados["valor_causa"] = linhas[i + 1].strip()
                
                if "Situação" in linha and i + 1 < len(linhas):
                    dados["situacao"] = linhas[i + 1].strip()
                    
        except Exception as e:
            logger.error(f"Erro extração alternativo: {str(e)}")
        
        return dados
    
    async def close(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            logger.info("🚪 Driver fechado")

# ========== CLASSE EVOLUTION API ==========
class EvolutionAPIHandler:
    def __init__(self, session, base_url, api_key, instance_name):
        self.session = session
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        
    async def send_message(self, number, message):
        """Envia mensagem via Evolution API"""
        try:
            # Formatar número
            numero_formatado = self._formatar_numero(number)
            
            # URL da Evolution API
            url = f"{self.base_url}/message/sendText/{self.instance_name}"
            
            payload = {
                "number": numero_formatado,
                "text": message
            }
            
            headers = {
                "Content-Type": "application/json",
                "apikey": self.api_key
            }
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status in [200, 201]:
                    logger.info(f"✅ Mensagem enviada para {numero_formatado}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Erro API: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Erro envio: {str(e)}")
            return False
    
    def _formatar_numero(self, number):
        """Formata número para WhatsApp"""
        # Remover tudo que não é número
        numeros = re.sub(r'\D', '', number)
        
        # Adicionar 55 se for Brasil
        if numeros and not numeros.startswith('55'):
            numeros = '55' + numeros
            
        return numeros + '@c.us'
    
    async def send_process_info(self, numero_whatsapp, processo_data):
        """Envia informações do processo formatadas"""
        if "error" in processo_data:
            mensagem = self._criar_mensagem_erro(processo_data)
        else:
            mensagem = self._criar_mensagem_sucesso(processo_data)
        
        return await self.send_message(numero_whatsapp, mensagem)
    
    def _criar_mensagem_erro(self, dados):
        """Cria mensagem de erro"""
        return f"""❌ *ERRO NA CONSULTA*

*Processo:* {dados.get('numero_processo', 'N/A')}
*Erro:* {dados.get('message', 'Desconhecido')}

⏰ *Data:* {dados.get('data_consulta', 'N/A')}
🤖 *Robô Advogado*"""
    
    def _criar_mensagem_sucesso(self, dados):
        """Cria mensagem de sucesso"""
        linhas = ["✅ *CONSULTA DE PROCESSO*", ""]
        
        if dados.get('numero_completo'):
            linhas.append(f"*Processo:* {dados['numero_completo']}")
        else:
            linhas.append(f"*Processo:* {dados.get('numero_processo', 'N/A')}")
        
        if dados.get('assunto'):
            linhas.append(f"*Assunto:* {dados['assunto']}")
        
        if dados.get('classe'):
            linhas.append(f"*Classe:* {dados['classe']}")
        
        if dados.get('valor_causa'):
            linhas.append(f"*Valor:* {dados['valor_causa']}")
        
        if dados.get('situacao'):
            linhas.append(f"*Situação:* {dados['situacao']}")
        
        if dados.get('juiz'):
            linhas.append(f"*Juiz:* {dados['juiz']}")
        
        linhas.extend([
            "",
            f"*Data Consulta:* {dados.get('data_consulta', 'N/A')}",
            f"*Fonte:* {dados.get('fonte', 'processoweb.com.br')}",
            "",
            "⚖️ *Robô Advogado*",
            "_Consulta automática de processos_"
        ])
        
        return "\n".join(linhas)

# ========== ROBÔ PRINCIPAL ==========
class RoboAdvogado:
    def __init__(self):
        self.session = None
        self.evolution = None
        self.consultor = None
        
    async def init(self):
        """Inicializa o robô"""
        logger.info("🚀 Inicializando Robô Advogado...")
        
        # Criar session HTTP
        self.session = aiohttp.ClientSession()
        
        # Configurar Evolution API
        self.evolution = EvolutionAPIHandler(
            session=self.session,
            base_url=EVOLUTION_URL,
            api_key=EVOLUTION_KEY,
            instance_name=INSTANCE_NAME
        )
        
        # Configurar consultor
        self.consultor = ProcessoWebConsultor()
        await self.consultor.setup_driver()
        
        logger.info("✅ Robô pronto para consultas!")
        return self
    
    async def consultar(self, numero_processo, numero_whatsapp=None):
        """Faz consulta completa"""
        try:
            logger.info(f"🔍 Consultando: {numero_processo}")
            
            # Consultar processo
            dados = await self.consultor.consultar_processo(numero_processo)
            
            # Enviar WhatsApp se solicitado
            if numero_whatsapp:
                logger.info(f"📤 Enviando para WhatsApp: {numero_whatsapp}")
                sucesso = await self.evolution.send_process_info(numero_whatsapp, dados)
                dados["whatsapp_enviado"] = sucesso
                dados["whatsapp_numero"] = numero_whatsapp
            
            return dados
            
        except Exception as e:
            logger.error(f"❌ Erro: {str(e)}")
            return {
                "error": True,
                "message": str(e),
                "numero_processo": numero_processo
            }
    
    async def close(self):
        """Fecha tudo"""
        if self.consultor:
            await self.consultor.close()
        if self.session:
            await self.session.close()
        logger.info("👋 Robô finalizado")

# ========== FUNÇÕES PRINCIPAIS ==========
async def consulta_rapida(numero_processo):
    """Consulta simples"""
    robo = RoboAdvogado()
    try:
        await robo.init()
        resultado = await robo.consultar(numero_processo)
        
        print("\n" + "="*60)
        print("🤖 RESULTADO DA CONSULTA")
        print("="*60)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print("="*60)
        
        return resultado
    finally:
        await robo.close()

async def consulta_com_whatsapp(numero_processo, numero_whatsapp):
    """Consulta e envia para WhatsApp"""
    robo = RoboAdvogado()
    try:
        await robo.init()
        resultado = await robo.consultar(numero_processo, numero_whatsapp)
        
        print("\n✅ Consulta realizada!")
        print(f"📤 WhatsApp: {resultado.get('whatsapp_enviado', False)}")
        print(f"📄 Dados: {json.dumps(resultado, indent=2, ensure_ascii=False)}")
        
        return resultado
    finally:
        await robo.close()

# ========== API WEB (OPCIONAL) ==========
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="Robô Advogado API", version="1.0")

robo_global = None

@app.on_event("startup")
async def startup_event():
    """Inicializa o robô ao iniciar a API"""
    global robo_global
    robo_global = RoboAdvogado()
    await robo_global.init()

@app.on_event("shutdown")
async def shutdown_event():
    """Fecha o robô ao desligar a API"""
    global robo_global
    if robo_global:
        await robo_global.close()

@app.get("/")
async def root():
    return {"status": "online", "service": "Robô Advogado"}

@app.get("/consultar/{numero_processo}")
async def consultar_api(numero_processo: str, whatsapp: str = None):
    """Endpoint API para consulta"""
    try:
        if robo_global is None:
            raise HTTPException(status_code=500, detail="Robô não inicializado")
        
        resultado = await robo_global.consultar(numero_processo, whatsapp)
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ========== MAIN ==========
def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("""
🤖 ROBÔ ADVOGADO - CONSULTA DE PROCESSOS

Uso:
  python app.py <numero_processo> [numero_whatsapp]
  
Exemplos:
  python app.py "5006623-82.2021.4.02.5103"
  python app.py "5006623-82.2021.4.02.5103" "5522999155366"

Para iniciar API web:
  python app.py --api
        """)
        sys.exit(1)
    
    # Verificar se deve iniciar API
    if sys.argv[1] == "--api":
        print("🌐 Iniciando API web na porta 8080...")
        uvicorn.run(app, host="0.0.0.0", port=8080)
        return
    
    # Consulta normal
    numero_processo = sys.argv[1]
    numero_whatsapp = sys.argv[2] if len(sys.argv) > 2 else None
    
    if numero_whatsapp:
        asyncio.run(consulta_com_whatsapp(numero_processo, numero_whatsapp))
    else:
        asyncio.run(consulta_rapida(numero_processo))

if __name__ == "__main__":
    main()
