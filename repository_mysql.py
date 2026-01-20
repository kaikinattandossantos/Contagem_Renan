import mysql.connector
import os
from datetime import datetime

# --- MODEL (Estrutura de Dados) ---
class InstagramProfileModel:
    def __init__(self, username: str, follower_count):
        self.username = username
        # CORREÇÃO: Se follower_count for None, define como 0 para não travar
        self.follower_count = int(follower_count) if follower_count is not None else 0

    @property
    def current_milestone(self) -> int:
        return self.follower_count // 1000

# --- YOUTUBE MODEL (Estrutura de Dados) ---
class YouTubeChannelModel:
    def __init__(self, handle: str, subscriber_count):
        self.handle = handle.lstrip('@').strip()
        self.subscriber_count = int(subscriber_count) if subscriber_count is not None else 0

    @property
    def current_milestone(self) -> int:
        return self.subscriber_count // 1000


# --- REPOSITORY (Acesso ao Banco) ---
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
            return InstagramProfileModel(result['username'], result['follower_count'])
        return None

    def save_profile(self, model: InstagramProfileModel):
        query = """
        INSERT INTO profiles (username, follower_count) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE follower_count = VALUES(follower_count)
        """
        self.cursor.execute(query, (model.username, model.follower_count))
        
        query_hist = "INSERT INTO profile_history (username, follower_count) VALUES (%s, %s)"
        self.cursor.execute(query_hist, (model.username, model.follower_count))
        self.conn.commit()

    def save_posts(self, username, posts_data):
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

    def get_post_likes(self, post_id: str):
        query = "SELECT likes_count FROM posts WHERE post_id = %s"
        self.cursor.execute(query, (post_id,))
        result = self.cursor.fetchone()
        if result:
            return result['likes_count']
        return None

    # --- AS FUNÇÕES QUE FALTAVAM ---
    # O erro dava porque o main.py chamava estas funções e elas não existiam aqui.

    def get_daily_history(self, username):
            # CORREÇÃO: Adicionado MAX() dentro do DATE_FORMAT para satisfazer o only_full_group_by
            query = """
            SELECT 
                DATE_FORMAT(MAX(recorded_at), '%d/%m') as date, 
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


    # --- YOUTUBE (Canal + Vídeos) ---

    def get_youtube_channel(self, handle: str):
        handle = handle.lstrip('@').strip()
        query = "SELECT handle, subscriber_count FROM youtube_channels WHERE handle = %s"
        self.cursor.execute(query, (handle,))
        result = self.cursor.fetchone()
        if result:
            return YouTubeChannelModel(result['handle'], result['subscriber_count'])
        return None

    def save_youtube_channel(self, model: YouTubeChannelModel):
        handle = model.handle
        query = """
        INSERT INTO youtube_channels (handle, subscriber_count)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE subscriber_count = VALUES(subscriber_count)
        """
        self.cursor.execute(query, (handle, model.subscriber_count))

        query_hist = "INSERT INTO youtube_channel_history (handle, subscriber_count) VALUES (%s, %s)"
        self.cursor.execute(query_hist, (handle, model.subscriber_count))
        self.conn.commit()

    def get_youtube_video_views(self, video_id: str):
        query = "SELECT views_count FROM youtube_videos WHERE video_id = %s"
        self.cursor.execute(query, (video_id,))
        result = self.cursor.fetchone()
        if result:
            return result['views_count']
        return None

    def save_youtube_videos(self, handle: str, videos_data: list[dict]):
        handle = handle.lstrip('@').strip()
        query = """
        INSERT INTO youtube_videos (video_id, handle, title, views_count, published_at, url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE views_count = VALUES(views_count)
        """
        data=[]
        for v in videos_data:
            data.append((
                v.get('video_id'),
                handle,
                (v.get('title') or '')[:60000],
                int(v.get('views_count') or 0),
                v.get('published_at'),
                v.get('url')
            ))
        if data:
            self.cursor.executemany(query, data)
            self.conn.commit()
