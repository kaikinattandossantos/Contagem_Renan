class InstagramProfileModel:
    def __init__(self, username: str, follower_count: int):
        self.username = username
        self.follower_count = int(follower_count)

    @property
    def current_milestone(self) -> int:
        # A lógica matemática do marco de 1k
        return self.follower_count // 1000
    
    def to_dict(self):
        return {"username": self.username, "follower_count": self.follower_count}