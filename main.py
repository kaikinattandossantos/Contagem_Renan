import time
import os
from dotenv import load_dotenv  
from repository import JsonRepository
from service import TrackerService

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
TARGET_USER = os.getenv("TARGET_USER")

def main():

    if not APIFY_TOKEN:
        print("❌ ERRO CRÍTICO: Token do Apify não encontrado no arquivo .env")
        return
    
    if not TARGET_USER:
        print("❌ ERRO: Usuário alvo não definido no arquivo .env")
        return

    print(f"🔒 Iniciando monitoramento seguro para: {TARGET_USER}")
    
    repo = JsonRepository()
    service = TrackerService(APIFY_TOKEN, repo)

    while True:
        try:
            service.check_and_notify(TARGET_USER)
        except Exception as e:
            print(f"⚠️ Erro na execução: {e}")
        
        print("⏳ Aguardando 15 minutos...")
        time.sleep(900) 

if __name__ == "__main__":
    main()