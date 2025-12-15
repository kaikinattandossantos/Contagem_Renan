import mysql.connector
import os
from model import InstagramProfileModel

class MySqlRepository:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME")
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
            # 1. Atualiza o estado atual (como já fazia)
            query_update = """
            INSERT INTO profiles (username, follower_count) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE follower_count = VALUES(follower_count)
            """
            self.cursor.execute(query_update, (model.username, model.follower_count))
            
            # 2. NOVO: Salva no histórico para o gráfico
            query_history = """
            INSERT INTO profile_history (username, follower_count)
            VALUES (%s, %s)
            """
            self.cursor.execute(query_history, (model.username, model.follower_count))
            
            self.conn.commit()
    
