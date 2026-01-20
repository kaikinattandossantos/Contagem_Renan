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
from pathlib import Path
from dotenv import load_dotenv

# --- DIAGNÓSTICO FORÇADO DO .ENV ---
current_dir = Path(__file__).parent.absolute()
env_path = current_dir / ".env"

print(f"--- VERIFICAÇÃO DE AMBIENTE ---")
print(f"📂 Pasta do script: {current_dir}")
print(f"📄 Procurando .env em: {env_path}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ Ficheiro .env encontrado!")
else:
    print("❌ ERRO: Ficheiro .env NÃO ENCONTRADO!")
    print("Certifique-se que o arquivo se chama exatamente '.env' e não '.env.txt'")
print(f"-------------------------------")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. LÓGICA DO ROBÔ (SCHEDULER) ---
# --- 1. LÓGICA DO ROBÔ (SCHEDULER) ---
def job():
    env_token = os.getenv("TELEGRAM_BOT_TOKEN")
    env_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print(f"🕵️ DEBUG: O chat_id carregado é '{env_chat_id}'")
    print(f"⏰ Executando Job: {time.strftime('%H:%M:%S')}")
    
    try:
        # 1. Configura o Repositório e o Notificador
        repo = MySqlRepository()
        notifier = TelegramNotifier(env_token, env_chat_id)
        
        # 2. Pega o Token do Apify (certifique-se que o nome no .env é este)
        apify_token = os.getenv("APIFY_API_TOKEN")

        # 3. CRIA O SERVIÇO COM OS 3 ARGUMENTOS NA ORDEM CORRETA
        # A sua classe [Imagem d6e9a0] pede: api_token, repository, notifier
        service = TrackerService(apify_token, repo, notifier)
        
        # 4. Executa a tarefa
        service.check_and_notify('renansantosmbl')
        
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
    repo = MySqlRepository()
    try:
        # 1. Busca dados atuais do perfil
        current = repo.get_profile(username)
        
        # --- AQUI ESTÁ A ALTERAÇÃO PRECISA ---
        # Se 'current' for None (perfil não existe no banco), define como 0
        if current is None:
            current_followers = 0
        else:
            # Garante que follower_count seja um número
            current_followers = current.follower_count if current.follower_count is not None else 0
        # -------------------------------------

        # 2. Histórico (Gráfico)
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
    job()
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Iniciando na porta {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)