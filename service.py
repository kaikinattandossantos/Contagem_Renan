from apify_client import ApifyClient
from model import InstagramProfileModel

class TrackerService:
    def __init__(self, api_token, repository, notifier):
        self.client = ApifyClient(api_token)
        self.repository = repository
        self.notifier = notifier

    def check_and_notify(self, target_username):
            print(f"🕵️  Verificando @{target_username} via Apify...")
            
            try:
                # --- 1. Executa Scraper ---
                run_input = { "usernames": [target_username], "resultsLimit": 5 }
                run = self.client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
                
                # Pega os dados do Dataset
                dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
                
                if not dataset_items:
                    print("⚠️  Aviso: Apify não retornou nenhum dado. Verifique o limite de créditos.")
                    return

                profile_data = dataset_items[0]
                
                # --- PROTEÇÃO CONTRA NONETYPE ---
                raw_followers = profile_data.get("followersCount")
                if raw_followers is None:
                    print(f"⚠️  Aviso: Não foi possível obter seguidores para @{target_username}")
                    return
                    
                current_followers = int(raw_followers)
                latest_posts = profile_data.get("latestPosts", [])

                # --- 2. Processa Perfil (Seguidores) ---
                print(f"💾 Atualizando perfil base...")
                current_model = InstagramProfileModel(target_username, current_followers)
                
                # Busca perfil antigo para comparar
                stored_profile = self.repository.get_profile(target_username)
                
                if stored_profile:
                    old_milestone = stored_profile.current_milestone
                    new_milestone = current_model.current_milestone
                    
                    if new_milestone > old_milestone:
                        msg = (f"🚨 *MARCO DE SEGUIDORES!* 🚨\n\n"
                            f"@{target_username} rompeu a barreira dos {new_milestone}k!\n"
                            f"🔥 Atual: {current_followers:,}")
                        self.notifier.send(msg.replace(',', '.'))

                # Salva o perfil novo (Atualiza a tabela profiles e history)
                self.repository.save_profile(current_model)

                # --- 3. Processa Posts (Lógica Viral) ---
                if latest_posts:
                    print(f"📸 Processando {len(latest_posts)} posts...")
                    top_post = latest_posts[0]
                    top_post_id = top_post.get('id')
                    current_likes = int(top_post.get('likesCount', 0))
                    viral_threshold = 40000 

                    previous_likes = self.repository.get_post_likes(top_post_id)
                    should_notify = False
                    
                    if previous_likes is not None:
                        if previous_likes < viral_threshold and current_likes >= viral_threshold:
                            should_notify = True
                            print(f"🚀 Viral: {previous_likes} -> {current_likes}")
                    else:
                        if current_likes >= viral_threshold:
                            should_notify = True
                            print("🔥 Post novo já chegou viralizando!")

                    if should_notify:
                        caption = (top_post.get('caption') or "Sem legenda")[:100]
                        msg = (f"🔥 *POST VIRALIZANDO!* 🔥\n\n"
                            f"O post passou de {viral_threshold} likes!\n"
                            f"👍 Atual: {current_likes:,}\n"
                            f"📝 \"{caption}...\"")
                        self.notifier.send(msg.replace(',', '.'))

                    # Atualiza posts no banco
                    self.repository.save_posts(target_username, latest_posts)
                    
                print(f"✅ Ciclo concluído para @{target_username}")

            except Exception as e:
                print(f"❌ Erro crítico no service: {e}")