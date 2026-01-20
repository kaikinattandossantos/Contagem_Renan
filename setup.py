import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def criar_tabelas():
    print("🔌 Conectando ao Railway...")
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    print("🔨 Criando/Verificando tabelas...")
    
    # 1. Tabela Profiles (O Pai)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        username VARCHAR(50) PRIMARY KEY,
        follower_count INT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """)

    # 2. Tabela Histórico
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        follower_count INT NOT NULL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Tabela Posts (O Filho)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        post_id VARCHAR(50) PRIMARY KEY,
        username VARCHAR(50),
        caption TEXT,
        likes_count INT,
        comments_count INT,
        posted_at TIMESTAMP,
        url VARCHAR(255),
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES profiles(username)
    );
    """)


    # 4. Tabelas YouTube
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS youtube_channels (
        handle VARCHAR(100) PRIMARY KEY,
        subscriber_count INT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS youtube_channel_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        handle VARCHAR(100) NOT NULL,
        subscriber_count INT NOT NULL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS youtube_videos (
        video_id VARCHAR(32) PRIMARY KEY,
        handle VARCHAR(100) NOT NULL,
        title TEXT,
        views_count INT DEFAULT 0,
        published_at TIMESTAMP NULL,
        url VARCHAR(255),
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
    print("✅ SUCESSO! Todas as tabelas estão prontas.")

if __name__ == "__main__":
    criar_tabelas()