import mysql.connector
import os
from datetime import datetime

# --- SEU MODEL (Estrutura de Dados) ---
class InstagramProfileModel:
    def __init__(self, username: str, follower_count: int):
        self.username = username
        self.follower_count = int(follower_count)

    @property
    def current_milestone(self) -> int:
        # A lógica matemática do marco de 1k (Ex: 320300 -> 320)
        return self.follower_count // 1000
    
    def to_dict(self):
        return {"username": self.username, "follower_count": self.follower_count}

# --- SEU REPOSITORY (Acesso ao Banco) ---
class MySqlRepository:
    def __init__(self):
        # Conecta usando as variáveis de ambiente do Railway
        self.conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def get_profile(self, username: str):
        query = "SELECT username, follower_count FROM profiles WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        
        if result:
            # AQUI: Instancia o SEU Model com os dados do banco
            return InstagramProfileModel(result['username'], result['follower_count'])
        return None

    def save_profile(self, model: InstagramProfileModel):
        # 1. Salva/Atualiza Perfil
        query = """
        INSERT INTO profiles (username, follower_count) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE follower_count = VALUES(follower_count)
        """
        self.cursor.execute(query, (model.username, model.follower_count))
        
        # 2. Salva Histórico
        query_hist = "INSERT INTO profile_history (username, follower_count) VALUES (%s, %s)"
        self.cursor.execute(query_hist, (model.username, model.follower_count))
        self.conn.commit()

    def save_posts(self, username, posts_data):
        # Lógica de salvar posts (PostgreSQL/MySQL datetime fix included)
        query = """
        INSERT INTO posts (post_id, username, caption, likes_count, comments_count, posted_at, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE likes_count = VALUES(likes_count), comments_count = VALUES(comments_count)
        """
        data = []
        for post in posts_data:
            ts = post.get('timestamp')
            try:
                posted_at = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                posted_at = datetime.now()
            
            data.append((
                post.get('id'), username, post.get('caption', '')[:60000], 
                post.get('likesCount', 0), post.get('commentsCount', 0), 
                posted_at, post.get('url')
            ))
        
        if data:
            self.cursor.executemany(query, data)
            self.conn.commit()
            print(f"💾 {len(data)} posts salvos no banco.")

    def get_post_likes(self, post_id: str):
        """Checa likes anteriores para detectar viralização"""
        query = "SELECT likes_count FROM posts WHERE post_id = %s"
        self.cursor.execute(query, (post_id,))
        result = self.cursor.fetchone()
        if result:
            return result['likes_count']
        return None

    # --- MÉTODOS PARA A API/DASHBOARD ---

    def get_daily_history(self, username):
        query = """
        SELECT 
            DATE_FORMAT(recorded_at, '%d/%m') as date, 
            MAX(follower_count) as followers
        FROM profile_history 
        WHERE username = %s 
        GROUP BY DATE(recorded_at) 
        ORDER BY MAX(recorded_at) ASC
        LIMIT 30
        """
        self.cursor.execute(query, (username,))
        return self.cursor.fetchall()

    def get_recent_posts(self, username):
        query = """
        SELECT caption, likes_count, DATE_FORMAT(posted_at, '%d/%m') as date_formatted, url
        FROM posts 
        WHERE username = %s 
        ORDER BY posted_at DESC 
        LIMIT 10
        """
        self.cursor.execute(query, (username,))
        return self.cursor.fetchall()