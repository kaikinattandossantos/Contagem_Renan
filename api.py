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
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )

@app.get("/dashboard/{username}")
def get_dashboard_data(username: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Dados Atuais
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

        # 3. Posts Recentes (Top News)
        # Ajustado para bater com o Frontend
        query_posts = """
        SELECT caption, likes_count, comments_count, DATE_FORMAT(posted_at, '%d/%m') as date_formatted, url
        FROM posts 
        WHERE username = %s 
        ORDER BY posted_at DESC 
        LIMIT 10
        """
        cursor.execute(query_posts, (username,))
        top_posts = cursor.fetchall()

        formatted_news = []
        for i, post in enumerate(top_posts):
            raw_caption = post['caption'] if post['caption'] else "Post sem legenda"
            title = (raw_caption[:50] + '...') if len(raw_caption) > 50 else raw_caption
            
            formatted_news.append({
                "id": i,
                "title": title,               # Front usa .title
                "date": post['date_formatted'], # Front usa .date
                "impact": post['likes_count'],  # Front usa .impact (CORRIGIDO AQUI)
                "description": raw_caption,     # Front usa .description
                "url": post['url']            # Front usa .url
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

# Rota auxiliar para garantir que tabelas existam
@app.get("/setup-banco")
def setup_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Recria tabelas se não existirem
    queries = [
        "CREATE TABLE IF NOT EXISTS profiles (username VARCHAR(50) PRIMARY KEY, follower_count INT NOT NULL, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS profile_history (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL, follower_count INT NOT NULL, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS posts (post_id VARCHAR(50) PRIMARY KEY, username VARCHAR(50), caption TEXT, likes_count INT, comments_count INT, posted_at TIMESTAMP, url VARCHAR(255), recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (username) REFERENCES profiles(username))"
    ]
    for q in queries:
        cursor.execute(q)
    conn.commit()
    conn.close()
    return {"status": "Banco verificado"}