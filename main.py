import time
import os
import schedule 
from dotenv import load_dotenv
from repository_mysql import MySqlRepository
from service import TrackerService
from notification import TelegramNotifier

load_dotenv()

def job():
    print("⏰ Iniciando rotina agendada...")
    try:
        notifier = TelegramNotifier(
            token=os.getenv("TELEGRAM_BOT_TOKEN"), 
            chat_id=os.getenv("TELEGRAM_CHAT_ID")
        )
        repo = MySqlRepository()
        service = TrackerService(
            api_token=os.getenv("APIFY_TOKEN"), 
            repository=repo,
            notifier=notifier
        )
        
        target_user = os.getenv("TARGET_USER")
        print(f"🔒 Verificando: {target_user}")
        service.check_and_notify(target_user)
        print("✅ Verificação concluída.")
        
    except Exception as e:
        print(f"⚠️ Erro crítico: {e}")

def main():
    print("🚀 Sistema de Monitoramento Iniciado")
    
    schedule.every(8).hours.do(job)
    

    job() 

    while True:
        schedule.run_pending()
        time.sleep(60) # Verifica a cada minuto se já está na hora

if __name__ == "__main__":
    main()