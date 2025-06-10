# contents/modules/oscar_brasil_app.py

import customtkinter as ctk
import requests
from PIL import Image, ImageDraw
from io import BytesIO
import math
import tkinter as tk
from datetime import date
import webbrowser # Importar webbrowser para abrir arquivos HTML
# Importar MovieDetailsWindow do homepage_model para reutilização
from contents.modules.homepage_model import MovieDetailsWindow


# --- Paleta de Cores BeeView (redefinir para consistência) ---
COLOR_BACKGROUND = "#040500"
COLOR_YELLOW_BASE = "#fff400"
COLOR_WHITE_CREAM = "#fffdd0"
COLOR_YELLOW_DARK = "#ffcf00"
COLOR_BUTTON_TEXT = COLOR_WHITE_CREAM
COLOR_YELLOW_BUTTON_TEXT = "#000000"

# --- Configurações da API TMDB ---
API_KEY = "5968e0e2ae961359489ef818f486a395"
BASE_IMAGE_URL = "https://image.tmdb.org/t/p/w200" # Tamanho para os cards da busca
MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=pt-BR" # <-- Adicione esta linha

# URL para buscar filmes brasileiros de alta avaliação (simulando "Oscar")
# Ordena por avaliação, com mínimo de votos, lançados a partir de 1990 até a data atual
OSCAR_ELIGIBLE_BRASIL_URL = (
    f"https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=pt-BR&region=BR"
    f"&sort_by=vote_average.desc&vote_count.gte=100&with_original_language=pt"
    f"&primary_release_date.gte=1990-01-01&primary_release_date.lte={date.today().strftime('%Y-%m-%d')}" # Data atual
    f"&include_adult=false"
)

# Configurações do hexágono para os resultados (mesmos da busca para consistência)
HEXAGON_OSCAR_WIDTH = 100
HEXAGON_OSCAR_HEIGHT = int(HEXAGON_OSCAR_WIDTH * 2 / math.sqrt(3))
HEXAGON_OSCAR_BORDER_COLOR = COLOR_YELLOW_BASE
HEXAGON_OSCAR_BORDER_WIDTH = 2


class OscarBrasilWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("BeeView - Brasil no Oscar")
        self.geometry("1000x700")
        self.configure(fg_color=COLOR_BACKGROUND)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Centralizar a janela em relação à janela principal
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.grab_set()
        self.focus_set()

        self.pil_image_cache = {}
        self.movie_card_images = {}
        self.movie_details_cache = {} # Cache para detalhes dos filmes da tela Oscar
        self.placeholder_image_ctk = self._create_placeholder_ctk_image((HEXAGON_OSCAR_WIDTH, HEXAGON_OSCAR_HEIGHT))

        self.total_assets_to_load = 0
        self.assets_loaded_count = 0
        self.fetched_movies = [] # Lista para armazenar os filmes buscados

        self.movie_details_window = None # Referência para a janela de detalhes do filme

        self._show_loading_screen() # Inicia com a tela de carregamento

        # --- Adicionar o botão "Análise Oscar Brasileiro" ---
        self._create_analysis_button()

    def _show_loading_screen(self):
        # Frame da tela de carregamento
        self.loading_frame = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND)
        self.loading_frame.pack(fill="both", expand=True)
        self.loading_frame.grid_columnconfigure(0, weight=1)
        self.loading_frame.grid_rowconfigure(0, weight=1)
        self.loading_frame.grid_rowconfigure(1, weight=0)
        self.loading_frame.grid_rowconfigure(2, weight=1)

        loading_label = ctk.CTkLabel(self.loading_frame, text="Carregando Filmes Brasileiros...",
                                     font=ctk.CTkFont(size=28, weight="bold"),
                                     text_color=COLOR_WHITE_CREAM)
        loading_label.grid(row=0, column=0, pady=(0, 20), sticky="s")

        self.progress_bar = ctk.CTkProgressBar(self.loading_frame, width=400, height=20, corner_radius=10,
                                               progress_color=COLOR_YELLOW_BASE, fg_color=COLOR_YELLOW_DARK)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, pady=20, sticky="n")

        self.after(100, self._start_asset_loading_process) # Inicia o processo de busca após um pequeno delay

    def _start_asset_loading_process(self):
        self.assets_loaded_count = 0
        self.total_assets_to_load = 1
        self._update_loading_progress()
        self.after(10, self._fetch_api_data_and_then_images)

    def _update_loading_progress(self):
        if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
            progress = 0
            if self.total_assets_to_load > 0:
                progress = self.assets_loaded_count / self.total_assets_to_load
            self.progress_bar.set(progress)

    def _fetch_api_data_and_then_images(self):
        if not self.winfo_exists(): return

        print("Buscando dados JSON para filmes do Oscar Brasil...")
        self.fetched_movies = self._fetch_movies_from_api(OSCAR_ELIGIBLE_BRASIL_URL)
        self.assets_loaded_count += 1
        self._update_loading_progress()
        if self.winfo_exists(): self.update_idletasks()

        if not self.winfo_exists(): return

        movies_to_process = self.fetched_movies[:20]
        self.total_assets_to_load = 1 + len(movies_to_process)

        self.all_movies_to_process = movies_to_process
        self.current_image_processing_index = 0

        if self.total_assets_to_load > 1 and self.winfo_exists():
            self.after(10, self._process_next_image)
        elif self.winfo_exists():
            self._finish_loading_and_init_ui()

    def _process_next_image(self):
        if not self.winfo_exists(): return

        if self.current_image_processing_index < len(self.all_movies_to_process):
            movie = self.all_movies_to_process[self.current_image_processing_index]
            movie_id = movie.get("id", f"oscar_unknown_{self.current_image_processing_index}")
            poster_path = movie.get("poster_path")
            image_url = f"{BASE_IMAGE_URL}{poster_path}" if poster_path else None

            self._prepare_image_versions_for_movie(movie_id, image_url)

            self.assets_loaded_count += 1
            self._update_loading_progress()
            if self.winfo_exists(): self.update_idletasks()

            self.current_image_processing_index += 1
            if self.winfo_exists(): self.after(10, self._process_next_image)
        elif self.winfo_exists():
            print("Todas as imagens processadas para Oscar Brasil.")
            self._finish_loading_and_init_ui()

    def _finish_loading_and_init_ui(self):
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()
        if self.winfo_exists(): self._create_widgets_and_display_movies()

    def _create_widgets_and_display_movies(self):
        title_font = ctk.CTkFont(size=28, weight="bold")
        title_label = ctk.CTkLabel(self, text="Baseado em popularidade e avaliação",
                                   font=title_font, text_color=COLOR_YELLOW_BASE, wraplength=900, justify="center")
        title_label.pack(pady=20, padx=20)

        self.status_label = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=14, slant="italic"),
                                         text_color="red", wraplength=800, justify="center")
        self.status_label.pack(pady=(0, 10))

        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.results_frame.grid_columnconfigure(0, weight=1)

        self._display_movies_in_grid(self.fetched_movies)


    def _fetch_movies_from_api(self, url):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.HTTPError as e:
            self.status_label.configure(text=f"Erro na API: {e.response.status_code} - {e.response.reason}")
            print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
        except requests.exceptions.ConnectionError:
            self.status_label.configure(text="Erro de conexão. Verifique sua internet.")
        except requests.exceptions.Timeout:
            self.status_label.configure(text="Tempo limite excedido. A API demorou muito para responder.")
        except requests.exceptions.RequestException as e:
            self.status_label.configure(text=f"Ocorreu um erro inesperado na busca: {e}")
        except Exception as e:
            self.status_label.configure(text=f"Ocorreu um erro interno: {e}")
        return []

    # --- Nova função para obter detalhes do filme ---
    def _get_movie_details(self, movie_id):
        if movie_id in self.movie_details_cache:
            return self.movie_details_cache[movie_id]

        url = MOVIE_DETAILS_URL.format(movie_id=movie_id, api_key=API_KEY)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            details = response.json()
            self.movie_details_cache[movie_id] = details
            return details
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar detalhes do filme {movie_id}: {e}")
            return None

    # --- Nova função para abrir a janela de detalhes ---
    def _on_movie_click(self, movie_info):
        movie_id = movie_info.get("id")
        if not movie_id:
            print("ID do filme não encontrado.")
            return

        # Verifica se a janela de detalhes já está aberta para o mesmo filme
        if self.movie_details_window is not None and self.movie_details_window.winfo_exists() and \
           getattr(self.movie_details_window, '_movie_id', None) == movie_id:
            self.movie_details_window.focus_set()
            return
        # Se a janela está aberta para outro filme, fecha a antiga
        elif self.movie_details_window is not None and self.movie_details_window.winfo_exists():
            self.movie_details_window.destroy()

        details = self._get_movie_details(movie_id)
        if not details:
            print(f"Não foi possível obter detalhes para o filme ID: {movie_id}")
            return

        # Abre a MovieDetailsWindow, passando o master da janela OscarBrasilWindow
        self.movie_details_window = MovieDetailsWindow(self.master, details, self.pil_image_cache)
        self.movie_details_window._movie_id = movie_id # Armazena o ID para verificar se é o mesmo filme
        self.movie_details_window.grab_set() # Torna a janela de detalhes modal
        self.movie_details_window.focus_set()


    def _display_movies_in_grid(self, movies_data):
        if not movies_data:
            self.status_label.configure(text="Nenhum filme encontrado com esses critérios. Tente ajustar os filtros.")
            return

        self.status_label.configure(text=f"{len(movies_data)} Filmes Brasileiros encontrados:")

        movies_per_row = 5

        row_frame = None
        for i, movie_info in enumerate(movies_data):
            if i % movies_per_row == 0:
                if row_frame:
                    row_frame.pack(fill="x", pady=5)
                row_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
                row_frame.grid_columnconfigure(0, weight=1)
                row_frame.grid_columnconfigure(movies_per_row + 1, weight=1)

            movie_id = movie_info.get("id", f"oscar_unknown_{i}")
            initial_image = self.movie_card_images.get(movie_id, {}).get("original", self.placeholder_image_ctk)

            card_frame = ctk.CTkFrame(row_frame, fg_color="transparent",
                                      width=HEXAGON_OSCAR_WIDTH + 20, height=HEXAGON_OSCAR_HEIGHT + 50)
            card_frame.pack_propagate(False)

            poster_label = ctk.CTkLabel(card_frame, text="", image=initial_image,
                                        width=HEXAGON_OSCAR_WIDTH, height=HEXAGON_OSCAR_HEIGHT)
            poster_label.pack(pady=(0,2))

            title = movie_info.get("title", "Título Desconhecido")
            title_label = ctk.CTkLabel(card_frame, text=title,
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color=COLOR_WHITE_CREAM, wraplength=HEXAGON_OSCAR_WIDTH + 10,
                                       justify="center")
            title_label.pack(pady=(0,5))

            # Adiciona o evento de clique ao poster_label e ao card_frame
            poster_label.bind("<Button-1>", lambda e, m_info=movie_info: self._on_movie_click(m_info))
            card_frame.bind("<Button-1>", lambda e, m_info=movie_info: self._on_movie_click(m_info))

            card_frame.grid(row=0, column=(i % movies_per_row) + 1, padx=5, pady=5)

        if row_frame:
            row_frame.pack(fill="x", pady=5)

    def _prepare_image_versions_for_movie(self, movie_id, image_url):
        if movie_id in self.movie_card_images: return

        pil_original = None
        if image_url:
            if movie_id in self.pil_image_cache:
                pil_original = self.pil_image_cache[movie_id]
            else:
                try:
                    response = requests.get(image_url, timeout=5)
                    response.raise_for_status()
                    img_data = response.content
                    pil_original = Image.open(BytesIO(img_data))
                    self.pil_image_cache[movie_id] = pil_original
                except Exception as e:
                    print(f"Erro ao baixar imagem ({image_url}): {e}")

        if not pil_original:
            if movie_id in self.pil_image_cache and self.pil_image_cache[movie_id].mode == 'RGBA':
                 pil_original = self.pil_image_cache[movie_id]
            else:
                pil_original = Image.new('RGBA', (HEXAGON_OSCAR_WIDTH, HEXAGON_OSCAR_HEIGHT), (50, 50, 50, 255))
                self.pil_image_cache[movie_id] = pil_original


        hex_normal_pil = self._apply_hexagonal_mask_and_border(pil_original, (HEXAGON_OSCAR_WIDTH, HEXAGON_OSCAR_HEIGHT), HEXAGON_OSCAR_BORDER_COLOR, HEXAGON_OSCAR_BORDER_WIDTH)
        ctk_normal = ctk.CTkImage(light_image=hex_normal_pil, dark_image=hex_normal_pil, size=(HEXAGON_OSCAR_WIDTH, HEXAGON_OSCAR_HEIGHT))

        self.movie_card_images[movie_id] = {"original": ctk_normal}

    def _create_hexagon_mask(self, size):
        width, height = int(size[0]), int(size[1])
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        points = [
            (width / 2, 0), (width, height / 4), (width, 3 * height / 4),
            (width / 2, height), (0, 3 * height / 4), (0, height / 4)
        ]
        draw.polygon(points, fill=255)
        return mask

    def _apply_hexagonal_mask_and_border(self, pil_image, target_hex_size, border_color, border_width):
        hex_width, hex_height = int(target_hex_size[0]), int(target_hex_size[1])
        original_width, original_height = pil_image.size
        target_aspect_ratio = hex_width / hex_height
        original_aspect_ratio = original_width / original_height

        if original_aspect_ratio > target_aspect_ratio:
            new_height = hex_height
            new_width = int(new_height * original_aspect_ratio)
        else:
            new_width = hex_width
            new_height = int(new_width / original_aspect_ratio)

        image_scaled = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - hex_width) / 2
        top = (new_height - hex_height) / 2
        right = (new_width + hex_width) / 2
        bottom = (new_height + hex_height) / 2
        image_cropped = image_scaled.crop((left, top, right, bottom))

        if image_cropped.size != (hex_width, hex_height):
            image_cropped = image_cropped.resize((hex_width, hex_height), Image.Resampling.LANCZOS)

        image_rgba = image_cropped.convert("RGBA")
        hexagon_mask = self._create_hexagon_mask((hex_width, hex_height))
        image_rgba.putalpha(hexagon_mask)

        if border_width > 0 and border_color:
            border_draw = ImageDraw.Draw(image_rgba)
            points = [
                (hex_width / 2, 0), (hex_width, hex_height / 4), (hex_width, 3 * hex_height / 4),
                (hex_width / 2, hex_height), (0, 3 * hex_height / 4), (0, hex_height / 4)
            ]
            border_draw.polygon(points, outline=border_color, width=border_width)
        return image_rgba

    def _create_placeholder_ctk_image(self, hex_size):
        placeholder_base = Image.new('RGBA', hex_size, (40, 40, 40, 255))
        placeholder_hex_pil = self._apply_hexagonal_mask_and_border(
            placeholder_base, hex_size, COLOR_YELLOW_DARK, HEXAGON_OSCAR_BORDER_WIDTH - 1
        )
        return ctk.CTkImage(light_image=placeholder_hex_pil, dark_image=placeholder_hex_pil, size=hex_size)

    def _create_analysis_button(self):
        """Cria e posiciona o botão 'Análise Oscar Brasileiro' no canto superior direito."""
        analysis_button = ctk.CTkButton(
            self,
            text="Análise Oscar Brasileiro",
            command=self._open_analysis_html,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_YELLOW_BASE,
            text_color=COLOR_YELLOW_BUTTON_TEXT,
            hover_color=COLOR_YELLOW_DARK
        )
        # Usa place para posicionar o botão no canto superior direito
        analysis_button.place(relx=0.98, rely=0.02, anchor="ne")

    def _open_analysis_html(self):
        """Abre o arquivo HTML com a análise do Oscar Brasileiro."""
        # Define o caminho para o arquivo HTML. Ajuste conforme a estrutura do seu projeto.
        # Por exemplo, se o arquivo estiver na pasta 'assets' dentro da raiz do seu projeto.
        html_file_path = "C:\\Users\\wilha\\Desktop\\BeeView -Aplicativo Definitivo\\contents\\assets\\oscar_brasil_analysis.html"  # Exemplo de caminho
        try:
            webbrowser.open(html_file_path)
        except Exception as e:
            print(f"Erro ao abrir o arquivo HTML: {e}")
            # Opcional: mostrar uma mensagem de erro na UI
            self.status_label.configure(text=f"Erro ao abrir análise: {e}")
if __name__ == "__main__":
    root_oscar = ctk.CTk()
    root_oscar.withdraw()
    oscar_app = OscarBrasilWindow(master=root_oscar)
    root_oscar.mainloop()