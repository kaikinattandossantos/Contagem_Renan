from apify_client import ApifyClient
from model import InstagramProfileModel

class TrackerService:
    def __init__(self, api_token, repository):
        self.client = ApifyClient(api_token)
        self.repository = repository

    def check_and_notify(self, target_username):
        print(f"🕵️  Iniciando verificação para: {target_username} via Apify...")

        # 1. Executa o Actor do Apify (Chamada Síncrona para simplificar o local)
        # Nota: Estamos pedindo apenas 1 resultado para economizar
        run_input = {
            "usernames": [target_username]
        }
        
        # Inicia o job e espera terminar
        run = self.client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
        
        # Busca os resultados no Dataset
        dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        
        if not dataset_items:
            print("❌ Erro: Apify não retornou dados. Verifique se o perfil existe ou se o proxy falhou.")
            return

        # Extrai dados do JSON retornado pelo Apify
        profile_data = dataset_items[0]
        current_followers = profile_data.get("followersCount")
        
        if current_followers is None:
            print("❌ Erro: Campo 'followersCount' não encontrado.")
            return

        print(f"📊 Seguidores atuais no Instagram: {current_followers}")

        # 2. Lógica de Comparação
        stored_profile = self.repository.get_profile(target_username)

        if not stored_profile:
            print("🆕 Primeiro monitoramento. Salvando estado inicial...")
            new_model = InstagramProfileModel(target_username, current_followers)
            self.repository.save_profile(new_model)
            return

        old_milestone = stored_profile.current_milestone
        new_milestone = current_followers // 1000

        # 3. Verifica Marco
        if new_milestone > old_milestone:
            # AQUI ENTRA SUA NOTIFICAÇÃO REAL (Telegram, Email, etc)
            print("="*40)
            print(f"🚀  SUCESSO! O perfil atingiu {new_milestone}k seguidores!")
            print("="*40)
        else:
            print(f"💤 Sem mudança de marco. (Atual: {new_milestone}k | Anterior: {old_milestone}k)")

        # 4. Atualiza o banco
        stored_profile.follower_count = current_followers
        self.repository.save_profile(stored_profile)