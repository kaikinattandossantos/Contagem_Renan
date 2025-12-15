from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

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

        # 1. Dados atuais
        cursor.execute("SELECT follower_count FROM profiles WHERE username = %s", (username,))
        current = cursor.fetchone()

        # 2. Histórico (Gráfico)
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

        processed_history = []
        if history:
            for i in range(len(history)):
                item = history[i]
                prev = history[i-1]['followers'] if i > 0 else item['followers']
                growth = item['followers'] - prev
                processed_history.append({
                    "date": item['date'],
                    "followers": item['followers'],
                    "growth": growth
                })

        # 3. Posts Recentes (Eventos de Impacto)
        query_posts = """
        SELECT caption, likes_count, DATE_FORMAT(posted_at, '%d/%m') as date_formatted, url
        FROM posts 
        WHERE username = %s 
        ORDER BY posted_at DESC 
        LIMIT 5
        """
        cursor.execute(query_posts, (username,))
        top_posts = cursor.fetchall()

        formatted_news = []
        for i, post in enumerate(top_posts):
            # Limpa legenda para virar título
            raw_caption = post['caption'] if post['caption'] else "Post sem legenda"
            title = (raw_caption[:50] + '...') if len(raw_caption) > 50 else raw_caption
            
            formatted_news.append({
                "id": i,
                "title": title,
                "date": post['date_formatted'],
                "impact": post['likes_count'],
                "description": raw_caption,
                "url": post['url']
            })

        return {
            "current_followers": current['follower_count'] if current else 0,
            "daily_data": processed_history,
            "top_news": formatted_news
        }
    
    except Exception as e:
        print(f"Erro API: {e}")
        return {"error": str(e), "daily_data": [], "top_news": []}
    finally:
        if conn.is_connected():
            conn.close()