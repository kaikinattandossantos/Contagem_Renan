from apify_client import ApifyClient
from model import InstagramProfileModel

class TrackerService:
    def __init__(self, api_token, repository, notifier):
        self.client = ApifyClient(api_token)
        self.repository = repository
        self.notifier = notifier

    def check_and_notify(self, target_username):
        print(f"🕵️  Verificando @{target_username} via Apify...")
        
        # --- 1. Executa Scraper ---
        run_input = { "usernames": [target_username], "resultsLimit": 5 }
        run = self.client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
        
        # Pega os dados do Dataset
        dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        if not dataset_items:
            raise Exception("Apify não retornou dados.")

        profile_data = dataset_items[0]
        current_followers = profile_data.get("followersCount")
        latest_posts = profile_data.get("latestPosts", [])

        # --- 2. Processa Perfil (Seguidores) ---
        print(f"💾 Atualizando perfil base...")
        # Cria o model e salva
        current_model = InstagramProfileModel(target_username, current_followers)
        
        # Verifica crescimento de seguidores (Lógica Mantida)
        stored_profile = self.repository.get_profile(target_username)
        if stored_profile:
            old_milestone = stored_profile.current_milestone
            new_milestone = current_model.current_milestone # Usa a property do model novo
            
            if new_milestone > old_milestone:
                msg = (f"🚨 *MARCO DE SEGUIDORES!* 🚨\n\n"
                       f"@{target_username} rompeu a barreira dos {new_milestone}k!")
                self.notifier.send(msg)

        # Salva o perfil novo
        self.repository.save_profile(current_model)

        # --- 3. Processa Posts (AQUI ESTÁ A CORREÇÃO DO VIRAL) ---
        if latest_posts:
            print(f"📸 Processando {len(latest_posts)} posts...")
            
            # Vamos olhar apenas o post mais recente (ou o fixado)
            top_post = latest_posts[0]
            top_post_id = top_post.get('id')
            current_likes = top_post.get('likesCount', 0)
            viral_threshold = 40000 # Seu limite de 40k

            # A. Pergunta ao banco: "Quantos likes esse post tinha antes?"
            previous_likes = self.repository.get_post_likes(top_post_id)
            
            should_notify = False
            
            # Cenário 1: O post já existia no banco
            if previous_likes is not None:
                # Só avisa se ANTES era menor que 40k e AGORA é maior/igual
                if previous_likes < viral_threshold and current_likes >= viral_threshold:
                    should_notify = True
                    print(f"🚀 Detectado rompimento de barreira: {previous_likes} -> {current_likes}")
                else:
                    print(f"ℹ️ Post {top_post_id} já monitorado (Antigo: {previous_likes} | Atual: {current_likes}). Sem alerta.")
            
            # Cenário 2: O post é novo (acabou de sair e já explodiu, ou primeira execução)
            else:
                if current_likes >= viral_threshold:
                    should_notify = True
                    print("🔥 Post novo já chegou viralizando!")

            # B. Envia notificação se necessário
            if should_notify:
                caption = top_post.get('caption', '')[:100]
                msg = (f"🔥 *POST VIRALIZANDO!* 🔥\n\n"
                       f"O post mais recente passou de {viral_threshold} likes!\n"
                       f"👍 Atual: {current_likes}\n"
                       f"📝 \"{caption}...\"")
                self.notifier.send(msg)

            # C. SÓ AGORA salva os posts no banco (atualizando o histórico)
            self.repository.save_posts(target_username, latest_posts)
            
        print("✅ Ciclo concluído.")
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