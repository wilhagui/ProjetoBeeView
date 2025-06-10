# standalone_search_app.py
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from io import BytesIO
import requests
import datetime
import threading # Adicionado para carregamento de imagens em background

# --- Configurações da API TMDB ---
API_KEY = "5968e0e2ae961359489ef818f486a395"
BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
TMDB_POSTER_SIZE_LIST = "w154"
TMDB_POSTER_SIZE_DETAIL = "w342"
TMDB_BACKDROP_SIZE_DETAIL = "w1280" # Usado para backdrop na tela de detalhes
TMDB_PROFILE_SIZE_CAST = "w185"

# --- Paleta de Cores BeeView ---
COLOR_BACKGROUND = "#0A0A0A"
COLOR_YELLOW_BEE = "#FFC107"
COLOR_WHITE_VIEW = "#F0F0F0"
COLOR_SEARCH_BAR_BG = "#1A1A1A"
COLOR_SEARCH_BAR_TEXT = "#E0E0E0"
COLOR_SEARCH_BAR_PLACEHOLDER = "#707070"
COLOR_BUZZ_TEXT = "#606060"
COLOR_RESULT_ITEM_BG = "#1C1C1C"
COLOR_RESULT_TEXT_TITLE = COLOR_WHITE_VIEW
COLOR_RESULT_TEXT_DETAILS = "#A0A0A0"
COLOR_ERROR_TEXT = "#FF6B6B"

COLOR_BACK_BUTTON_BG = "#282828"
COLOR_BACK_BUTTON_TEXT = COLOR_YELLOW_BEE
COLOR_DETAIL_TITLE_BG = "#121212" # Fundo para o título do filme na tela de detalhes
COLOR_DETAIL_TITLE_TEXT = COLOR_YELLOW_BEE
COLOR_DETAIL_CARD_BG = "#131313" # Fundo dos cards de Sinopse, Elenco, Detalhes
COLOR_DETAIL_CARD_BORDER = COLOR_YELLOW_BEE # Borda dos cards
COLOR_DETAIL_SECTION_TITLE_TEXT = COLOR_YELLOW_BEE # Cor para "Sinopse:", "Elenco:", "Detalhes:"
COLOR_DETAIL_TEXT_PRIMARY = COLOR_WHITE_VIEW
COLOR_DETAIL_TEXT_SECONDARY = "#B0B0B0"
COLOR_YELLOW_SEPARATOR_LINE = COLOR_YELLOW_BEE


BEE_CLASSIFICATIONS = {
    "Queen Bee": {"text": "Queen Bee", "fg_color": "#D9027D", "text_color": "#FFFFFF"},
    "Guard Bees": {"text": "Guard Bees", "fg_color": "#FFBF00", "text_color": "#000000"},
    "Worker Bees": {"text": "Worker Bees", "fg_color": "#F4D03F", "text_color": "#000000"},
    "Drone Bees": {"text": "Drone Bees", "fg_color": "#506070", "text_color": "#FFFFFF"},
    "Unclassified": {"text": "", "fg_color": "transparent", "text_color": "transparent"}
}

# --- Configurações de UI ---
POSTER_LIST_WIDTH = 90
POSTER_LIST_HEIGHT = 135
DETAIL_POSTER_WIDTH = 160
DETAIL_POSTER_HEIGHT = 240
ACTOR_PIC_SIZE = 50

class StandaloneSearchApp(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()

        self.title("BeeView - Pesquisa")
        self.geometry("1280x720")
        self.configure(fg_color=COLOR_BACKGROUND)
        ctk.set_appearance_mode("Dark")

        try:
            self.ui_font_family = "Bahnschrift"
            ctk.CTkFont(family=self.ui_font_family) # Tenta carregar para verificar disponibilidade
        except:
            self.ui_font_family = "Arial" # Fallback

        self.http_session = requests.Session() # Usar sessão para requisições HTTP

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self.image_cache = {}
        self.placeholder_poster_list = self._create_placeholder_image((POSTER_LIST_WIDTH, POSTER_LIST_HEIGHT), "Poster")
        self.placeholder_poster_detail = self._create_placeholder_image((DETAIL_POSTER_WIDTH, DETAIL_POSTER_HEIGHT), "Poster")
        self.placeholder_backdrop_detail = self._create_placeholder_image((1280, 380), "Backdrop", bg_color="#101010") # Placeholder para backdrop
        self.placeholder_actor_profile = self._create_circular_placeholder_image(ACTOR_PIC_SIZE, "?")


        self.last_search_query = ""
        self.last_search_results_data = []
        self.current_movie_detail_data = None
        self.current_view = "search_initial"
        self.initial_info_label = None

        self._display_initial_search_view()

    def _clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.initial_info_label = None

    def _create_logo(self, parent, size=70):
        logo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        font_logo = ctk.CTkFont(family=self.ui_font_family, size=size, weight="bold")
        lbl_bee = ctk.CTkLabel(logo_frame, text="Bee", font=font_logo, text_color=COLOR_YELLOW_BEE)
        lbl_bee.pack(side="left")
        lbl_view = ctk.CTkLabel(logo_frame, text="View", font=font_logo, text_color=COLOR_WHITE_VIEW)
        lbl_view.pack(side="left", padx=(0, 5 if size < 70 else 10))
        return logo_frame

    def _display_initial_search_view(self):
        self.current_view = "search_initial"
        if self.winfo_width() != 1000 : self.geometry("1000x720") # Ajustar geometria para tela inicial
        self._clear_main_container()
        self.main_container.configure(fg_color=COLOR_BACKGROUND) # Cor de fundo principal
        # Configuração de grid para centralizar conteúdo
        self.main_container.grid_rowconfigure(0, weight=1) # Espaçador superior
        self.main_container.grid_rowconfigure(1, weight=0) # Logo
        self.main_container.grid_rowconfigure(2, weight=0) # Barra de pesquisa
        self.main_container.grid_rowconfigure(3, weight=0) # Info label
        self.main_container.grid_rowconfigure(4, weight=2) # Espaçador inferior
        self.main_container.grid_columnconfigure(0, weight=1) # Coluna central

        logo = self._create_logo(self.main_container)
        logo.grid(row=1, column=0, pady=(0, 30))

        self.search_entry = ctk.CTkEntry(
            self.main_container, placeholder_text="Pesquisar filmes...",
            font=ctk.CTkFont(family=self.ui_font_family, size=18), width=600, height=55, corner_radius=27,
            fg_color=COLOR_SEARCH_BAR_BG, text_color=COLOR_SEARCH_BAR_TEXT,
            placeholder_text_color=COLOR_SEARCH_BAR_PLACEHOLDER, border_color=COLOR_YELLOW_BEE, border_width=2
        )
        self.search_entry.grid(row=2, column=0, pady=20)
        self.search_entry.bind("<Return>", self._trigger_search)
        
        self.initial_info_label = ctk.CTkLabel(
            self.main_container, text="BuzzzZZZZZzzzz.....",
            font=ctk.CTkFont(family=self.ui_font_family, size=16, slant="italic"), text_color=COLOR_BUZZ_TEXT
        )
        self.initial_info_label.grid(row=3, column=0, pady=10)

    def _trigger_search(self, event=None):
        query = self.search_entry.get()
        if self.current_view == "search_initial" and self.initial_info_label and self.initial_info_label.winfo_exists():
            if not query.strip():
                self.initial_info_label.configure(text="Digite algo para pesquisar.", text_color=COLOR_ERROR_TEXT)
                return
            self.initial_info_label.configure(text=f"Pesquisando por '{query}'...", text_color=COLOR_BUZZ_TEXT)
        elif not query.strip():
            print("Query de pesquisa vazia em tela de resultados/detalhes.")
            return

        self.last_search_query = query
        if hasattr(self, 'main_container') and self.main_container.winfo_exists(): # Assegura que o container existe
             self.main_container.update_idletasks() # Atualiza UI antes da chamada de API
        self._perform_search_api(query)

    def _custom_score(self, movie):
        popularity = movie.get('popularity', 0.0)
        vote_count = movie.get('vote_count', 0)
        vote_average = movie.get('vote_average', 0.0)
        
        # Base score
        score = popularity * 0.5  # Popularidade tem peso maior

        # Bônus por alta contagem de votos (indicador de filme estabelecido/grande)
        if vote_count > 15000: score += popularity * 0.35
        elif vote_count > 7500: score += popularity * 0.25
        elif vote_count > 2500: score += popularity * 0.15
        elif vote_count > 500: score += popularity * 0.05

        # Bônus por alta nota média (se tiver um número razoável de votos)
        if vote_average >= 7.8 and vote_count > 1000: score += popularity * 0.15
        elif vote_average >= 7.0 and vote_count > 500: score += popularity * 0.05
        
        return score

    def _perform_search_api(self, query):
        search_url = f"{BASE_URL}/search/movie"
        params = {"api_key": API_KEY, "query": query, "language": "pt-BR", "include_adult": "false", "page": 1}
        try:
            response = self.http_session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            # Reordenar resultados com base na pontuação customizada
            self.last_search_results_data = sorted(results, key=self._custom_score, reverse=True)
            self._display_search_results_view(query, self.last_search_results_data)
        except requests.exceptions.RequestException as e:
            print(f"Erro de API/Rede: {e}")
            self._display_search_results_view(query, [], error_message="Erro ao buscar. Verifique sua conexão.")
        except Exception as e:
            print(f"Erro inesperado durante a busca API: {e}")
            self._display_search_results_view(query, [], error_message="Ocorreu um erro inesperado na busca.")

    def _create_placeholder_image(self, size, text="?", bg_color="#222222", text_color="#555555"):
        img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arialbd.ttf", int(min(size) / 2.2))
        except IOError:
            try: font = ImageFont.truetype("arial.ttf", int(min(size) / 2.2))
            except IOError: font = ImageFont.load_default(size=int(min(size)/2.5))       
        draw.text((size[0]/2, size[1]/2), text, fill=text_color, anchor="mm", font=font)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    def _create_circular_placeholder_image(self, size, text="?", bg_color="#444444", text_color="#888888"):
        img = Image.new("RGBA", (size,size), (0,0,0,0)) 
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, size-1, size-1), fill=bg_color)
        try: font = ImageFont.truetype("arial.ttf", int(size / 2.5))
        except IOError: font = ImageFont.load_default(size=int(size/2.5))
        draw.text((size/2, size/2), text, fill=text_color, anchor="mm", font=font)
        mask = Image.new('L', (size,size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size-1, size-1), fill=255)
        img.putalpha(mask)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size,size))

    def _apply_image_processing(self, pil_image_original, target_size, is_detail_backdrop, make_circular):
        processed_pil_image = pil_image_original.copy()
        if is_detail_backdrop:
            ow, oh = processed_pil_image.size
            rh = target_size[1]; rw = int(ow * rh / oh)
            if rw < target_size[0]: rw = target_size[0]; rh = int(oh * rw / ow)
            processed_pil_image = processed_pil_image.resize((rw, rh), Image.Resampling.LANCZOS)
            left = (rw - target_size[0]) / 2; top = (rh - target_size[1]) / 2
            processed_pil_image = processed_pil_image.crop((left, top, left + target_size[0], top + target_size[1]))
            enhancer = ImageEnhance.Brightness(processed_pil_image.convert("RGB"))
            processed_pil_image = enhancer.enhance(0.6)
        elif make_circular:
            processed_pil_image = processed_pil_image.resize(target_size, Image.Resampling.LANCZOS)
            mask = Image.new('L', target_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0) + target_size, fill=255)
            processed_pil_image.putalpha(mask)
        else:
            processed_pil_image.thumbnail(target_size, Image.Resampling.LANCZOS)
            final_image_canvas = Image.new("RGBA", target_size, (0,0,0,0))
            paste_x = (target_size[0] - processed_pil_image.width) // 2
            paste_y = (target_size[1] - processed_pil_image.height) // 2
            final_image_canvas.paste(processed_pil_image, (paste_x, paste_y), processed_pil_image if processed_pil_image.mode == 'RGBA' else None)
            processed_pil_image = final_image_canvas
        return processed_pil_image

    def _process_image_in_thread(self, cache_key, image_url, target_size, image_type,
                                 is_detail_backdrop, make_circular, img_label_to_update, placeholder_on_error):
        try:
            response = self.http_session.get(image_url, timeout=7)
            response.raise_for_status()
            pil_image_original = Image.open(BytesIO(response.content)).convert("RGBA")
            
            processed_pil_image = self._apply_image_processing(pil_image_original, target_size, is_detail_backdrop, make_circular)
            
            ctk_img = ctk.CTkImage(light_image=processed_pil_image, dark_image=processed_pil_image, size=target_size)
            self.image_cache[cache_key] = ctk_img

            if img_label_to_update and img_label_to_update.winfo_exists():
                self.after(0, lambda label=img_label_to_update, img=ctk_img: label.configure(image=img) if label.winfo_exists() else None)
        except Exception as e:
            print(f"Erro na thread ao carregar/processar imagem {image_url}: {e}")
            if img_label_to_update and img_label_to_update.winfo_exists(): # Garante que o placeholder seja exibido em caso de erro na thread
                 self.after(0, lambda label=img_label_to_update, img=placeholder_on_error: label.configure(image=img) if label.winfo_exists() else None)


    def _load_image_from_url(self, image_path, target_size, image_type="poster",
                             is_detail_backdrop=False, make_circular=False, img_label_to_update=None):
        if not img_label_to_update or not img_label_to_update.winfo_exists():
            # print("Aviso: _load_image_from_url chamado sem um img_label_to_update válido ou existente.")
            # Retornar um placeholder genérico se nenhum label for fornecido ou se ele não existir mais
            if image_type == "poster": return self.placeholder_poster_list if target_size == (POSTER_LIST_WIDTH, POSTER_LIST_HEIGHT) else self.placeholder_poster_detail
            if image_type == "profile": return self.placeholder_actor_profile
            return self.placeholder_backdrop_detail
            
        current_placeholder = None
        if image_type == "poster":
            current_placeholder = self.placeholder_poster_list if target_size == (POSTER_LIST_WIDTH, POSTER_LIST_HEIGHT) else self.placeholder_poster_detail
        elif image_type == "profile":
            current_placeholder = self.placeholder_actor_profile
        else: # backdrop
            current_placeholder = self.placeholder_backdrop_detail
        
        img_label_to_update.configure(image=current_placeholder)

        if not image_path:
            return # Label já está com placeholder

        # Determinar o tamanho da imagem TMDB com base no tipo e tamanho alvo
        if image_type == "profile": tmdb_img_size = TMDB_PROFILE_SIZE_CAST
        elif image_type == "poster": tmdb_img_size = TMDB_POSTER_SIZE_DETAIL if target_size == (DETAIL_POSTER_WIDTH, DETAIL_POSTER_HEIGHT) else TMDB_POSTER_SIZE_LIST
        else: tmdb_img_size = TMDB_BACKDROP_SIZE_DETAIL
        image_url = f"{TMDB_IMAGE_BASE_URL}{tmdb_img_size}{image_path}"
        
        cache_key = f"{image_url}_{target_size[0]}x{target_size[1]}_{image_type}_{is_detail_backdrop}_{make_circular}"

        if cache_key in self.image_cache:
            img_label_to_update.configure(image=self.image_cache[cache_key])
            return # Cache hit

        thread = threading.Thread(target=self._process_image_in_thread,
                                   args=(cache_key, image_url, target_size, image_type,
                                         is_detail_backdrop, make_circular, img_label_to_update, current_placeholder))
        thread.daemon = True
        thread.start()
        # A função não retorna um valor de imagem aqui, pois a atualização é assíncrona.
        # O label já exibe o placeholder.

    def _display_search_results_view(self, query, results_data, error_message=None):
        self.current_view = "search_results"
        if self.winfo_width() != 1000 : self.geometry("1000x720")
        self._clear_main_container()
        self.main_container.configure(fg_color=COLOR_BACKGROUND)

        self.main_container.grid_rowconfigure(0, weight=0) # Logo
        self.main_container.grid_rowconfigure(1, weight=0) # Barra de Pesquisa
        self.main_container.grid_rowconfigure(2, weight=1) # Resultados (ScrollFrame)
        self.main_container.grid_columnconfigure(0, weight=1)

        logo_frame = self._create_logo(self.main_container, size=50)
        logo_frame.grid(row=0, column=0, pady=(10,10))
        
        self.search_entry = ctk.CTkEntry(
             self.main_container, font=ctk.CTkFont(family=self.ui_font_family, size=18), width=600, height=55,
             corner_radius=27, fg_color=COLOR_SEARCH_BAR_BG, text_color=COLOR_SEARCH_BAR_TEXT,
             placeholder_text_color=COLOR_SEARCH_BAR_PLACEHOLDER, border_color=COLOR_YELLOW_BEE, border_width=2
        )
        self.search_entry.insert(0, query)
        self.search_entry.grid(row=1, column=0, pady=(0,20))
        self.search_entry.bind("<Return>", self._trigger_search)

        if error_message:
            ctk.CTkLabel(self.main_container, text=error_message, font=ctk.CTkFont(family=self.ui_font_family, size=18), text_color=COLOR_ERROR_TEXT).grid(row=2, column=0, pady=20, sticky="n")
            return
        if not results_data and query:
            ctk.CTkLabel(self.main_container, text=f"Nenhum resultado encontrado para '{query}'.", font=ctk.CTkFont(family=self.ui_font_family, size=18), text_color=COLOR_RESULT_TEXT_DETAILS).grid(row=2, column=0, pady=20, sticky="n")
            return
        
        results_scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent", scrollbar_button_color=COLOR_YELLOW_BEE, scrollbar_button_hover_color=COLOR_WHITE_VIEW)
        results_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=50)

        for item_data in results_data:
            movie_id = item_data.get("id")
            title = item_data.get("title", "N/A")
            # Lambda agora captura movie_id e title corretamente para cada item
            click_callback = lambda e, mid=movie_id, mtitle=title: self._on_result_click(mtitle, mid)

            item_frame = ctk.CTkFrame(results_scroll_frame, fg_color=COLOR_RESULT_ITEM_BG, corner_radius=15, height=155) # Altura fixa para consistência
            item_frame.pack(fill="x", pady=(5,10), padx=10)
            item_frame.bind("<Button-1>", click_callback)

            item_content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            item_content_frame.pack(fill="both", expand=True, padx=0, pady=0) # Removido padding aqui para controlar dentro
            item_content_frame.grid_columnconfigure(0, weight=0, minsize=POSTER_LIST_WIDTH + 30) # Poster + padding
            item_content_frame.grid_columnconfigure(1, weight=1) # Textos
            item_content_frame.grid_rowconfigure(0, weight=1)
            item_content_frame.bind("<Button-1>", click_callback)
            
            # Poster (inicia com placeholder, _load_image_from_url lida com o carregamento em thread)
            img_label = ctk.CTkLabel(item_content_frame, text="", width=POSTER_LIST_WIDTH, height=POSTER_LIST_HEIGHT) # Placeholder será setado por _load_image_from_url
            img_label.grid(row=0, column=0, padx=(15,10), pady=10, sticky="nsw") # Sticky nsw para alinhar topo-esquerda
            img_label.bind("<Button-1>", click_callback)
            self._load_image_from_url(item_data.get("poster_path"), (POSTER_LIST_WIDTH, POSTER_LIST_HEIGHT), "poster", img_label_to_update=img_label)


            text_frame = ctk.CTkFrame(item_content_frame, fg_color="transparent")
            text_frame.grid(row=0, column=1, sticky="nsew", padx=(0,15), pady=10)
            text_frame.bind("<Button-1>", click_callback)

            title_label = ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(family=self.ui_font_family, size=18, weight="bold"), text_color=COLOR_RESULT_TEXT_TITLE, anchor="w", justify="left", wraplength=450)
            title_label.pack(pady=(0,5), fill="x", anchor="nw") # anchor nw
            title_label.bind("<Button-1>", click_callback)

            overview = item_data.get("overview", "Sinopse não disponível.")
            max_overview = 120 
            display_overview = (overview[:max_overview] + '...') if len(overview) > max_overview else overview
            synopsis_label = ctk.CTkLabel(text_frame, text=f"{display_overview}", font=ctk.CTkFont(family=self.ui_font_family, size=12), text_color=COLOR_RESULT_TEXT_DETAILS, wraplength=450, justify="left", anchor="w")
            synopsis_label.pack(pady=2, fill="x", anchor="nw") # anchor nw
            synopsis_label.bind("<Button-1>", click_callback)

            rating = item_data.get("vote_average", 0.0)
            rating_text = f"Avaliação: {rating:.1f}/10" if rating else "Avaliação: N/A"
            rating_label = ctk.CTkLabel(text_frame, text=rating_text, font=ctk.CTkFont(family=self.ui_font_family, size=13, weight="bold"), text_color=COLOR_RESULT_TEXT_DETAILS, anchor="w")
            rating_label.pack(pady=(5,0), fill="x", anchor="sw") # anchor sw
            rating_label.bind("<Button-1>", click_callback)


    def _on_result_click(self, movie_title, movie_id):
        if movie_id:
            print(f"Item clicado: {movie_title} (ID: {movie_id}). Buscando detalhes...")
            self._fetch_movie_details_api(movie_id, movie_title)
        else:
            print(f"Item clicado: {movie_title}, mas não possui ID.")
            # Opcional: Mostrar uma mensagem na UI que detalhes não estão disponíveis.

    def _fetch_movie_details_api(self, movie_id, fallback_title="Filme"):
        self._clear_main_container() # Limpa para mostrar o label de carregamento
        loading_label_detail = ctk.CTkLabel(self.main_container, text=f"Carregando detalhes para {fallback_title}...", text_color=COLOR_BUZZ_TEXT, font=ctk.CTkFont(family=self.ui_font_family, size=18))
        loading_label_detail.place(relx=0.5, rely=0.5, anchor="center")
        self.main_container.update_idletasks() # Garante que o label de carregamento apareça

        detail_url = f"{BASE_URL}/movie/{movie_id}"
        params = {"api_key": API_KEY, "language": "pt-BR", "append_to_response": "credits,videos"}
        try:
            response = self.http_session.get(detail_url, params=params, timeout=10)
            response.raise_for_status()
            self.current_movie_detail_data = response.json()
            if loading_label_detail.winfo_exists(): loading_label_detail.destroy() # Remove o label de carregamento
            self._display_movie_detail_view(self.current_movie_detail_data)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar detalhes do filme (ID: {movie_id}): {e}")
            if loading_label_detail.winfo_exists(): loading_label_detail.configure(text="Erro ao carregar detalhes. Tente voltar.", text_color=COLOR_ERROR_TEXT)
            # Adicionar um botão de voltar aqui seria uma boa melhoria de UX em caso de erro
        except Exception as e:
            print(f"Erro inesperado ao processar detalhes: {e}")
            if loading_label_detail.winfo_exists(): loading_label_detail.configure(text="Erro inesperado ao carregar.", text_color=COLOR_ERROR_TEXT)
            
    def _get_bee_classification(self, movie_data):
        vote_avg = movie_data.get("vote_average", 0.0)
        vote_count = movie_data.get("vote_count", 0)
        popularity = movie_data.get("popularity", 0.0)

        # Lógica de classificação refinada
        if vote_avg >= 8.0 and vote_count >= 2000 and popularity >= 150: return BEE_CLASSIFICATIONS["Queen Bee"]
        if vote_avg >= 7.8 and vote_count >= 1000 and popularity >= 100: return BEE_CLASSIFICATIONS["Queen Bee"] # Ajuste para Queen Bee
        if vote_avg >= 7.0 and vote_count >= 500 and popularity >= 50: return BEE_CLASSIFICATIONS["Guard Bees"]
        if vote_avg >= 6.8 and vote_count >= 250 and popularity >= 30: return BEE_CLASSIFICATIONS["Guard Bees"] # Ajuste para Guard Bees
        if vote_avg >= 5.5 and vote_count >= 100 : return BEE_CLASSIFICATIONS["Worker Bees"]
        if vote_avg >= 5.0 and vote_count >= 50 : return BEE_CLASSIFICATIONS["Worker Bees"] # Ajuste para Worker Bees
        if vote_count >= 20: # Se tem alguns votos
            if vote_avg < 5.0 : return BEE_CLASSIFICATIONS["Drone Bees"] # Mas a nota é baixa
        elif vote_avg < 4.0: # Penaliza notas muito baixas mesmo com poucos votos
             return BEE_CLASSIFICATIONS["Drone Bees"]
        return BEE_CLASSIFICATIONS["Unclassified"] # Default se não se encaixar

    def _format_runtime(self, minutes):
        if not minutes or not isinstance(minutes, int): return "N/A"
        h = minutes // 60
        m = minutes % 60
        return f"{h}h {m}min" if h > 0 else f"{m}min"

    def _format_date(self, date_str):
        if not date_str: return "N/A"
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return date_str # Retorna a string original se o formato for inesperado

    def _display_movie_detail_view(self, movie_data):
        self.current_view = "movie_detail"
        if self.winfo_width() != 1280 or self.winfo_height() != 720 : self.geometry("1280x720") # Garante o tamanho da janela
        self._clear_main_container()
        self.main_container.configure(fg_color=COLOR_BACKGROUND)
        self.main_container.pack_propagate(False) # Evita que o main_container encolha com o conteúdo

        top_banner_height = 370
        top_banner_frame = ctk.CTkFrame(self.main_container, height=top_banner_height, fg_color=COLOR_BACKGROUND, corner_radius=0)
        top_banner_frame.pack(side="top", fill="x", expand=False)
        top_banner_frame.pack_propagate(False)

        # Backdrop
        backdrop_label = ctk.CTkLabel(top_banner_frame, text="")
        backdrop_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._load_image_from_url(movie_data.get("backdrop_path"), 
                                 (self.winfo_width(), top_banner_height), # Usar winfo_width para largura dinâmica do backdrop
                                 "backdrop", is_detail_backdrop=True, img_label_to_update=backdrop_label)
        
        content_overlay_frame = ctk.CTkFrame(top_banner_frame, fg_color="transparent")
        content_overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)

        back_button = ctk.CTkButton(
            content_overlay_frame, text="‹ Voltar", width=90, height=35, font=ctk.CTkFont(family=self.ui_font_family, size=15, weight="bold"),
            fg_color=COLOR_BACK_BUTTON_BG, text_color=COLOR_BACK_BUTTON_TEXT, hover_color=COLOR_YELLOW_BEE, corner_radius=8,
            command=lambda: self._display_search_results_view(self.last_search_query, self.last_search_results_data)
        )
        back_button.place(x=30, y=25)

        poster_info_container = ctk.CTkFrame(content_overlay_frame, fg_color="transparent")
        poster_info_container.place(x=40, y=85)

        poster_img_label = ctk.CTkLabel(poster_info_container, text="", corner_radius=8) # Placeholder será setado por _load_image_from_url
        poster_img_label.pack(side="left", padx=(0, 20), anchor="nw")
        self._load_image_from_url(movie_data.get("poster_path"), (DETAIL_POSTER_WIDTH, DETAIL_POSTER_HEIGHT), "poster", img_label_to_update=poster_img_label)


        info_texts_frame = ctk.CTkFrame(poster_info_container, fg_color="transparent")
        info_texts_frame.pack(side="left", anchor="nw", pady=(5,0))

        title_text = movie_data.get("title", "Título Indisponível")
        title_container_frame = ctk.CTkFrame(info_texts_frame, fg_color=COLOR_DETAIL_TITLE_BG, corner_radius=10)
        title_label = ctk.CTkLabel(title_container_frame, text=title_text,
                                   font=ctk.CTkFont(family=self.ui_font_family, size=28, weight="bold"),
                                   text_color=COLOR_DETAIL_TITLE_TEXT, padx=15, pady=8, 
                                   wraplength= self.winfo_width() - DETAIL_POSTER_WIDTH - 180) # Ajustar wraplength dinamicamente
        title_label.pack()
        title_container_frame.pack(anchor="w", pady=(0, 10))

        classification = self._get_bee_classification(movie_data)
        if classification["text"]:
            bee_tag_label = ctk.CTkLabel(info_texts_frame, text=classification["text"],
                font=ctk.CTkFont(family=self.ui_font_family, size=15, weight="bold"),
                fg_color=classification["fg_color"], text_color=classification["text_color"],
                height=28, corner_radius=14, padx=12)
            bee_tag_label.pack(anchor="w", pady=(0, 8))

        rating_value = movie_data.get("vote_average", 0.0)
        rating_text = f"Avaliação: {rating_value:.1f}" if rating_value else "Avaliação: N/A"
        rating_label = ctk.CTkLabel(info_texts_frame, text=rating_text,
                                   font=ctk.CTkFont(family=self.ui_font_family, size=16), text_color=COLOR_WHITE_VIEW)
        rating_label.pack(anchor="w", pady=(0, 10))
        
        # --- Linha Amarela Separadora ---
        yellow_line = ctk.CTkFrame(self.main_container, height=3, fg_color=COLOR_YELLOW_SEPARATOR_LINE, corner_radius=0)
        yellow_line.pack(side="top", fill="x", pady=(0,10)) # pady ajustado

        # --- Bottom Section (Cards de Informação) ---
        cards_outer_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        cards_outer_frame.pack(side="top", fill="both", expand=True, padx=35, pady=(0,20)) # padx e pady ajustados
        cards_outer_frame.grid_columnconfigure((0,1,2), weight=1, uniform="cards_group_detail_new")
        cards_outer_frame.grid_rowconfigure(0, weight=1)


        # Card Sinopse
        sinopse_card = ctk.CTkFrame(cards_outer_frame, fg_color=COLOR_DETAIL_CARD_BG, border_width=1, border_color=COLOR_DETAIL_CARD_BORDER, corner_radius=10)
        sinopse_card.grid(row=0, column=0, padx=(0,10), pady=0, sticky="nsew")
        ctk.CTkLabel(sinopse_card, text="Sinopse:", font=ctk.CTkFont(family=self.ui_font_family, size=16, weight="bold"), text_color=COLOR_DETAIL_SECTION_TITLE_TEXT).pack(anchor="nw", padx=15, pady=(10,5))
        sinopse_text_widget = ctk.CTkTextbox(sinopse_card, wrap="word", activate_scrollbars=True, scrollbar_button_color=COLOR_YELLOW_BEE, fg_color="transparent", font=ctk.CTkFont(family=self.ui_font_family, size=13), text_color=COLOR_DETAIL_TEXT_PRIMARY, border_width=0, corner_radius=0)
        sinopse_text_widget.insert("1.0", movie_data.get("overview", "Sinopse não disponível."))
        sinopse_text_widget.configure(state="disabled")
        sinopse_text_widget.pack(fill="both", expand=True, padx=15, pady=(0,10))

        # Card Elenco
        elenco_card = ctk.CTkFrame(cards_outer_frame, fg_color=COLOR_DETAIL_CARD_BG, border_width=1, border_color=COLOR_DETAIL_CARD_BORDER, corner_radius=10)
        elenco_card.grid(row=0, column=1, padx=10, pady=0, sticky="nsew")
        ctk.CTkLabel(elenco_card, text="Elenco Principal:", font=ctk.CTkFont(family=self.ui_font_family, size=16, weight="bold"), text_color=COLOR_DETAIL_SECTION_TITLE_TEXT).pack(anchor="nw", padx=15, pady=(10,5))
        elenco_scroll_frame = ctk.CTkScrollableFrame(elenco_card, fg_color="transparent", border_width=0, scrollbar_button_color=COLOR_YELLOW_BEE)
        elenco_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        cast_list = movie_data.get("credits", {}).get("cast", [])
        if cast_list:
            for i, actor in enumerate(cast_list[:7]): # Limita a 7 atores
                actor_frame = ctk.CTkFrame(elenco_scroll_frame, fg_color="transparent")
                actor_frame.pack(fill="x", pady=5, padx=5)
                
                actor_img_label = ctk.CTkLabel(actor_frame, text="") # Placeholder setado por _load_image_from_url
                actor_img_label.pack(side="left", padx=(0,10))
                self._load_image_from_url(actor.get("profile_path"), (ACTOR_PIC_SIZE, ACTOR_PIC_SIZE), "profile", make_circular=True, img_label_to_update=actor_img_label)

                actor_info_frame = ctk.CTkFrame(actor_frame, fg_color="transparent")
                actor_info_frame.pack(side="left", fill="x", expand=True, anchor="w")
                ctk.CTkLabel(actor_info_frame, text=actor.get("name", "N/A"), font=ctk.CTkFont(family=self.ui_font_family, size=13, weight="bold"), text_color=COLOR_DETAIL_TEXT_PRIMARY, anchor="w").pack(fill="x")
                ctk.CTkLabel(actor_info_frame, text=f"({actor.get('character', 'N/A')})", font=ctk.CTkFont(family=self.ui_font_family, size=11), text_color=COLOR_DETAIL_TEXT_SECONDARY, anchor="w", wraplength=180).pack(fill="x")
        else:
            ctk.CTkLabel(elenco_scroll_frame, text="Elenco não disponível.", font=ctk.CTkFont(family=self.ui_font_family, size=13), text_color=COLOR_DETAIL_TEXT_SECONDARY).pack(padx=15, pady=10)

        # Card Info Adicionais
        info_card = ctk.CTkFrame(cards_outer_frame, fg_color=COLOR_DETAIL_CARD_BG, border_width=1, border_color=COLOR_DETAIL_CARD_BORDER, corner_radius=10)
        info_card.grid(row=0, column=2, padx=(10,0), pady=0, sticky="nsew")
        ctk.CTkLabel(info_card, text="Detalhes:", font=ctk.CTkFont(family=self.ui_font_family, size=16, weight="bold"), text_color=COLOR_DETAIL_SECTION_TITLE_TEXT).pack(anchor="nw", padx=15, pady=(10,10))
        details_frame_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        details_frame_inner.pack(fill="x", padx=15, pady=0, anchor="n")
        
        runtime_str = self._format_runtime(movie_data.get("runtime"))
        ctk.CTkLabel(details_frame_inner, text=f"Duração: {runtime_str}", font=ctk.CTkFont(family=self.ui_font_family, size=13, weight="bold"), text_color=COLOR_DETAIL_TEXT_PRIMARY).pack(anchor="w", pady=2)
        release_date_str = self._format_date(movie_data.get("release_date"))
        ctk.CTkLabel(details_frame_inner, text=f"Lançamento: {release_date_str}", font=ctk.CTkFont(family=self.ui_font_family, size=13), text_color=COLOR_DETAIL_TEXT_PRIMARY).pack(anchor="w", pady=2)
        origin_countries = movie_data.get("production_countries", [])
        country_str = origin_countries[0]["iso_3166_1"] if origin_countries else "N/A" # Pega só o código do primeiro país
        ctk.CTkLabel(details_frame_inner, text=f"País: {country_str}", font=ctk.CTkFont(family=self.ui_font_family, size=13), text_color=COLOR_DETAIL_TEXT_PRIMARY).pack(anchor="w", pady=2)
        genres = movie_data.get("genres", [])
        genres_str = ", ".join([g["name"] for g in genres[:3]]) if genres else "N/A" # Primeiros 3 gêneros
        ctk.CTkLabel(details_frame_inner, text=f"Gêneros: {genres_str}", font=ctk.CTkFont(family=self.ui_font_family, size=13), text_color=COLOR_DETAIL_TEXT_PRIMARY, wraplength=200).pack(anchor="w", pady=2)


if __name__ == "__main__":
    app = StandaloneSearchApp()
    app.mainloop()