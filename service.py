from apify_client import ApifyClient
from model import InstagramProfileModel

class TrackerService:
    def __init__(self, api_token, repository, notifier):
        self.client = ApifyClient(api_token)
        self.repository = repository
        self.notifier = notifier

    def check_and_notify(self, target_username):
        print(f"🕵️  Verificando @{target_username} via Apify...")
        
        # Configuração do Scraper
        run_input = {
            "usernames": [target_username],
            "resultsLimit": 5 
        }
        
        # Executa Apify
        run = self.client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
        dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        
        if not dataset_items:
            raise Exception("Apify returned no data.")

        profile_data = dataset_items[0]
        current_followers = profile_data.get("followersCount")
        
        if current_followers is None:
            raise Exception("Follower count not found in data.")

        # 1. SALVAR O PERFIL (Resolver erro de Foreign Key)
        print(f"💾 Atualizando perfil base...")
        current_model = InstagramProfileModel(target_username, current_followers)
        
        # Recupera histórico para comparação antes de sobrescrever
        stored_profile = self.repository.get_profile(target_username)
        
        # Salva no banco (Agora o usuário existe!)
        self.repository.save_profile(current_model)

        # 2. PROCESSAR POSTS (Agora é seguro salvar posts)
        latest_posts = profile_data.get("latestPosts", [])
        if latest_posts:
            print(f"📸 Processando {len(latest_posts)} posts...")
            self.repository.save_posts(target_username, latest_posts)
            
            # Alerta de Viralização
            top_post = latest_posts[0]
            likes = top_post.get('likesCount', 0)
            if likes > 10000: 
                 self.notifier.send(f"🔥 *POST VIRALIZANDO!* O último post do @{target_username} bateu {likes} likes!")

        # 3. NOTIFICAR CRESCIMENTO
        if not stored_profile:
            self.notifier.send(f"👀 Monitoramento iniciado para *@{target_username}* com {current_followers} seguidores.")
            return

        old_milestone = stored_profile.current_milestone
        new_milestone = current_followers // 1000

        if new_milestone > old_milestone:
            msg = (
                f"🚨 *MARCO ATINGIDO!* 🚨\n\n"
                f"O perfil *@{target_username}* rompeu a barreira dos {new_milestone}k!\n"
                f"📈 Anterior: {stored_profile.follower_count}\n"
                f"🔥 Atual: {current_followers}"
            )
            self.notifier.send(msg)