import time
import os
import schedule
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from repository_mysql import MySqlRepository  # Certifique-se que o nome do arquivo é repository_mysql.py ou mude para model
from service import TrackerService
from notification import TelegramNotifier

# Se o seu arquivo de repositório se chama 'model.py', mude a importação acima para:
# from model import MySqlRepository

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
        
        target_user = os.getenv("TARGET_USER") or "renansantosmbl" # Fallback de segurança
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
    # Roda a cada 4 horas (8 horas pode ser muito tempo para viralização)
    schedule.every(4).hours.do(job)
    
    # Roda uma vez assim que liga para garantir que temos dados
    initial_check = threading.Thread(target=job)
    initial_check.start()
    
    scheduler_thread = threading.Thread(target=run_scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()

@app.get("/")
def home():
    return {"status": "online", "message": "QG Digital Running."}

# --- 2. LÓGICA DA API (DASHBOARD) ---
# Aqui estava o erro. Agora corrigido para usar os métodos do Repository.

@app.get("/dashboard/{username}")
def get_dashboard_data(username: str):
    try:
        # Instancia o repositório
        repo = MySqlRepository()
        
        # A. Busca Perfil
        profile_model = repo.get_profile(username)
        
        if not profile_model:
            return {
                "current_followers": 0,
                "daily_data": [],
                "top_news": []
            }
            
        current_followers = profile_model.follower_count
        
        # B. Busca Histórico (Gráfico)
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

        # C. Busca Posts (Notícias)
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