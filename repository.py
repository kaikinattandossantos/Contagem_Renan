import json
import os
from model import InstagramProfileModel

class JsonRepository:
    def __init__(self, filename="db.json"):
        self.filename = filename

    def get_profile(self, username: str):
        if not os.path.exists(self.filename):
            return None
        
        with open(self.filename, 'r') as f:
            data = json.load(f)
            # Retorna o Model se o usuário existir no JSON
            if data.get("username") == username:
                return InstagramProfileModel(data["username"], data["follower_count"])
        return None

    def save_profile(self, model: InstagramProfileModel):
        with open(self.filename, 'w') as f:
            json.dump(model.to_dict(), f)