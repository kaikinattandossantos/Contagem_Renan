import time
import os
import schedule
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from repository_mysql import MySqlRepository
from service import TrackerService
from notification import TelegramNotifier

load_dotenv()

# --- 1. CONFIGURAÇÃO DA API (Para o Vercel acessar) ---
app = FastAPI()

# Permite que o Vercel acesse sua API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. LÓGICA DO ROBÔ (O Trabalho Pesado) ---
def job():
    print(f"⏰ [Agendamento] Iniciando verificação: {time.strftime('%H:%M:%S')}")
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
            print("✅ Verificação concluída.")
    except Exception as e:
        print(f"⚠️ Erro no Job: {e}")

# Função que roda o relógio do schedule em loop infinito
def run_scheduler_loop():
    print("🔄 Loop do agendador iniciado em segundo plano...")
    while True:
        schedule.run_pending()
        time.sleep(60)

# --- 3. CICLO DE VIDA (Inicia o Robô junto com a API) ---
@app.on_event("startup")
def startup_event():
    print("🚀 API Iniciada. Ligando motores do agendamento...")
    
    # Configura o agendamento
    schedule.every(8).hours.do(job)
    
    # Executa uma vez na hora que liga (pra você ver funcionando)
    # Use uma Thread separada para não travar o boot da API
    initial_check = threading.Thread(target=job)
    initial_check.start()
    
    # Inicia o loop do schedule em UMA OUTRA THREAD SEPARADA
    # Isso permite que o Uvicorn rode o site na thread principal
    scheduler_thread = threading.Thread(target=run_scheduler_loop)
    scheduler_thread.daemon = True # Morre se a API desligar
    scheduler_thread.start()

# --- 4. ROTAS DA API (Para o seu Dashboard no Vercel) ---
@app.get("/")
def home():
    return {"status": "online", "message": "O Robô está trabalhando em segundo plano."}

@app.get("/dashboard/{username}")
def get_dashboard_data(username: str):
    # Aqui vai aquela lógica de leitura do banco que você já tinha
    # Vou resumir para conectar no seu repository existente
    try:
        repo = MySqlRepository()
        conn = repo.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Pega dados atuais
        cursor.execute("SELECT follower_count FROM profiles WHERE username = %s", (username,))
        current = cursor.fetchone()
        
        # (Adicione aqui o resto das suas queries de histórico/posts se precisar)
        
        cursor.close()
        conn.close()
        
        return {
            "username": username,
            "followers": current['follower_count'] if current else 0
        }
    except Exception as e:
        return {"error": str(e)}