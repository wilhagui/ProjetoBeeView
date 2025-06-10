import customtkinter as ctk
from datetime import datetime # For year calculation in DOB
# math is no longer needed as hexagons are removed

class RegistrationPage(ctk.CTkFrame):
    def __init__(self, master, on_register_attempt_callback, on_show_login_callback):
        super().__init__(master, fg_color="#000000") # Main background black
        self.master = master
        self.on_register_attempt_callback = on_register_attempt_callback
        self.on_show_login_callback = on_show_login_callback

        # Styling constants
        self.PRIMARY_YELLOW = "#F5B82E"
        self.DARK_YELLOW_HOVER = "#EAA620"
        self.INPUT_BG_COLOR = "#2B2B2B"
        self.TEXT_COLOR_LIGHT = "#FFFFFF"
        self.TEXT_COLOR_MEDIUM = "#DDDDDD"
        self.TEXT_COLOR_DARK_LINK = "#BBBBBB"
        self.SEPARATOR_COLOR = "#666666"

        # Configure main RegistrationPage frame grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Hexagon related attributes and calls are removed

        self._create_content_layout() # Sets up top bar and main columns area
        self._populate_widgets()      # Fills the layout with widgets

    def _create_content_layout(self):
        # This frame sits directly on RegistrationPage and holds all visible UI content
        self.content_area_frame = ctk.CTkFrame(self, fg_color="transparent") # Parent is self
        self.content_area_frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=25)

        self.content_area_frame.grid_rowconfigure(0, weight=0) # Top bar (fixed height)
        self.content_area_frame.grid_rowconfigure(1, weight=1) # Main content (two columns)
        self.content_area_frame.grid_columnconfigure(0, weight=1) # Spans full width

        # Top Bar Frame
        self.top_bar_frame = ctk.CTkFrame(self.content_area_frame, fg_color="transparent", height=50)
        self.top_bar_frame.grid(row=0, column=0, sticky="new", pady=(0, 25))
        self.top_bar_frame.grid_columnconfigure(0, weight=1) # Logo
        self.top_bar_frame.grid_columnconfigure(1, weight=0) # Spacer
        self.top_bar_frame.grid_columnconfigure(2, weight=1) # Back link

        # Main Columns Frame (below top bar)
        self.main_columns_frame = ctk.CTkFrame(self.content_area_frame, fg_color="transparent")
        self.main_columns_frame.grid(row=1, column=0, sticky="nsew")

        # Configure the two columns and separator
        self.main_columns_frame.grid_columnconfigure(0, weight=45, uniform="page_cols") # Left form
        self.main_columns_frame.grid_columnconfigure(1, weight=0)                       # Separator
        self.main_columns_frame.grid_columnconfigure(2, weight=55, uniform="page_cols") # Right form
        self.main_columns_frame.grid_rowconfigure(0, weight=1)


    def _populate_widgets(self):
        # --- Populate Top Bar ---
        logo_font_size = 32
        
        logo_container = ctk.CTkFrame(self.top_bar_frame, fg_color="transparent")
        logo_container.grid(row=0, column=0, sticky="w")
        bee_label = ctk.CTkLabel(logo_container, text="Bee", font=ctk.CTkFont(size=logo_font_size, weight="bold"), text_color=self.PRIMARY_YELLOW)
        bee_label.pack(side="left")
        view_label = ctk.CTkLabel(logo_container, text="View", font=ctk.CTkFont(size=logo_font_size, weight="bold"), text_color=self.TEXT_COLOR_LIGHT)
        view_label.pack(side="left", padx=(2,0))

        back_arrow_char = "←" # Unicode left arrow
        back_to_login_button = ctk.CTkButton(self.top_bar_frame, text=f"{back_arrow_char} Voltar pra tela de login",
                                             command=self._handle_show_login,
                                             fg_color="transparent", text_color=self.TEXT_COLOR_MEDIUM,
                                             hover=False, font=ctk.CTkFont(size=13))
        back_to_login_button.grid(row=0, column=2, sticky="e")
        def on_enter_back(e): back_to_login_button.configure(text_color=self.PRIMARY_YELLOW)
        def on_leave_back(e): back_to_login_button.configure(text_color=self.TEXT_COLOR_MEDIUM)
        back_to_login_button.bind("<Enter>", on_enter_back)
        back_to_login_button.bind("<Leave>", on_leave_back)

        # --- Prepare Left and Right Content Frames ---
        self.left_form_content = ctk.CTkFrame(self.main_columns_frame, fg_color="transparent")
        self.left_form_content.grid(row=0, column=0, padx=(20,10), pady=10, sticky="nsew")
        self.left_form_content.grid_columnconfigure(0, weight=1)
        self.left_form_content.grid_rowconfigure(0, weight=1) 
        self.left_form_content.grid_rowconfigure(1, weight=0) 
        self.left_form_content.grid_rowconfigure(2, weight=1) 
        
        left_inner_frame = ctk.CTkFrame(self.left_form_content, fg_color="transparent")
        left_inner_frame.grid(row=1, column=0, sticky="ew")
        left_inner_frame.grid_columnconfigure(0, weight=1)


        separator = ctk.CTkFrame(self.main_columns_frame, width=1.5, fg_color=self.SEPARATOR_COLOR, corner_radius=0)
        separator.grid(row=0, column=1, sticky="ns", pady=20)

        self.right_form_content = ctk.CTkFrame(self.main_columns_frame, fg_color="transparent")
        self.right_form_content.grid(row=0, column=2, padx=(10,20), pady=10, sticky="nsew")
        self.right_form_content.grid_columnconfigure(0, weight=1)
        self.right_form_content.grid_rowconfigure(0, weight=1) 
        self.right_form_content.grid_rowconfigure(1, weight=0) 
        self.right_form_content.grid_rowconfigure(2, weight=1) 
        
        right_inner_frame = ctk.CTkFrame(self.right_form_content, fg_color="transparent")
        right_inner_frame.grid(row=1, column=0, sticky="ew")
        right_inner_frame.grid_columnconfigure(0, weight=1)

        # --- Populate Left Form (Email, Passwords) ---
        input_width = 280 
        input_height = 42
        input_corner_radius = 21
        input_font = ctk.CTkFont(size=13)
        label_font = ctk.CTkFont(size=13)

        email_label = ctk.CTkLabel(left_inner_frame, text="Email:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        email_label.grid(row=0, column=0, padx=5, pady=(0, 2), sticky="ew")
        self.email_entry = ctk.CTkEntry(left_inner_frame, placeholder_text="", width=input_width, height=input_height,
                                           font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                           text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=1.5)
        self.email_entry.grid(row=1, column=0, padx=5, pady=(0,12), sticky="ew")

        password_label = ctk.CTkLabel(left_inner_frame, text="Senha:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        password_label.grid(row=2, column=0, padx=5, pady=(0, 2), sticky="ew")
        self.password_entry = ctk.CTkEntry(left_inner_frame, placeholder_text="", show="*", width=input_width, height=input_height,
                                            font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                            text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=1.5)
        self.password_entry.grid(row=3, column=0, padx=5, pady=(0,12), sticky="ew")

        confirm_password_label = ctk.CTkLabel(left_inner_frame, text="Repetir senha:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        confirm_password_label.grid(row=4, column=0, padx=5, pady=(0, 2), sticky="ew")
        self.confirm_password_entry = ctk.CTkEntry(left_inner_frame, placeholder_text="", show="*", width=input_width, height=input_height,
                                                    font=input_font, fg_color=self.INPUT_BG_COLOR, border_color=self.PRIMARY_YELLOW,
                                                    text_color=self.TEXT_COLOR_LIGHT, corner_radius=input_corner_radius, border_width=1.5)
        self.confirm_password_entry.grid(row=5, column=0, padx=5, pady=(0,12), sticky="ew")
        
        self.message_label = ctk.CTkLabel(left_inner_frame, text="", font=ctk.CTkFont(size=11), wraplength=input_width-10, justify="left")
        self.message_label.grid(row=6, column=0, padx=5, pady=(8,0), sticky="ew")
        self._set_message("", "green") 

        # --- Populate Right Form (DOB, Terms, Register Button) ---
        dob_label = ctk.CTkLabel(right_inner_frame, text="Data de nascimento:", font=label_font, text_color=self.TEXT_COLOR_LIGHT, anchor="w")
        dob_label.grid(row=0, column=0, padx=5, pady=(0,3), sticky="ew")

        dob_frame = ctk.CTkFrame(right_inner_frame, fg_color="transparent")
        dob_frame.grid(row=1, column=0, padx=5, pady=(0,18), sticky="ew")
        dob_frame.grid_columnconfigure(0, weight=1, uniform="dob")
        dob_frame.grid_columnconfigure(1, weight=1, uniform="dob")
        dob_frame.grid_columnconfigure(2, weight=1, uniform="dob")
        
        dob_opt_height = 38
        dob_opt_fg = self.INPUT_BG_COLOR
        dob_opt_button_color = "#4D4D4D" 
        dob_opt_text_color = self.TEXT_COLOR_MEDIUM
        dob_opt_corner_radius = 19

        days = ["Dia"] + [str(i) for i in range(1, 32)]
        months = ["Mês"] + [str(i) for i in range(1, 13)]
        current_year = datetime.now().year
        years = ["Ano"] + [str(i) for i in range(current_year - 100, current_year - 12)] 

        self.day_combobox = ctk.CTkOptionMenu(dob_frame, values=days, height=dob_opt_height, width=75,
                                              fg_color=dob_opt_fg, button_color=dob_opt_button_color, text_color=dob_opt_text_color,
                                              dropdown_fg_color=dob_opt_fg, corner_radius=dob_opt_corner_radius,
                                              font=ctk.CTkFont(size=12))
        self.day_combobox.grid(row=0, column=0, padx=(0,4), sticky="ew")

        self.month_combobox = ctk.CTkOptionMenu(dob_frame, values=months, height=dob_opt_height, width=75,
                                                fg_color=dob_opt_fg, button_color=dob_opt_button_color, text_color=dob_opt_text_color,
                                                dropdown_fg_color=dob_opt_fg, corner_radius=dob_opt_corner_radius,
                                                font=ctk.CTkFont(size=12))
        self.month_combobox.grid(row=0, column=1, padx=4, sticky="ew")

        self.year_combobox = ctk.CTkOptionMenu(dob_frame, values=years, height=dob_opt_height, width=90,
                                               fg_color=dob_opt_fg, button_color=dob_opt_button_color, text_color=dob_opt_text_color,
                                               dropdown_fg_color=dob_opt_fg, corner_radius=dob_opt_corner_radius,
                                               font=ctk.CTkFont(size=12))
        self.year_combobox.grid(row=0, column=2, padx=(4,0), sticky="ew")

        terms_frame = ctk.CTkFrame(right_inner_frame, fg_color="transparent")
        terms_frame.grid(row=2, column=0, padx=5, pady=(8,12), sticky="ew")
        terms_frame.grid_columnconfigure(0, weight=0) 
        terms_frame.grid_columnconfigure(1, weight=1) 

        self.terms_checkbox = ctk.CTkCheckBox(terms_frame, text="", 
                                               fg_color=self.PRIMARY_YELLOW, hover_color=self.DARK_YELLOW_HOVER,
                                               checkmark_color="#000000", checkbox_width=17, checkbox_height=17,
                                               corner_radius=8)
        self.terms_checkbox.grid(row=0, column=0, pady=(0,0), sticky="nw", padx=(0,3))

        terms_text = "Aceite os Termos: Ao continuar, você concorda com nossos Termos de Uso e Política de Privacidade."
        terms_label = ctk.CTkLabel(terms_frame, text=terms_text, font=ctk.CTkFont(size=10), 
                                   text_color=self.TEXT_COLOR_MEDIUM, wraplength=input_width - 40, 
                                   justify="left", anchor="w")
        terms_label.grid(row=0, column=1, sticky="ew")

        register_button = ctk.CTkButton(right_inner_frame, text="Registrar", command=self._handle_registration_attempt,
                                        width=input_width, height=input_height, font=ctk.CTkFont(size=14, weight="bold"),
                                        fg_color=self.PRIMARY_YELLOW, text_color="#000000", hover_color=self.DARK_YELLOW_HOVER,
                                        corner_radius=input_corner_radius)
        register_button.grid(row=3, column=0, padx=5, pady=(18,0), sticky="ew")

    def _handle_registration_attempt(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        day = self.day_combobox.get()
        month = self.month_combobox.get()
        year = self.year_combobox.get()
        terms_accepted = bool(self.terms_checkbox.get())

        if not email or not password or not confirm_password:
            self._set_message("Todos os campos de texto são obrigatórios.", "red")
            return
        if day == "Dia" or month == "Mês" or year == "Ano": 
            self._set_message("Por favor, selecione sua data de nascimento completa.", "red")
            return
        if password != confirm_password:
            self._set_message("As senhas não coincidem.", "red")
            return
        if len(password) < 6:
            self._set_message("A senha deve ter pelo menos 6 caracteres.", "red")
            return
        if not terms_accepted:
            self._set_message("Você deve aceitar os Termos para continuar.", "red")
            return

        date_of_birth = f"{year}-{month.zfill(2)}-{day.zfill(2)}" 
        # A linha abaixo chama o callback.
        # Certifique-se de que o método MainApplication._handle_registration_attempt
        # em face_app.py está definido para aceitar self, email, password e date_of_birth.
        success, message = self.on_register_attempt_callback(email, password, date_of_birth)

        if success:
            self._set_message(message, "green")
            self.email_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
            self.confirm_password_entry.delete(0, 'end')
            self.day_combobox.set("Dia") 
            self.month_combobox.set("Mês") 
            self.year_combobox.set("Ano") 
            self.terms_checkbox.deselect()
        else:
            self._set_message(message, "red")

    def _handle_show_login(self):
        if self.on_show_login_callback:
            self.on_show_login_callback()

    def _set_message(self, message, color):
        self.message_label.configure(text=message, text_color=color)
        if message:
            self.message_label.grid()
        else:
            self.message_label.grid_remove()

# --- Test Block ---
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    test_root = ctk.CTk()
    test_root.title("Teste - Página de Registro BeeView (Sem Hexágonos)")
    test_root.geometry("1000x700") 
    test_root.minsize(850, 650)
    test_root.grid_columnconfigure(0, weight=1)
    test_root.grid_rowconfigure(0, weight=1)

    def _mock_register_attempt(email, password, dob): # Este mock aceita 3 argumentos
        print(f"TESTE: Registrar: Email='{email}', Senha='{len(password)} chars', DOB='{dob}'")
        if not email.endswith("@example.com"): 
            return False, "Por favor, use um email '@example.com' para teste."
        if email == "registered@example.com": 
             return False, "Este email já está registrado."
        return True, "Registro bem-sucedido! Faça o login."

    def _mock_show_login():
        print("TESTE: Mostrar página de login.")

    reg_page = RegistrationPage(test_root,
                                on_register_attempt_callback=_mock_register_attempt,
                                on_show_login_callback=_mock_show_login)
    reg_page.grid(row=0, column=0, sticky="nsew")
    test_root.mainloop()