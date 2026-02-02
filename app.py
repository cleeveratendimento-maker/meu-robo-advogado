#!/usr/bin/env python3
"""
Robô Advogado - Versão Simplificada
Apenas para testar se o EasyPane consegue buildar
"""

import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Função principal simplificada"""
    print("="*60)
    print("🤖 ROBÔ ADVOGADO - VERSÃO SIMPLIFICADA")
    print("="*60)
    
    # Mostrar variáveis de ambiente
    print("\n📋 CONFIGURAÇÕES:")
    print(f"INSTANCE_NAME: {os.getenv('INSTANCE_NAME', 'consultar')}")
    print(f"EVOLUTION_URL: {os.getenv('EVOLUTION_URL', 'Não configurado')}")
    
    # Testar importações
    print("\n✅ IMPORTAÇÕES:")
    
    try:
        import selenium
        print(f"Selenium: OK (v{selenium.__version__})")
    except ImportError:
        print("Selenium: FALHA")
    
    try:
        import aiohttp
        print(f"Aiohttp: OK (v{aiohttp.__version__})")
    except ImportError:
        print("Aiohttp: FALHA")
    
    # Verificar se está no EasyPane
    print("\n🌐 AMBIENTE:")
    print(f"Sistema: {sys.platform}")
    print(f"Python: {sys.version}")
    
    # Teste de funcionalidade básica
    if len(sys.argv) > 1:
        print(f"\n🔍 Argumento recebido: {sys.argv[1]}")
    else:
        print("\n💡 Dica: Para testar, execute:")
        print('  python app.py "5006623-82.2021.4.02.5103"')
    
    print("\n" + "="*60)
    print("✅ Build do EasyPane bem-sucedida!")
    print("="*60)

if __name__ == "__main__":
    main()
