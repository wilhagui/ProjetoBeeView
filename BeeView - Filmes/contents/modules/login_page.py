import customtkinter as ctk
import math

class LoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login_attempt_callback, on_show_registration_callback):
        super().__init__(master, fg_color="#000000") # Main background black
        self.master = master
        self.on_login_attempt_callback = on_login_attempt_callback
        self.on_show_registration_callback = on_show_registration_callback

        # Styling constants from the image (with adjustments)
        self.PRIMARY_YELLOW = "#F5B82E"
        self.DARK_YELLOW_HOVER = "#EAA620" # Slightly darker yellow for hover
        self.TEXT_COLOR_LIGHT = "#FFFFFF"
        self.TEXT_COLOR_MEDIUM = "#DDDDDD"
        self.TEXT_COLOR_DARK_LINK = "#BBBBBB"
        self.INPUT_BG_COLOR = "#2B2B2B"    # Dark background for input fields
        
        # Adjusted hexagon outline color to be a dark, desaturated yellow/brown
        # self.HEXAGON_OUTLINE_COLOR = "#A0522D" # Original Sienna
        self.HEXAGON_OUTLINE_COLOR = "#4D401F" # Dark desaturated yellow-brown, closer to image
        
        self.HEXAGON_HOVER_FILL_COLOR = self.PRIMARY_YELLOW # Keep hover fill
        self.HEXAGON_RADIUS = 55 # Base radius for hexagons
        
        # Adjusted separator color to be lighter
        self.SEPARATOR_COLOR = "#A9A9A9" # Light gray for the vertical line (was #666666)

        self.hexagons_data = [] # Stores data for each hexagon [id, vertices, is_hovered]

        # Configure main LoginPage frame grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_hexagon_canvas()
        self._create_content_frame() # This frame will sit on top of the canvas
        self._create_widgets_in_content_frame()

        # Initial drawing of hexagons after a short delay
        self.master.after(100, self._draw_hexagons_on_resize)
        self.bg_canvas.bind("<Configure>", self._draw_hexagons_on_resize) # Redraw on resize

    def _show_error(self, message):
        # Add a check to ensure the error_label (and its parent frame) still exists
        if self.error_label and self.error_label.winfo_exists():
            self.error_label.configure(text=message)
        elif self.winfo_exists():  # Check if the LoginPage frame itself still exists
            print(f"Warning: Attempted to update error_label after it was destroyed. Message: {message}")
        else:
            print(f"Warning: Attempted to update error on a destroyed LoginPage. Message: {message}")

    # ... (rest of your code) ...

    def _create_hexagon_canvas(self):
        self.bg_canvas = ctk.CTkCanvas(self, bg="#000000", highlightthickness=0)
        self.bg_canvas.grid(row=0, column=0, sticky="nsew")
        self.bg_canvas.bind("<Motion>", self._on_canvas_mouse_move)
        self.bg_canvas.bind("<Leave>", self._on_canvas_mouse_leave)

    def _create_content_frame(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        self.content_frame.grid_columnconfigure(0, weight=45, uniform="page_sections") # Left part
        self.content_frame.grid_columnconfigure(1, weight=0)                         # Separator
        self.content_frame.grid_columnconfigure(2, weight=55, uniform="page_sections") # Right part
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _calculate_hexagon_vertices(self, center_x, center_y, radius):
        vertices = []
        for i in range(6):
            angle_deg = 60 * i - 30 # Flat top/bottom
            angle_rad = math.pi / 180 * angle_deg
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            vertices.append((x, y))
        return vertices

    def _draw_hexagons_on_resize(self, event=None):
        self.bg_canvas.delete("all_hexagons")
        self.hexagons_data = []
        
        width = self.bg_canvas.winfo_width()
        height = self.bg_canvas.winfo_height()

        if width <= 1 or height <= 1:
            self.master.after(100, self._draw_hexagons_on_resize)
            return

        # Adjusted normalized positions for hexagons to better match image distribution
        norm_hex_positions = [
            # Left side
            (0.07, 0.12, 0.8),  # Top-left corner, slightly smaller
            (0.18, 0.40, 1.0),  # Mid-left (below Email area)
            (0.10, 0.85, 1.1),  # Bottom-left (near Entrar button)

            # Right side
            (0.93, 0.15, 0.9),  # Top-right corner
            (0.82, 0.48, 1.25), # Mid-right (near logo), prominent
            (0.88, 0.83, 1.0),  # Bottom-right area
            (0.70, 0.91, 0.75)  # Lower-right, smaller
        ]

        for norm_x, norm_y, radius_scale in norm_hex_positions:
            center_x = width * norm_x
            center_y = height * norm_y
            radius = self.HEXAGON_RADIUS * radius_scale
            
            vertices = self._calculate_hexagon_vertices(center_x, center_y, radius)
            flat_vertices = [coord for point in vertices for coord in point]
            
            poly_id = self.bg_canvas.create_polygon(
                flat_vertices,
                outline=self.HEXAGON_OUTLINE_COLOR,
                fill="", 
                width=2, # Outline width
                tags="all_hexagons"
            )
            self.hexagons_data.append({"id": poly_id, "vertices": vertices, "is_hovered": False})

    def _is_point_in_polygon(self, x, y, polygon_vertices):
        num_vertices = len(polygon_vertices)
        if num_vertices < 3: return False
        inside = False
        p1x, p1y = polygon_vertices[0]
        for i in range(num_vertices + 1):
            p2x, p2y = polygon_vertices[i % num_vertices]
            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def _on_canvas_mouse_move(self, event):
        mouse_x, mouse_y = event.x, event.y
        something_hovered_now = False
        for i, hex_data in enumerate(self.hexagons_data):
            is_inside = self._is_point_in_polygon(mouse_x, mouse_y, hex_data["vertices"])
            if is_inside:
                something_hovered_now = True
                if not hex_data["is_hovered"]:
                    self.bg_canvas.itemconfig(hex_data["id"], fill=self.HEXAGON_HOVER_FILL_COLOR)
                    self.hexagons_data[i]["is_hovered"] = True
            elif hex_data["is_hovered"]: 
                self.bg_canvas.itemconfig(hex_data["id"], fill="")
                self.hexagons_data[i]["is_hovered"] = False
        
        if something_hovered_now:
            for i, hex_data in enumerate(self.hexagons_data):
                if not self._is_point_in_polygon(mouse_x, mouse_y, hex_data["vertices"]) and hex_data["is_hovered"]:
                    self.bg_canvas.itemconfig(hex_data["id"], fill="")
                    self.hexagons_data[i]["is_hovered"] = False

    def _on_canvas_mouse_leave(self, event):
        for i, hex_data in enumerate(self.hexagons_data):
            if hex_data["is_hovered"]:
                self.bg_canvas.itemconfig(hex_data["id"], fill="")
                self.hexagons_data[i]["is_hovered"] = False

    def _create_widgets_in_content_frame(self):
        # Dynamic padding based on window size - master here is the root window
        # Ensure master is ready for winfo_width/height. If this runs too early, it could be 1.
        # It's generally okay in CTk for initial setup.
        try:
            master_width = self.master.winfo_width()
            master_height = self.master.winfo_height()
            if master_width <=1 or master_height <=1: # Fallback if not yet rendered
                master_width = int(self.master.cget("width"))
                master_height = int(self.master.cget("height"))

            content_outer_padx = master_width * 0.05
            content_outer_pady = master_height * 0.1
        except: # Fallback if something goes wrong with winfo
            master_width = 960 # from your main
            master_height = 720 # from your main
            content_outer_padx = master_width * 0.05
            content_outer_pady = master_height * 0.1


        # Left Frame (for login form)
        left_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(content_outer_padx, 20), pady=content_outer_pady, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1) 
        left_frame.grid_rowconfigure(1, weight=0) 
        left_frame.grid_rowconfigure(2, weight=1) 

        form_elements_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        form_elements_frame.grid(row=1, column=0, sticky="ew")
        form_elements_frame.grid_columnconfigure(0, weight=1)

        # Vertical Separator - Adjusted padding for greater height
        separator = ctk.CTkFrame(self.content_frame, width=1.5, fg_color=self.SEPARATOR_COLOR, corner_radius=0)
        # Use a smaller pady for the separator to make it taller, aligning with content_outer_pady
        separator_pady = content_outer_pady * 0.5 # Adjust this factor as needed, 0 means full height within cell
        separator.grid(row=0, column=1, sticky="ns", pady=content_outer_pady)


        # Right Frame (for branding)
        right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=(20, content_outer_padx), pady=content_outer_pady, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1) 
        right_frame.grid_rowconfigure(1, weight=0) 
        right_frame.grid_rowconfigure(2, weight=1) 
        
        branding_content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        branding_content_frame.grid(row=1, column=0, sticky="ew") # Changed to ew for better centering if content is wide
        branding_content_frame.grid_columnconfigure(0, weight=1)

        # --- Populate Left Frame (Login Form) ---
        input_width = 300 
        input_height = 45
        input_corner_radius = 22 # Matches image's rounded inputs/button
        input_font = ctk.CTkFont(size=14)
        label_font = ctk.CTkFont(size=14) # Image labels seem similar size to input text prompt

        email_label = ctk.CTkLabel(form_elements_frame, text="Email:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        email_label.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="ew") # Increased bottom pady slightly

        self.email_entry = ctk.CTkEntry(form_elements_frame, placeholder_text="", width=input_width, height=input_height,
                                        font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                        text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=2)
        self.email_entry.grid(row=1, column=0, padx=10, pady=(0,20), sticky="ew") # Increased bottom pady

        password_label = ctk.CTkLabel(form_elements_frame, text="Senha:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        password_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew") # Increased bottom pady slightly

        self.password_entry = ctk.CTkEntry(form_elements_frame, placeholder_text="", show="*", width=input_width, height=input_height,
                                           font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                           text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=2)
        self.password_entry.grid(row=3, column=0, padx=10, pady=(0,15), sticky="ew") # Increased bottom pady

        options_frame = ctk.CTkFrame(form_elements_frame, fg_color="transparent")
        options_frame.grid(row=4, column=0, padx=10, pady=(10,15), sticky="ew") # Adjusted pady
        options_frame.grid_columnconfigure(0, weight=1) 
        options_frame.grid_columnconfigure(1, weight=0) # Give less weight to the right for forgot password or make it auto

        self.keep_logged_in_checkbox = ctk.CTkCheckBox(options_frame, text=" manter conectado",
                                                       font=ctk.CTkFont(size=12), text_color=self.TEXT_COLOR_LIGHT, # Slightly larger font
                                                       fg_color=self.PRIMARY_YELLOW, hover_color=self.DARK_YELLOW_HOVER,
                                                       checkmark_color="#000000", checkbox_width=20, checkbox_height=20, # Slightly larger
                                                       corner_radius=10)
        self.keep_logged_in_checkbox.grid(row=0, column=0, sticky="w")

        forgot_password_button = ctk.CTkButton(options_frame, text="Esqueceu a senha?",
                                             command=self._handle_forgot_password, fg_color="transparent",
                                             text_color=self.TEXT_COLOR_DARK_LINK, hover=False, # Hover managed manually
                                             font=ctk.CTkFont(size=12), anchor="e") # Slightly larger font
        forgot_password_button.grid(row=0, column=1, sticky="e", padx=(10,0)) # Add some padx to separate
        
        def on_enter_forgot(e): forgot_password_button.configure(text_color=self.PRIMARY_YELLOW, font=ctk.CTkFont(size=12, underline=True))
        def on_leave_forgot(e): forgot_password_button.configure(text_color=self.TEXT_COLOR_DARK_LINK, font=ctk.CTkFont(size=12, underline=False))
        forgot_password_button.bind("<Enter>", on_enter_forgot)
        forgot_password_button.bind("<Leave>", on_leave_forgot)

        login_button = ctk.CTkButton(form_elements_frame, text="Entrar", command=self._process_login_submission,
                                     width=input_width, height=input_height, font=ctk.CTkFont(size=16, weight="bold"), # Slightly larger
                                     fg_color=self.PRIMARY_YELLOW, text_color="#000000", hover_color=self.DARK_YELLOW_HOVER,
                                     corner_radius=input_corner_radius)
        login_button.grid(row=5, column=0, padx=10, pady=(25, 5), sticky="ew") # Increased top pady

        self.error_label = ctk.CTkLabel(form_elements_frame, text="", text_color="#FF5555", font=ctk.CTkFont(size=12), anchor="w", wraplength=input_width-20)
        self.error_label.grid(row=6, column=0, padx=10, pady=(5, 5), sticky="ew")
        self._show_error("")

        # --- Populate Right Frame (Branding) ---
        try:
            logo_font_size = max(40, min(70, int(self.master.winfo_height() / 11))) # Adjusted divisor for potentially larger logo
        except:
             logo_font_size = 60


        logo_frame = ctk.CTkFrame(branding_content_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(0,30), sticky="s") # Increased bottom pady

        bee_label = ctk.CTkLabel(logo_frame, text="Bee", font=ctk.CTkFont(size=logo_font_size, weight="bold"), text_color=self.PRIMARY_YELLOW)
        bee_label.pack(side="left", anchor="s", pady=(0,0)) 
        view_label = ctk.CTkLabel(logo_frame, text="View", font=ctk.CTkFont(size=logo_font_size, weight="bold"), text_color=self.TEXT_COLOR_LIGHT)
        view_label.pack(side="left", anchor="s", pady=(0,0))

        no_account_label_font = ctk.CTkFont(size=15) # Slightly larger
        no_account_label = ctk.CTkLabel(branding_content_frame, text="Não possue conta em nossa aplicação?",
                                        font=no_account_label_font, text_color=self.TEXT_COLOR_MEDIUM,
                                        wraplength=300, justify="center") # Increased wraplength
        no_account_label.grid(row=1, column=0, padx=20, pady=(15,8), sticky="n") # Adjusted pady

        register_button_font = ctk.CTkFont(size=15, weight="bold") # Slightly larger
        register_button_styled = ctk.CTkButton(branding_content_frame, text="Faça sua conta aqui",
                                              command=self._handle_show_registration, fg_color="transparent",
                                              text_color=self.PRIMARY_YELLOW, hover=False, # Hover managed manually
                                              font=register_button_font)
        register_button_styled.grid(row=2, column=0, padx=20, pady=(0,15), sticky="n") # Adjusted pady
        
        def on_enter_reg(e): register_button_styled.configure(font=ctk.CTkFont(size=15, weight="bold", underline=True))
        def on_leave_reg(e): register_button_styled.configure(font=ctk.CTkFont(size=15, weight="bold", underline=False))
        register_button_styled.bind("<Enter>", on_enter_reg)
        register_button_styled.bind("<Leave>", on_leave_reg)

    def _process_login_submission(self):
        username = self.email_entry.get()
        password = self.password_entry.get()
        keep_logged_in = bool(self.keep_logged_in_checkbox.get())

        if not username or not password:
            self._show_error("Email e senha são obrigatórios.")
            return
        
        # Simulate network delay for realism if desired
        # self.master.after(500, lambda: self._submit_to_callback(username, password, keep_logged_in))
        self._submit_to_callback(username, password, keep_logged_in)

    def _submit_to_callback(self, username, password, keep_logged_in):
        success, message = self.on_login_attempt_callback(username, password, keep_logged_in)
        if success:
            self._show_error("") 
        else:
            self._show_error(message)

    def _handle_show_registration(self):
        if self.on_show_registration_callback:
            self.on_show_registration_callback()

    def _show_error(self, message):
        self.error_label.configure(text=message)
        if message:
            self.error_label.grid()
        else:
            self.error_label.grid_remove()

    def _handle_forgot_password(self):
        print("Forgot password clicked")
        self._show_error("Funcionalidade 'Esqueci a senha' não implementada.")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    test_root_window = ctk.CTk()
    test_root_window.title("BeeView Login")
    test_root_window.geometry("960x720") 
    test_root_window.minsize(800, 600) 
    test_root_window.grid_columnconfigure(0, weight=1)
    test_root_window.grid_rowconfigure(0, weight=1)

    # Store the instance for potential error message updates from mock
    # This is a bit hacky for testing; usually, you wouldn't call instance._show_error from outside
    global login_frame_instance 

    def _mock_login_attempt(username, password, keep_logged_in):
        print(f"TESTE: Tentativa de login: {username}, senha: {password}, Manter conectado: {keep_logged_in}")
        if username == "test@example.com" and password == "123":
            print("TESTE: Login mock bem-sucedido!")
            # Example of how you might update UI after successful login (though typically handled by screen change)
            # login_frame_instance._show_error("Login bem-sucedido! Redirecionando...") # Test success feedback
            return True, "Login bem-sucedido!"
        return False, "Email ou senha inválidos."

    def _mock_show_registration():
        print("TESTE: Mostrar página de registro.")
        if login_frame_instance: # Check if instance exists
             login_frame_instance._show_error("Redirecionando para o registro...")


    login_frame_instance = LoginPage(master=test_root_window,
                                     on_login_attempt_callback=_mock_login_attempt,
                                     on_show_registration_callback=_mock_show_registration)
    login_frame_instance.grid(row=0, column=0, sticky="nsew")
    
    test_root_window.mainloop()