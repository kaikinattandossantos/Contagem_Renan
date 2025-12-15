# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Permite que o Frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

@app.get("/dashboard/{username}")
def get_dashboard_data(username: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Pega dados atuais
        # AQUI ESTAVA O ERRO: O banco retorna 'follower_count', não 'followers'
        cursor.execute("SELECT follower_count FROM profiles WHERE username = %s", (username,))
        current = cursor.fetchone()

        # 2. Pega histórico
        # Aqui usamos 'AS followers', então a chave 'followers' funcionará neste caso
        query_history = """
        SELECT 
            DATE_FORMAT(recorded_at, '%d/%m') as date, 
            MAX(follower_count) as followers
        FROM profile_history 
        WHERE username = %s 
        GROUP BY DATE(recorded_at) 
        ORDER BY recorded_at ASC
        LIMIT 30
        """
        cursor.execute(query_history, (username,))
        history = cursor.fetchall()

        # Calcula crescimento diário
        processed_history = []
        if history:
            for i in range(len(history)):
                item = history[i]
                # Se for o primeiro registro, crescimento é 0, senão compara com anterior
                prev = history[i-1]['followers'] if i > 0 else item['followers']
                growth = item['followers'] - prev
                
                processed_history.append({
                    "date": item['date'],
                    "followers": item['followers'],
                    "growth": growth
                })

        return {
            # CORREÇÃO CRÍTICA AQUI EMBAIXO:
            "current_followers": current['follower_count'] if current else 0,
            "daily_data": processed_history
        }
    
    except Exception as e:
        print(f"Erro na API: {e}")
        return {"error": str(e), "daily_data": [], "current_followers": 0}
    
    finally:
        if conn.is_connected():
            conn.close()