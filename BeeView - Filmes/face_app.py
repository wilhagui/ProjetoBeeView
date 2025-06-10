# face_app.py
import customtkinter as ctk
import json
import os

# Make sure these imports match your directory structure
from contents.modules.login_page import LoginPage
from contents.modules.registration_page import RegistrationPage
from contents.modules.homepage_model import HomePageTestApp # <<< UPDATED IMPORT

class MainApplication(ctk.CTk):
    """
    Classe principal da aplicação. Gerencia a janela e a troca de 'páginas' (frames).
    """
    USER_DATA_FILE = "users_data.json"
    SESSION_FILE = "session.json"

    def __init__(self):
        super().__init__()

        self.title("Meu Aplicativo BeeView")
        self.geometry("1350x950") # Adjusted to typical size for HomePageTestApp

        # Configure the main window grid to allow the content frame to expand
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_user_email = None # Changed from self.current_user to be more specific
        self.current_frame = None

        self._ensure_user_data_file()
        self._check_active_session()

    def _ensure_user_data_file(self):
        if not os.path.exists(self.USER_DATA_FILE):
            with open(self.USER_DATA_FILE, 'w') as f:
                json.dump({"users": {}}, f, indent=4)

    def _load_user_data(self):
        try:
            with open(self.USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file is corrupted or not found, create a new one
            self._ensure_user_data_file()
            return {"users": {}}

    def _save_user_data(self, data):
        with open(self.USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def _save_session(self, email): # Saving email now
        with open(self.SESSION_FILE, 'w') as f:
            json.dump({"logged_in_user_email": email}, f, indent=4)

    def _load_session(self):
        if os.path.exists(self.SESSION_FILE):
            try:
                with open(self.SESSION_FILE, 'r') as f:
                    session_data = json.load(f)
                    return session_data.get("logged_in_user_email")
            except (FileNotFoundError, json.JSONDecodeError):
                return None
        return None

    def _clear_session(self):
        if os.path.exists(self.SESSION_FILE):
            os.remove(self.SESSION_FILE)

    def _check_active_session(self):
        logged_in_user_email = self._load_session()
        if logged_in_user_email:
            users_data = self._load_user_data()
            if logged_in_user_email in users_data.get("users", {}):
                self.current_user_email = logged_in_user_email
                print(f"MainApplication: Usuário '{self.current_user_email}' restaurado da sessão.")
                self._show_main_content_page() # Show HomePageTestApp directly
                return
            else:
                self._clear_session() # User in session but not in DB, clear session
        self._show_login_page()

    def _handle_login_attempt(self, email, password, keep_logged_in): # Parameter changed to email
        users_data = self._load_user_data()
        user_credentials = users_data.get("users", {})

        # Adjusted to check new user data structure
        if email in user_credentials and user_credentials[email].get("password") == password:
            self.current_user_email = email
            print(f"MainApplication: Usuário '{email}' logado com sucesso!")

            if keep_logged_in:
                self._save_session(email)
            else:
                self._clear_session() # Ensure session is cleared if not kept

            if self.current_frame: # Destroy login frame
                self.current_frame.destroy()
                self.current_frame = None
            self._show_main_content_page() # Show HomePageTestApp
            return True, "Login bem-sucedido!"
        else:
            return False, "Email ou senha inválidos."

    # --- MÉTODO CORRIGIDO ---
    def _handle_registration_attempt(self, email, password, date_of_birth): # Signature changed
        users_data = self._load_user_data()
        users = users_data.get("users", {}) # This is a dictionary of users

        if not email.strip() or not password.strip(): # Assuming email is used as username
             return False, "Email e senha não podem ser vazios."
        if not date_of_birth or date_of_birth.count('-') != 2: # Basic check for DOB format
            return False, "Data de nascimento inválida."
        if email in users:
            return False, "Este email já está registrado."

        # Store user data with new structure
        users[email] = {
            "password": password,
            "dob": date_of_birth
        }
        # users_data["users"] = users # Ensure 'users' dict is correctly assigned back if it was copied
        self._save_user_data(users_data) # users_data already holds the reference to the 'users' dict
        
        print(f"MainApplication: Usuário '{email}' (DOB: {date_of_birth}) registrado com sucesso!")
        return True, "Registro bem-sucedido! Faça o login."
    # --- FIM DA CORREÇÃO ---

    def _show_login_page(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        
        self.geometry("1000x700") # Resize for login/registration
        
        login_frame = LoginPage(
            master=self,
            on_login_attempt_callback=self._handle_login_attempt,
            on_show_registration_callback=self._show_registration_page
        )
        # login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="") # sticky="" can cause issues
        login_frame.grid(row=0, column=0, sticky="nsew") # Make it expand
        self.current_frame = login_frame


    def _show_registration_page(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

        self.geometry("1000x700") # Resize for login/registration

        registration_frame = RegistrationPage(
            master=self,
            on_register_attempt_callback=self._handle_registration_attempt,
            on_show_login_callback=self._show_login_page
        )
        # registration_frame.grid(row=0, column=0, padx=20, pady=20, sticky="")
        registration_frame.grid(row=0, column=0, sticky="nsew") # Make it expand
        self.current_frame = registration_frame

    def _show_main_content_page(self):
        """Cria e exibe a HomePageTestApp após o login."""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
        
        self.geometry("1350x950") # Resize for main content

        home_page_instance = HomePageTestApp(
            master=self,
            current_user=self.current_user_email, # Pass the email
            logout_callback=self._logout
        )
        home_page_instance.grid(row=0, column=0, sticky="nsew")
        self.current_frame = home_page_instance

    def _logout(self):
        """Realiza o logout do usuário e volta para a tela de login."""
        print(f"MainApplication: Usuário '{self.current_user_email}' deslogado.")
        
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
            
        self.current_user_email = None
        self._clear_session()
        self._show_login_page()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    # ctk.set_default_color_theme("blue") # Keep or change as you like

    app = MainApplication()
    app.mainloop()