import requests

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token          
        self.chat_id = chat_id      
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"

    def send(self, message: str):
        if not self.token or not self.chat_id:
            print("⚠️ Aviso: Credenciais do Telegram não configuradas. Notificação ignorada.")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            print("📨 Notificação enviada com sucesso!")
        except Exception as e:
            print(f"❌ Falha ao enviar notificação: {e}")
