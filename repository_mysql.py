import mysql.connector
import os
from model import InstagramProfileModel
from datetime import datetime

class MySqlRepository:
    def __init__(self):
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
            return InstagramProfileModel(result['username'], result['follower_count'])
        return None

    def save_profile(self, model: InstagramProfileModel):
        # 1. Salva estado atual
        query_update = """
        INSERT INTO profiles (username, follower_count) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE follower_count = VALUES(follower_count)
        """
        self.cursor.execute(query_update, (model.username, model.follower_count))
        
        # 2. Salva histórico
        query_history = """
        INSERT INTO profile_history (username, follower_count)
        VALUES (%s, %s)
        """
        self.cursor.execute(query_history, (model.username, model.follower_count))
        self.conn.commit()

    def save_posts(self, username, posts_data):
        # 3. Salva Posts (Inteligência)
        query = """
        INSERT INTO posts (post_id, username, caption, likes_count, comments_count, posted_at, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            likes_count = VALUES(likes_count),
            comments_count = VALUES(comments_count)
        """
        
        data_to_insert = []
        for post in posts_data:
            # Tratamento de data (Apify retorna ISO string, MySQL precisa de datetime)
            ts_str = post.get('timestamp')
            try:
                # Tenta converter string ISO para objeto datetime python
                posted_at = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                posted_at = datetime.now()

            data_to_insert.append((
                post.get('id'),
                username,
                post.get('caption', '')[:65000] if post.get('caption') else "", 
                post.get('likesCount', 0),
                post.get('commentsCount', 0),
                posted_at,
                post.get('url')
            ))
            
        if data_to_insert:
            self.cursor.executemany(query, data_to_insert)
            self.conn.commit()
            print(f"💾 {len(data_to_insert)} posts salvos/atualizados no banco.")