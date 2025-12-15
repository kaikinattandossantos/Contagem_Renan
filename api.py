# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Permite que o Frontend (que roda em outra porta) acesse a API
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
    cursor = conn.cursor(dictionary=True)

    # 1. Pega dados atuais
    cursor.execute("SELECT follower_count FROM profiles WHERE username = %s", (username,))
    current = cursor.fetchone()

    # 2. Pega histórico dos últimos 30 dias (agrupado por dia para não repetir dados)
    # Pegamos o MAIOR valor de cada dia
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

    conn.close()

    # Calcula crescimento diário (mock simples por enquanto na lógica)
    processed_history = []
    for i in range(len(history)):
        item = history[i]
        prev = history[i-1]['followers'] if i > 0 else item['followers']
        growth = item['followers'] - prev
        processed_history.append({
            "date": item['date'],
            "followers": item['followers'],
            "growth": growth
        })

    return {
        "current_followers": current['followers'] if current else 0,
        "daily_data": processed_history
    }

# Para rodar: uvicorn api:app --reload