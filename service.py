from apify_client import ApifyClient
from model import InstagramProfileModel, YouTubeChannelModel
import json
import re
import requests

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

    # ------------------------------
    # YOUTUBE (scraping clássico)
    # ------------------------------

    @staticmethod
    def _parse_compact_number(value: str) -> int:
        if not value:
            return 0
        s = value.strip().lower()
        s = s.replace('views', '').replace('view', '').replace('visualizações', '').replace('inscritos', '').replace('subscribers', '').strip()
        s = s.replace(',', '.').replace(' ', '')
        mult = 1
        if s.endswith('k'):
            mult = 1000
            s = s[:-1]
        elif s.endswith('m'):
            mult = 1_000_000
            s = s[:-1]
        elif s.endswith('b'):
            mult = 1_000_000_000
            s = s[:-1]
        if s.count('.') > 1:
            s = s.replace('.', '')
        try:
            return int(float(s) * mult)
        except:
            digits = re.sub(r'[^0-9]', '', s)
            return int(digits) if digits else 0

    def _youtube_fetch_html(self, handle: str) -> str:
        handle = handle.lstrip('@').strip()
        url = f"https://www.youtube.com/@{handle}/videos"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        return r.text

    def _youtube_extract_initial_data(self, html: str) -> dict:
        # tenta achar ytInitialData
        m = re.search(r"var ytInitialData = (\{.*?\});", html, re.DOTALL)
        if not m:
            m = re.search(r"ytInitialData\s*=\s*(\{.*?\});", html, re.DOTALL)
        if not m:
            return {}
        blob = m.group(1)
        try:
            return json.loads(blob)
        except Exception:
            return {}

    def _youtube_find_subscriber_count(self, data: dict) -> int:
        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'subscriberCountText':
                        if isinstance(v, dict):
                            if 'simpleText' in v:
                                return v['simpleText']
                            runs = v.get('runs')
                            if runs and isinstance(runs, list) and runs and 'text' in runs[0]:
                                return runs[0]['text']
                    res = walk(v)
                    if res is not None:
                        return res
            elif isinstance(obj, list):
                for it in obj:
                    res = walk(it)
                    if res is not None:
                        return res
            return None

        raw = walk(data)
        if not raw:
            return 0
        return self._parse_compact_number(str(raw))

    def _youtube_find_latest_videos(self, data: dict, handle: str) -> list[dict]:
        handle_clean = handle.lstrip('@').strip()
        videos = []

        def walk(obj):
            if isinstance(obj, dict):
                if 'videoRenderer' in obj and isinstance(obj['videoRenderer'], dict):
                    vr = obj['videoRenderer']
                    vid = vr.get('videoId')
                    title = ''
                    if isinstance(vr.get('title'), dict):
                        runs = vr['title'].get('runs')
                        if runs and isinstance(runs, list):
                            title = runs[0].get('text', '')
                        else:
                            title = vr['title'].get('simpleText', '')
                    views_raw = ''
                    vct = vr.get('viewCountText')
                    if isinstance(vct, dict):
                        views_raw = vct.get('simpleText') or ''
                        if not views_raw:
                            runs = vct.get('runs')
                            if runs and isinstance(runs, list) and runs:
                                views_raw = runs[0].get('text', '')
                    views = self._parse_compact_number(views_raw)
                    if vid:
                        videos.append({
                            'video_id': vid,
                            'title': title,
                            'views_count': views,
                            'published_at': None,
                            'url': f"https://www.youtube.com/watch?v={vid}"
                        })
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for it in obj:
                    walk(it)

        walk(data)
        seen=set()
        uniq=[]
        for v in videos:
            if v['video_id'] in seen:
                continue
            seen.add(v['video_id'])
            uniq.append(v)
        return uniq

    def check_youtube_and_notify(self, channel_handle: str, viral_views_threshold: int = 30000):
        try:
            handle = channel_handle.lstrip('@').strip()
            print(f"🕵️  Verificando YouTube @{handle} via scraping...")

            html = self._youtube_fetch_html(handle)
            data = self._youtube_extract_initial_data(html)
            if not data:
                print("⚠️  Aviso: não foi possível extrair ytInitialData do YouTube.")
                return

            # --- 1) Canal / Inscritos ---
            subs = self._youtube_find_subscriber_count(data)
            channel_model = YouTubeChannelModel(handle, subs)

            stored = self.repository.get_youtube_channel(handle)
            if stored:
                if channel_model.current_milestone > stored.current_milestone:
                    msg = (f"🚨 *MARCO DE INSCRITOS (YouTube)!* 🚨\n\n"
                           f"@{handle} rompeu a barreira dos {channel_model.current_milestone}k!\n"
                           f"🔥 Atual: {subs:,}")
                    self.notifier.send(msg.replace(',', '.'))

            self.repository.save_youtube_channel(channel_model)

            # --- 2) Vídeos / Viral por views ---
            videos = self._youtube_find_latest_videos(data, handle)
            if videos:
                top = videos[0]
                vid = top['video_id']
                current_views = int(top.get('views_count') or 0)
                prev_views = self.repository.get_youtube_video_views(vid)

                should_notify = False
                if prev_views is not None:
                    if prev_views < viral_views_threshold and current_views >= viral_views_threshold:
                        should_notify = True
                        print(f"🚀 Viral YouTube: {prev_views} -> {current_views}")
                else:
                    if current_views >= viral_views_threshold:
                        should_notify = True
                        print("🔥 Vídeo novo já chegou viralizando!")

                if should_notify:
                    title = (top.get('title') or 'Sem título')[:120]
                    msg = (f"🔥 *VÍDEO VIRALIZANDO (YouTube)!* 🔥\n\n"
                           f"Passou de {viral_views_threshold:,} views!\n"
                           f"👀 Atual: {current_views:,}\n"
                           f"🎬 {title}")
                    self.notifier.send(msg.replace(',', '.'))

                self.repository.save_youtube_videos(handle, videos[:20])

            print(f"✅ Ciclo YouTube concluído para @{handle}")

        except Exception as e:
            print(f"❌ Erro crítico no YouTube service: {e}")
