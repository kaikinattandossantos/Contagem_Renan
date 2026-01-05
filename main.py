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

# --- 1. LÓGICA DO ROBÔ (SCHEDULER) ---
def job():
    print(f"🕵️ VERDADE NUA E CRUA: O chat_id carregado é '{env_chat_id}'")
    print(f"⏰ Executando Job: {time.strftime('%H:%M:%S')}")
    try:
        # --- DEBUG: O CÓDIGO VAI CONFESSAR AGORA ---
        env_token = os.getenv("TELEGRAM_BOT_TOKEN")
        env_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        print(f"🕵️ DEBUG ENV TOKEN: {env_token[:5]}... (oculto)")
        print(f"🕵️ DEBUG ENV CHAT_ID: '{env_chat_id}'") # As aspas mostram se tem espaço em branco
        # -------------------------------------------

        notifier = TelegramNotifier(
            token=env_token, 
            chat_id=env_chat_id
        )
        
        # Teste rápido: O ID dentro da classe bate com o do ENV?
        if notifier.chat_id != env_chat_id:
             print(f"❌ ERRO GRAVE: O Notifier recebeu '{notifier.chat_id}' mas o env era '{env_chat_id}'")

        repo = MySqlRepository()
        service = TrackerService(
            api_token=os.getenv("APIFY_TOKEN"), 
            repository=repo,
            notifier=notifier
        )
        
        target_user = os.getenv("TARGET_USER") or "renansantosmbl"
        if target_user:
            service.check_and_notify(target_user)
            print("✅ Sucesso.")
            
    except Exception as e:
        print(f"⚠️ Erro no Job: {e}")

def run_scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.on_event("startup")
def startup_event():
    schedule.every(4).hours.do(job)
    
    initial_check = threading.Thread(target=job)
    initial_check.start()
    
    scheduler_thread = threading.Thread(target=run_scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()

@app.get("/")
def home():
    return {"status": "online", "message": "QG Digital Running."}



@app.get("/dashboard/{username}")
def get_dashboard_data(username: str):
    try:
        repo = MySqlRepository()
        
        profile_model = repo.get_profile(username)
        
        if not profile_model:
            return {
                "current_followers": 0,
                "daily_data": [],
                "top_news": []
            }
            
        current_followers = profile_model.follower_count
        
        raw_history = repo.get_daily_history(username)
        processed_history = []
        
        if raw_history:
            for i in range(len(raw_history)):
                item = raw_history[i]
                prev = raw_history[i-1]['followers'] if i > 0 else item['followers']
                processed_history.append({
                    "date": item['date'],
                    "followers": item['followers'],
                    "growth": item['followers'] - prev
                })

        raw_posts = repo.get_recent_posts(username)
        formatted_news = []
        
        for i, post in enumerate(raw_posts):
            caption = post['caption'] if post.get('caption') else "Sem legenda"
            title = (caption[:50] + '...') if len(caption) > 50 else caption
            
            formatted_news.append({
                "id": i,
                "title": title,
                "date": post['date_formatted'],
                "impact": post['likes_count'],
                "description": caption,
                "url": post['url']
            })

        return {
            "current_followers": current_followers,
            "daily_data": processed_history,
            "top_news": formatted_news
        }

    except Exception as e:
        print(f"ERRO API: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Iniciando na porta {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)