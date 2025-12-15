import os
from dotenv import load_dotenv
from notification import TelegramNotifier

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print(f"🔑 Token lido: {token[:10]}... (oculto)")
print(f"📍 Chat ID lido: {chat_id}")

notifier = TelegramNotifier(token, chat_id)
print("📨 Tentando enviar mensagem de teste...")

notifier.send("🔔 Teste de Notificação: Se você está lendo isso, a conexão funciona!")