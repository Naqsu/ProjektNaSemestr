import json
import hashlib
import os
from utils import log_event, create_directory_if_not_exists, COLOR_RED, COLOR_GREEN

USERS_FILE = 'users.json'
class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

    def to_dict(self):
        return {"username": self.username, "password_hash": self.password_hash}

    @staticmethod
    def from_dict(data):
        return User(data["username"], data["password_hash"])

class AuthService:
    def __init__(self):
        self.users = self._load_users()
        log_event(f"AuthService zainicjalizowany, załadowano {len(self.users)} użytkowników.", level="DEBUG")

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self):
        if not os.path.exists(USERS_FILE):
            log_event(f"Plik użytkowników {USERS_FILE} nie istnieje. Zwracam pusty słownik.", level="INFO")
            return {}
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
                log_event(f"Załadowano dane użytkowników z {USERS_FILE}.", level="DEBUG")
                return users_data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            log_event(f"Błąd podczas ładowania pliku użytkowników {USERS_FILE}: {e}", level="ERROR", color=COLOR_RED)
            return {}

    def _save_users(self):
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(self.users, f, indent=4)
            log_event(f"Zapisano dane użytkowników do {USERS_FILE}.", level="DEBUG")
        except IOError as e:
            log_event(f"Błąd podczas zapisywania danych użytkowników do {USERS_FILE}: {e}", level="ERROR", color=COLOR_RED)


    def register(self, username, password):
        if not username or not password:
            log_event(f"Próba rejestracji z pustą nazwą użytkownika lub hasłem.", level="WARNING")
            return False, "Nazwa użytkownika i hasło nie mogą być puste."
        if username in self.users:
            log_event(f"Nieudana próba rejestracji: użytkownik '{username}' już istnieje.", level="INFO")
            return False, "Użytkownik o tej nazwie już istnieje."
        
        hashed_password = self._hash_password(password)
        self.users[username] = hashed_password
        self._save_users()
        log_event(f"Użytkownik '{username}' zarejestrowany pomyślnie.", level="INFO", color=COLOR_GREEN)
        return True, "Rejestracja zakończona sukcesem."

    def login(self, username, password):
        if not username or not password:
            log_event(f"Próba logowania z pustą nazwą użytkownika lub hasłem.", level="WARNING")
            return False, "Nazwa użytkownika i hasło nie mogą być puste."
        
        stored_password_hash = self.users.get(username)
        if not stored_password_hash:
            log_event(f"Nieudana próba logowania: użytkownik '{username}' nie znaleziony.", level="INFO")
            return False, "Nieprawidłowa nazwa użytkownika lub hasło."
        
        hashed_password = self._hash_password(password)
        if hashed_password == stored_password_hash:
            log_event(f"Użytkownik '{username}' zalogowany pomyślnie.", level="INFO", color=COLOR_GREEN)
            return True, "Logowanie zakończone sukcesem."
        else:
            log_event(f"Nieudana próba logowania dla użytkownika '{username}': nieprawidłowe hasło.", level="INFO", color=COLOR_RED)
            return False, "Nieprawidłowa nazwa użytkownika lub hasło."