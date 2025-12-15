import time
import os
from dotenv import load_dotenv
from repository_mysql import MySqlRepository
from service import TrackerService
from notification import TelegramNotifier

load_dotenv()

def main():
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
    print(f"🔒 Iniciando monitoramento para: {target_user}")

    while True:
        try:
            service.check_and_notify(target_user)
            print("✅ Verificação concluída com sucesso.")
        except Exception as e:
            error_msg = f"⚠️ Erro na execução: {str(e)}"
            print(error_msg)
            notifier.send(error_msg)
        
        time.sleep(1800)

if __name__ == "__main__":
    main()