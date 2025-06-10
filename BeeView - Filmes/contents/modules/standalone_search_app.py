import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from io import BytesIO
import requests
import datetime
import threading
import math # Added for hexagon calculations
import webbrowser # Added for opening URLs

# --- Configurações da API TMDB ---
TMDB_API_KEY = "5968e0e2ae961359489ef818f486a395" # Replace with your actual API key
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
TMDB_POSTER_SIZE_LIST = "w154"
TMDB_POSTER_SIZE_DETAIL_SRC = "w342" # Source size for detail poster before hex processing
TMDB_BACKDROP_SIZE_DETAIL = "w1280"
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

COLOR_DETAIL_OVERLAY_BG = "transparent" 
COLOR_DETAIL_TEXT_KEY = COLOR_WHITE_VIEW
COLOR_DETAIL_TEXT_VALUE = COLOR_WHITE_VIEW
COLOR_DETAIL_SYNOPSIS_TEXT = "#D0D0D0"
COLOR_HEX_PLACEHOLDER_BG = "#282828"
COLOR_HEX_PLACEHOLDER_TEXT = "#606060"
COLOR_BACK_BUTTON_DETAIL_BG = "#282828" # Specific for detail view back button
COLOR_BACK_BUTTON_DETAIL_TEXT = COLOR_YELLOW_BEE
COLOR_TRAILER_BUTTON_BG = COLOR_YELLOW_BEE
COLOR_TRAILER_BUTTON_TEXT = "#000000" # Black text for yellow button
COLOR_TRAILER_BUTTON_HOVER = "#FFD700" # Darker yellow for hover
COLOR_TRAILER_BUTTON_DISABLED_BG = "#404040"


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

DETAIL_HEX_POSTER_WIDTH = 190
DETAIL_HEX_POSTER_HEIGHT = 220

ACTOR_PIC_SIZE = 50
STAR_ICON = "★" 
LIGHTBULB_ICON = "💡" 

class StandaloneSearchApp(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()

        self.title("BeeView - Pesquisa")
        self.geometry("1280x720")
        self.configure(fg_color=COLOR_BACKGROUND)
        ctk.set_appearance_mode("Dark")

        try:
            self.ui_font_family = "Bahnschrift"
            ctk.CTkFont(family=self.ui_font_family) 
        except:
            self.ui_font_family = "Arial" 

        self.http_session = requests.Session()

        self.root_container = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        self.root_container.pack(fill="both", expand=True)

        self.image_cache = {}
        self.placeholder_poster_list = self._create_placeholder_image((POSTER_LIST_WIDTH, POSTER_LIST_HEIGHT), "Poster")
        self.placeholder_hex_poster_detail = self._create_placeholder_image(
            (DETAIL_HEX_POSTER_WIDTH, DETAIL_HEX_POSTER_HEIGHT), "Poster", shape="hexagon",
            bg_color=COLOR_HEX_PLACEHOLDER_BG, text_color=COLOR_HEX_PLACEHOLDER_TEXT
        )
        self.placeholder_backdrop_detail = self._create_placeholder_image((1280, 380), "Backdrop", bg_color="#101010")
        self.placeholder_actor_profile = self._create_circular_placeholder_image(ACTOR_PIC_SIZE, "?")

        self.last_search_query = ""
        self.last_search_results_data = []
        self.current_movie_detail_data = None
        self.current_view = "search_initial"
        
        self.main_view_container = ctk.CTkFrame(self.root_container, fg_color="transparent")

        self._display_initial_search_view()

    def _clear_view_container(self, container):
        for widget in container.winfo_children():
            widget.destroy()

    def _create_logo(self, parent, size=70, command=None):
        logo_frame = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2" if command else "")
        font_logo = ctk.CTkFont(family=self.ui_font_family, size=size, weight="bold")
        
        lbl_bee = ctk.CTkLabel(logo_frame, text="Bee", font=font_logo, text_color=COLOR_YELLOW_BEE)
        lbl_bee.pack(side="left")
        if command:
            lbl_bee.bind("<Button-1>", lambda e: command())

        lbl_view = ctk.CTkLabel(logo_frame, text="View", font=font_logo, text_color=COLOR_WHITE_VIEW)
        lbl_view.pack(side="left", padx=(0, 5 if size < 70 else 10))
        if command:
            lbl_view.bind("<Button-1>", lambda e: command())
            logo_frame.bind("<Button-1>", lambda e: command())
            
        return logo_frame

    def _display_initial_search_view(self):
        self.current_view = "search_initial"
        if self.winfo_width() != 1000 : self.geometry("1000x720")
        
        self._clear_view_container(self.root_container) 
        self.main_view_container = ctk.CTkFrame(self.root_container, fg_color=COLOR_BACKGROUND)
        self.main_view_container.pack(fill="both", expand=True)

        self.main_view_container.grid_rowconfigure(0, weight=1) 
        self.main_view_container.grid_rowconfigure(1, weight=0) 
        self.main_view_container.grid_rowconfigure(2, weight=0) 
        self.main_view_container.grid_rowconfigure(3, weight=0) 
        self.main_view_container.grid_rowconfigure(4, weight=2) 
        self.main_view_container.grid_columnconfigure(0, weight=1) 

        logo = self._create_logo(self.main_view_container, size=70)
        logo.grid(row=1, column=0, pady=(0, 30))

        self.search_entry = ctk.CTkEntry(
            self.main_view_container, placeholder_text="Pesquisar filmes...",
            font=ctk.CTkFont(family=self.ui_font_family, size=18), width=600, height=55, corner_radius=27,
            fg_color=COLOR_SEARCH_BAR_BG, text_color=COLOR_SEARCH_BAR_TEXT,
            placeholder_text_color=COLOR_SEARCH_BAR_PLACEHOLDER, border_color=COLOR_YELLOW_BEE, border_width=2
        )
        self.search_entry.grid(row=2, column=0, pady=20)
        self.search_entry.bind("<Return>", self._trigger_search)
        
        self.initial_info_label = ctk.CTkLabel(
            self.main_view_container, text="BuzzzZZZZZzzzz.....",
            font=ctk.CTkFont(family=self.ui_font_family, size=16, slant="italic"), text_color=COLOR_BUZZ_TEXT
        )
        self.initial_info_label.grid(row=3, column=0, pady=10)
        if self.last_search_query: 
            self.search_entry.insert(0, self.last_search_query)


    def _trigger_search(self, event=None):
        query = self.search_entry.get()
        if self.current_view == "search_initial" and hasattr(self, 'initial_info_label') and self.initial_info_label and self.initial_info_label.winfo_exists():
            if not query.strip():
                self.initial_info_label.configure(text="Digite algo para pesquisar.", text_color=COLOR_ERROR_TEXT)
                return
            self.initial_info_label.configure(text=f"Pesquisando por '{query}'...", text_color=COLOR_BUZZ_TEXT)
        elif not query.strip() and self.current_view != "search_initial":
            print("Query de pesquisa vazia.")
            return
        elif not query.strip(): 
            return

        self.last_search_query = query
        if hasattr(self, 'main_view_container') and self.main_view_container.winfo_exists():
            self.main_view_container.update_idletasks()
        self._perform_search_api(query)

    def _custom_score(self, movie):
        popularity = movie.get('popularity', 0.0)
        vote_count = movie.get('vote_count', 0)
        vote_average = movie.get('vote_average', 0.0)
        score = popularity * 0.5 
        if vote_count > 15000: score += popularity * 0.35
        elif vote_count > 7500: score += popularity * 0.25
        elif vote_count > 2500: score += popularity * 0.15
        elif vote_count > 500: score += popularity * 0.05
        if vote_average >= 7.8 and vote_count > 1000: score += popularity * 0.15
        elif vote_average >= 7.0 and vote_count > 500: score += popularity * 0.05
        return score

    def _perform_search_api(self, query):
        search_url = f"{TMDB_BASE_URL}/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": query, "language": "pt-BR", "include_adult": "false", "page": 1}
        try:
            response = self.http_session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            self.last_search_results_data = sorted(results, key=self._custom_score, reverse=True)
            self._display_search_results_view(query, self.last_search_results_data)
        except requests.exceptions.RequestException as e:
            print(f"Erro de API/Rede: {e}")
            self._display_search_results_view(query, [], error_message="Erro ao buscar. Verifique sua conexão.")
        except Exception as e:
            print(f"Erro inesperado durante a busca API: {e}")
            self._display_search_results_view(query, [], error_message="Ocorreu um erro inesperado na busca.")

    def _create_placeholder_image(self, size, text="?", bg_color="#222222", text_color="#555555", shape="rectangle"):
        img = Image.new("RGBA", size, (0,0,0,0) if shape == "hexagon" else bg_color) 
        draw = ImageDraw.Draw(img)

        if shape == "hexagon":
            draw.polygon(self._get_hexagon_points(size), fill=bg_color)
        elif shape != "rectangle": 
             pass 

        try:
            font_size_divisor = 2.2
            if shape == "hexagon": font_size_divisor = 3 
            font = ImageFont.truetype("arialbd.ttf", int(min(size) / font_size_divisor))
        except IOError:
            try: font = ImageFont.truetype("arial.ttf", int(min(size) / font_size_divisor))
            except IOError: font = ImageFont.load_default(size=int(min(size)/(font_size_divisor + 0.3)))
        
        text_bbox = draw.textbbox((0,0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        draw.text(((size[0]-text_width)/2, (size[1]-text_height)/2), text, fill=text_color, font=font)
        
        if shape == "hexagon": 
            mask_hex = Image.new('L', size, 0)
            draw_mask_hex = ImageDraw.Draw(mask_hex)
            draw_mask_hex.polygon(self._get_hexagon_points(size), fill=255)
            img.putalpha(mask_hex)

        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    def _get_hexagon_points(self, size):
        width, height = size
        return [
            (width * 0.5, 0), (width, height * 0.25), (width, height * 0.75),
            (width * 0.5, height), (0, height * 0.75), (0, height * 0.25)
        ]

    def _create_circular_placeholder_image(self, size, text="?", bg_color="#444444", text_color="#888888"):
        img = Image.new("RGBA", (size,size), (0,0,0,0)) 
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, size-1, size-1), fill=bg_color)
        try: font = ImageFont.truetype("arial.ttf", int(size / 2.5))
        except IOError: font = ImageFont.load_default(size=int(size/2.5))
        
        text_bbox = draw.textbbox((0,0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw.text(((size-text_width)/2, (size-text_height)/2), text, fill=text_color, font=font)
        
        mask = Image.new('L', (size,size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size-1, size-1), fill=255)
        img.putalpha(mask)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size,size))

    def _apply_image_processing(self, pil_image_original, target_size, is_detail_backdrop, make_circular, shape="rectangle"):
        processed_pil_image = pil_image_original.copy().convert("RGBA")

        if is_detail_backdrop:
            ow, oh = processed_pil_image.size
            rh = target_size[1]; rw = int(ow * rh / oh)
            if rw < target_size[0]: rw = target_size[0]; rh = int(oh * rw / ow)
            processed_pil_image = processed_pil_image.resize((rw, rh), Image.Resampling.LANCZOS)
            left = (rw - target_size[0]) / 2; top = (rh - target_size[1]) / 2
            processed_pil_image = processed_pil_image.crop((left, top, left + target_size[0], top + target_size[1]))
            enhancer = ImageEnhance.Brightness(processed_pil_image.convert("RGB")) 
            processed_pil_image = enhancer.enhance(0.5).convert("RGBA") 
        elif shape == "hexagon":
            img_for_hex = processed_pil_image.resize(target_size, Image.Resampling.LANCZOS)
            mask = Image.new('L', target_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.polygon(self._get_hexagon_points(target_size), fill=255)
            img_for_hex.putalpha(mask)
            processed_pil_image = img_for_hex
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
            final_image_canvas.paste(processed_pil_image, (paste_x, paste_y), processed_pil_image)
            processed_pil_image = final_image_canvas
        return processed_pil_image

    def _process_image_in_thread(self, cache_key, image_url, target_size, image_type,
                                 is_detail_backdrop, make_circular, shape, 
                                 img_label_to_update, placeholder_on_error):
        try:
            response = self.http_session.get(image_url, timeout=7)
            response.raise_for_status()
            pil_image_original = Image.open(BytesIO(response.content))
            
            processed_pil_image = self._apply_image_processing(
                pil_image_original, target_size, is_detail_backdrop, make_circular, shape 
            )
            
            ctk_img = ctk.CTkImage(light_image=processed_pil_image, dark_image=processed_pil_image, size=target_size)
            self.image_cache[cache_key] = ctk_img

            if img_label_to_update and img_label_to_update.winfo_exists():
                self.after(0, lambda label=img_label_to_update, img=ctk_img: label.configure(image=img) if label.winfo_exists() else None)
        except Exception as e:
            print(f"Erro na thread ao carregar/processar imagem {image_url}: {e}")
            if img_label_to_update and img_label_to_update.winfo_exists():
                self.after(0, lambda label=img_label_to_update, img=placeholder_on_error: label.configure(image=img) if label.winfo_exists() else None)

    def _load_image_from_url(self, image_path, target_size, image_type="poster",
                             is_detail_backdrop=False, make_circular=False, shape="rectangle", 
                             img_label_to_update=None):
        
        current_placeholder = None
        if image_type == "poster_list": current_placeholder = self.placeholder_poster_list
        elif image_type == "poster_detail_hex": current_placeholder = self.placeholder_hex_poster_detail
        elif image_type == "profile": current_placeholder = self.placeholder_actor_profile
        elif image_type == "backdrop": current_placeholder = self.placeholder_backdrop_detail
        else: 
            current_placeholder = self._create_placeholder_image(target_size, "?", shape=shape)

        if not img_label_to_update or not img_label_to_update.winfo_exists():
            return current_placeholder 

        img_label_to_update.configure(image=current_placeholder, text="") 

        if not image_path:
            return 

        tmdb_img_size_code = TMDB_POSTER_SIZE_LIST 
        if image_type == "profile": tmdb_img_size_code = TMDB_PROFILE_SIZE_CAST
        elif image_type == "poster_detail_hex": tmdb_img_size_code = TMDB_POSTER_SIZE_DETAIL_SRC
        elif image_type == "backdrop": tmdb_img_size_code = TMDB_BACKDROP_SIZE_DETAIL
        
        image_url = f"{TMDB_IMAGE_BASE_URL}{tmdb_img_size_code}{image_path}"
        
        cache_key = f"{image_url}_{target_size[0]}x{target_size[1]}_{image_type}_{is_detail_backdrop}_{make_circular}_{shape}"

        if cache_key in self.image_cache:
            img_label_to_update.configure(image=self.image_cache[cache_key])
            return 

        thread = threading.Thread(target=self._process_image_in_thread,
                                  args=(cache_key, image_url, target_size, image_type,
                                        is_detail_backdrop, make_circular, shape, 
                                        img_label_to_update, current_placeholder))
        thread.daemon = True
        thread.start()


    def _display_search_results_view(self, query, results_data, error_message=None):
        self.current_view = "search_results"
        if self.winfo_width() != 1000 : self.geometry("1000x720")
        
        self._clear_view_container(self.root_container)
        self.main_view_container = ctk.CTkFrame(self.root_container, fg_color=COLOR_BACKGROUND)
        self.main_view_container.pack(fill="both", expand=True)

        self.main_view_container.grid_rowconfigure(0, weight=0) 
        self.main_view_container.grid_rowconfigure(1, weight=0) 
        self.main_view_container.grid_rowconfigure(2, weight=1) 
        self.main_view_container.grid_columnconfigure(0, weight=1)

        logo_frame = self._create_logo(self.main_view_container, size=50)
        logo_frame.grid(row=0, column=0, pady=(10,10))
        
        self.search_entry = ctk.CTkEntry(
            self.main_view_container, font=ctk.CTkFont(family=self.ui_font_family, size=18), width=600, height=55,
            corner_radius=27, fg_color=COLOR_SEARCH_BAR_BG, text_color=COLOR_SEARCH_BAR_TEXT,
            placeholder_text_color=COLOR_SEARCH_BAR_PLACEHOLDER, border_color=COLOR_YELLOW_BEE, border_width=2
        )
        self.search_entry.insert(0, query)
        self.search_entry.grid(row=1, column=0, pady=(0,20))
        self.search_entry.bind("<Return>", self._trigger_search)

        if error_message:
            ctk.CTkLabel(self.main_view_container, text=error_message, font=ctk.CTkFont(family=self.ui_font_family, size=18), text_color=COLOR_ERROR_TEXT).grid(row=2, column=0, pady=20, sticky="n")
            return
        if not results_data and query:
            ctk.CTkLabel(self.main_view_container, text=f"Nenhum resultado encontrado para '{query}'.", font=ctk.CTkFont(family=self.ui_font_family, size=18), text_color=COLOR_RESULT_TEXT_DETAILS).grid(row=2, column=0, pady=20, sticky="n")
            return
        
        results_scroll_frame = ctk.CTkScrollableFrame(self.main_view_container, fg_color="transparent", scrollbar_button_color=COLOR_YELLOW_BEE, scrollbar_button_hover_color=COLOR_WHITE_VIEW)
        results_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=50)

        for item_data in results_data:
            movie_id = item_data.get("id")
            title = item_data.get("title", "N/A")
            click_callback = lambda e, mid=movie_id, mtitle=title: self._on_result_click(mtitle, mid)

            item_frame = ctk.CTkFrame(results_scroll_frame, fg_color=COLOR_RESULT_ITEM_BG, corner_radius=15, height=155)
            item_frame.pack(fill="x", pady=(5,10), padx=10)
            item_frame.bind("<Button-1>", click_callback)

            item_content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            item_content_frame.pack(fill="both", expand=True, padx=0, pady=0)
            item_content_frame.grid_columnconfigure(0, weight=0, minsize=POSTER_LIST_WIDTH + 30)
            item_content_frame.grid_columnconfigure(1, weight=1)
            item_content_frame.grid_rowconfigure(0, weight=1)
            item_content_frame.bind("<Button-1>", click_callback)
            
            img_label = ctk.CTkLabel(item_content_frame, text="", width=POSTER_LIST_WIDTH, height=POSTER_LIST_HEIGHT)
            img_label.grid(row=0, column=0, padx=(15,10), pady=10, sticky="nsw")
            img_label.bind("<Button-1>", click_callback)
            self._load_image_from_url(item_data.get("poster_path"), 
                                      (POSTER_LIST_WIDTH, POSTER_LIST_HEIGHT), 
                                      "poster_list", img_label_to_update=img_label)

            text_frame = ctk.CTkFrame(item_content_frame, fg_color="transparent")
            text_frame.grid(row=0, column=1, sticky="nsew", padx=(0,15), pady=10)
            text_frame.bind("<Button-1>", click_callback)

            title_label = ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(family=self.ui_font_family, size=18, weight="bold"), text_color=COLOR_RESULT_TEXT_TITLE, anchor="w", justify="left", wraplength=450)
            title_label.pack(pady=(0,5), fill="x", anchor="nw")
            title_label.bind("<Button-1>", click_callback)

            overview = item_data.get("overview", "Sinopse não disponível.")
            max_overview = 120 
            display_overview = (overview[:max_overview] + '...') if len(overview) > max_overview else overview
            synopsis_label = ctk.CTkLabel(text_frame, text=f"{display_overview}", font=ctk.CTkFont(family=self.ui_font_family, size=12), text_color=COLOR_RESULT_TEXT_DETAILS, wraplength=450, justify="left", anchor="w")
            synopsis_label.pack(pady=2, fill="x", anchor="nw")
            synopsis_label.bind("<Button-1>", click_callback)

            rating = item_data.get("vote_average", 0.0)
            rating_text = f"Avaliação: {rating:.1f}/10" if rating else "Avaliação: N/A"
            rating_label = ctk.CTkLabel(text_frame, text=rating_text, font=ctk.CTkFont(family=self.ui_font_family, size=13, weight="bold"), text_color=COLOR_RESULT_TEXT_DETAILS, anchor="w")
            rating_label.pack(pady=(5,0), fill="x", anchor="sw")
            rating_label.bind("<Button-1>", click_callback)

    def _on_result_click(self, movie_title, movie_id):
        if movie_id:
            print(f"Item clicado: {movie_title} (ID: {movie_id}). Buscando detalhes...")
            self._fetch_movie_details_api(movie_id, movie_title)
        else:
            print(f"Item clicado: {movie_title}, mas não possui ID.")

    def _fetch_movie_details_api(self, movie_id, fallback_title="Filme"):
        self._clear_view_container(self.root_container) 
        
        loading_label_detail = ctk.CTkLabel(self.root_container, text=f"Carregando detalhes para {fallback_title}...", text_color=COLOR_BUZZ_TEXT, font=ctk.CTkFont(family=self.ui_font_family, size=18))
        loading_label_detail.place(relx=0.5, rely=0.5, anchor="center")
        self.root_container.update_idletasks()

        detail_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {"api_key": TMDB_API_KEY, "language": "pt-BR", "append_to_response": "credits,videos"}
        try:
            response = self.http_session.get(detail_url, params=params, timeout=10)
            response.raise_for_status()
            self.current_movie_detail_data = response.json()
            if loading_label_detail.winfo_exists(): loading_label_detail.destroy()
            self._display_movie_detail_view(self.current_movie_detail_data)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar detalhes do filme (ID: {movie_id}): {e}")
            if loading_label_detail.winfo_exists(): loading_label_detail.configure(text="Erro ao carregar detalhes. Tente voltar.", text_color=COLOR_ERROR_TEXT)
            back_btn_error = ctk.CTkButton(self.root_container, text="Voltar à Pesquisa", command=self._display_initial_search_view)
            back_btn_error.place(relx=0.5, rely=0.6, anchor="center")

        except Exception as e:
            print(f"Erro inesperado ao processar detalhes: {e}")
            if loading_label_detail.winfo_exists(): loading_label_detail.configure(text="Erro inesperado ao carregar.", text_color=COLOR_ERROR_TEXT)
            back_btn_error = ctk.CTkButton(self.root_container, text="Voltar à Pesquisa", command=self._display_initial_search_view)
            back_btn_error.place(relx=0.5, rely=0.6, anchor="center")
            
    def _get_bee_classification(self, movie_data):
        vote_avg = movie_data.get("vote_average", 0.0)
        vote_count = movie_data.get("vote_count", 0)
        popularity = movie_data.get("popularity", 0.0)
        if vote_avg >= 8.0 and vote_count >= 2000 and popularity >= 150: return BEE_CLASSIFICATIONS["Queen Bee"]
        if vote_avg >= 7.8 and vote_count >= 1000 and popularity >= 100: return BEE_CLASSIFICATIONS["Queen Bee"]
        if vote_avg >= 7.0 and vote_count >= 500 and popularity >= 50: return BEE_CLASSIFICATIONS["Guard Bees"]
        if vote_avg >= 6.8 and vote_count >= 250 and popularity >= 30: return BEE_CLASSIFICATIONS["Guard Bees"]
        if vote_avg >= 5.5 and vote_count >= 100 : return BEE_CLASSIFICATIONS["Worker Bees"]
        if vote_avg >= 5.0 and vote_count >= 50 : return BEE_CLASSIFICATIONS["Worker Bees"]
        if vote_count >= 20: 
            if vote_avg < 5.0 : return BEE_CLASSIFICATIONS["Drone Bees"]
        elif vote_avg < 4.0: 
            return BEE_CLASSIFICATIONS["Drone Bees"]
        return BEE_CLASSIFICATIONS["Unclassified"]

    def _format_runtime(self, minutes):
        if not minutes or not isinstance(minutes, int): return "N/A"
        h = minutes // 60
        m = minutes % 60
        return f"{h}h {m}min" if h > 0 else f"{m}min"

    def _format_date(self, date_str, format_type="DMY"):
        if not date_str: return "N/A"
        try:
            dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if format_type == "Y": return dt_obj.strftime("%Y")
            return dt_obj.strftime("%d/%m/%Y")
        except ValueError:
            return date_str

    def _open_trailer(self, trailer_key):
        if trailer_key:
            webbrowser.open_new_tab(f"https://www.youtube.com/watch?v={trailer_key}")
        else:
            print("Nenhuma chave de trailer para abrir.")


    def _display_movie_detail_view(self, movie_data):
        self.current_view = "movie_detail"
        if self.geometry().split('x')[0] != "1280": self.geometry("1280x720")
        
        self._clear_view_container(self.root_container) 

        backdrop_label = ctk.CTkLabel(self.root_container, text="")
        backdrop_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._load_image_from_url(movie_data.get("backdrop_path"),
                                  (self.winfo_screenwidth(), self.winfo_screenheight()), 
                                  "backdrop", is_detail_backdrop=True, 
                                  img_label_to_update=backdrop_label)

        # Adjusted overlay size to be smaller
        overlay_width = self.winfo_width() * 0.80  # Reduced from 0.90
        overlay_height = self.winfo_height() * 0.85 # Reduced from 0.90
        
        overlay_content_host_frame = ctk.CTkFrame(self.root_container, fg_color=COLOR_DETAIL_OVERLAY_BG, 
                                                 width=overlay_width, height=overlay_height, corner_radius=15) 
        overlay_content_host_frame.place(relx=0.5, rely=0.5, anchor="center")
        overlay_content_host_frame.pack_propagate(False) 

        top_bar_frame = ctk.CTkFrame(overlay_content_host_frame, fg_color="transparent")
        top_bar_frame.pack(side="top", fill="x", padx=20, pady=(10,0))

        logo_detail_view = self._create_logo(top_bar_frame, size=35, command=self._display_initial_search_view) 
        logo_detail_view.pack(side="left", anchor="nw", pady=(0,5))

        back_to_results_button = ctk.CTkButton(
            top_bar_frame, text="‹ Voltar aos Resultados", 
            font=ctk.CTkFont(family=self.ui_font_family, size=14, weight="bold"),
            fg_color=COLOR_BACK_BUTTON_DETAIL_BG, text_color=COLOR_BACK_BUTTON_DETAIL_TEXT,
            hover_color=COLOR_YELLOW_BEE, corner_radius=8, height=30,
            command=lambda: self._display_search_results_view(self.last_search_query, self.last_search_results_data)
        )
        back_to_results_button.pack(side="right", anchor="ne", padx=(0,10), pady=(0,5))


        main_content_area = ctk.CTkFrame(overlay_content_host_frame, fg_color="transparent")
        main_content_area.pack(fill="both", expand=True, padx=30, pady=10)

        main_content_area.grid_columnconfigure(0, weight=3) 
        main_content_area.grid_columnconfigure(1, weight=7) 
        main_content_area.grid_rowconfigure(0, weight=1) 

        left_column_frame = ctk.CTkFrame(main_content_area, fg_color="transparent")
        left_column_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        classification = self._get_bee_classification(movie_data)
        if classification["text"]:
            bee_tag_label = ctk.CTkLabel(left_column_frame, text=classification["text"],
                                         font=ctk.CTkFont(family=self.ui_font_family, size=14, weight="bold"),
                                         fg_color=classification["fg_color"], text_color=classification["text_color"],
                                         height=26, corner_radius=13, padx=10)
            bee_tag_label.pack(anchor="nw", pady=(0, 15)) 

        hex_poster_img_label = ctk.CTkLabel(left_column_frame, text="")
        hex_poster_img_label.pack(anchor="n", pady=(0, 10))
        self._load_image_from_url(movie_data.get("poster_path"),
                                  (DETAIL_HEX_POSTER_WIDTH, DETAIL_HEX_POSTER_HEIGHT),
                                  "poster_detail_hex", shape="hexagon",
                                  img_label_to_update=hex_poster_img_label)
        
        avaliacao_frame = ctk.CTkFrame(left_column_frame, fg_color="transparent")
        avaliacao_frame.pack(anchor="n", pady=(10,0))

        ctk.CTkLabel(avaliacao_frame, text="Avaliação:", 
                     font=ctk.CTkFont(family=self.ui_font_family, size=15, weight="bold"),
                     text_color=COLOR_WHITE_VIEW).pack(side="left", padx=(0,5))
        
        ctk.CTkLabel(avaliacao_frame, text=STAR_ICON, 
                     font=ctk.CTkFont(family=self.ui_font_family, size=18), 
                     text_color=COLOR_YELLOW_BEE).pack(side="left", padx=(0,5))

        rating_value = movie_data.get("vote_average", 0.0)
        rating_display_text = f"{rating_value:.1f}/10" if rating_value else "N/A"
        
        ctk.CTkLabel(avaliacao_frame, text=rating_display_text,
                     font=ctk.CTkFont(family=self.ui_font_family, size=15),
                     text_color=COLOR_WHITE_VIEW).pack(side="left")

        right_column_frame = ctk.CTkFrame(main_content_area, fg_color="transparent")
        right_column_frame.grid(row=0, column=1, sticky="nsew")

        title_text = movie_data.get("title", "Título Indisponível")
        title_label = ctk.CTkLabel(right_column_frame, text=title_text,
                                   font=ctk.CTkFont(family=self.ui_font_family, size=28, weight="bold"), 
                                   text_color=COLOR_YELLOW_BEE, wraplength=overlay_width * 0.45, # Adjusted wraplength
                                   anchor="nw", justify="left")
        title_label.pack(anchor="nw", pady=(0, 15)) 

        details_to_display = [
            ("Título Original", movie_data.get("original_title", title_text)), 
            ("Ano de lançamento", self._format_date(movie_data.get("release_date"), format_type="Y")),
        ]
        crew = movie_data.get("credits", {}).get("crew", [])
        directors = [p["name"] for p in crew if p.get("job") == "Director"]
        director_str = ", ".join(directors[:2]) if directors else "N/A" 
        details_to_display.append(("Diretor", director_str))
        
        genres = movie_data.get("genres", [])
        genres_str = ", ".join([g["name"] for g in genres[:3]]) if genres else "N/A" 
        details_to_display.append(("Gênero", genres_str))

        countries = movie_data.get("production_countries", [])
        country_str = ", ".join([c["name"] for c in countries[:2]]) if countries else "N/A" 
        details_to_display.append(("Nacionalidade", country_str))
        details_to_display.append(("Duração", self._format_runtime(movie_data.get("runtime")))) 

        details_items_frame = ctk.CTkFrame(right_column_frame, fg_color="transparent")
        details_items_frame.pack(fill="x", anchor="nw", pady=(0,10))

        for key, value in details_to_display:
            detail_item_frame = ctk.CTkFrame(details_items_frame, fg_color="transparent")
            detail_item_frame.pack(fill="x", pady=1)
            
            key_label = ctk.CTkLabel(detail_item_frame, text=f"{key}:", 
                                     font=ctk.CTkFont(family=self.ui_font_family, size=13, weight="bold"), 
                                     text_color=COLOR_DETAIL_TEXT_KEY, anchor="w")
            key_label.pack(side="left", padx=(0,5))
            
            value_label = ctk.CTkLabel(detail_item_frame, text=value,
                                       font=ctk.CTkFont(family=self.ui_font_family, size=13), 
                                       text_color=COLOR_DETAIL_TEXT_VALUE, anchor="w", justify="left",
                                       wraplength=overlay_width * 0.35) # Adjusted wraplength
            value_label.pack(side="left", fill="x", expand=True)

        synopsis_text = movie_data.get("overview", "Sinopse não disponível.")
        synopsis_textbox_frame = ctk.CTkFrame(right_column_frame, fg_color="transparent")
        synopsis_textbox_frame.pack(fill="both", expand=True, pady=(0, 5)) 
        
        synopsis_textbox = ctk.CTkTextbox(synopsis_textbox_frame, wrap="word", activate_scrollbars=True,
                                          scrollbar_button_color=COLOR_YELLOW_BEE, fg_color="transparent",
                                          font=ctk.CTkFont(family=self.ui_font_family, size=13),
                                          text_color=COLOR_DETAIL_SYNOPSIS_TEXT, border_width=0)
        synopsis_textbox.insert("1.0", synopsis_text)
        synopsis_textbox.configure(state="disabled")
        synopsis_textbox.pack(side="top", fill="both", expand=True, pady=(0,10)) 

        bottom_actions_frame = ctk.CTkFrame(right_column_frame, fg_color="transparent")
        bottom_actions_frame.pack(side="bottom", fill="x", pady=(5, 10)) 

        trailer_key = None
        videos = movie_data.get("videos", {}).get("results", [])
        for video in videos:
            if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                trailer_key = video.get("key")
                break
        
        trailer_button = ctk.CTkButton(
            bottom_actions_frame, text="Assistir Trailer", 
            font=ctk.CTkFont(family=self.ui_font_family, size=14, weight="bold"),
            fg_color=COLOR_TRAILER_BUTTON_BG, text_color=COLOR_TRAILER_BUTTON_TEXT,
            hover_color=COLOR_TRAILER_BUTTON_HOVER, corner_radius=8, height=35,
            command=lambda k=trailer_key: self._open_trailer(k)
        )
        trailer_button.pack(side="left", padx=(0,15))

        if not trailer_key:
            trailer_button.configure(state="disabled", text="Trailer Indisponível", fg_color=COLOR_TRAILER_BUTTON_DISABLED_BG)

        lightbulb_label = ctk.CTkLabel(bottom_actions_frame, text=LIGHTBULB_ICON,
                                       font=ctk.CTkFont(family=self.ui_font_family, size=28), 
                                       text_color=COLOR_YELLOW_BEE) 
        lightbulb_label.pack(side="left")


if __name__ == "__main__":
    app = StandaloneSearchApp()
    app.mainloop()
