import time
import os
import schedule
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from repository_mysql import MySqlRepository
from service import TrackerService
from notification import TelegramNotifier

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def job():
    print(f"⏰ Executando Job: {time.strftime('%H:%M:%S')}")
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
        if target_user:
            service.check_and_notify(target_user)
            print("✅ Sucesso.")
    except Exception as e:
        print(f"⚠️ Erro: {e}")

def run_scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.on_event("startup")
def startup_event():
    schedule.every(8).hours.do(job)
    
    initial_check = threading.Thread(target=job)
    initial_check.start()
    
    scheduler_thread = threading.Thread(target=run_scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()

@app.get("/")
def home():
    return {"status": "online", "message": "System running."}

@app.get("/dashboard/{username}")
def get_dashboard_data(username: str):
    try:
        repo = MySqlRepository()
        conn = repo.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT follower_count FROM profiles WHERE username = %s", (username,))
        current = cursor.fetchone()
        
        
        cursor.close()
        conn.close()
        
        return {
            "username": username,
            "followers": current['follower_count'] if current else 0
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Iniciando na porta {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)