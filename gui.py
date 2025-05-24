import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
from items import Potion
from utils import log_event, COLOR_CYAN, format_currency

class RPGInterface:

    def __init__(self, root, auth_service, game_logic_service):
        self.root = root
        self.auth = auth_service
        self.game = game_logic_service
        self.current_username = None
        self.root.title('Proste RPG v1.1')
        self.root.geometry('850x650')
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', padding=6, relief='flat', font=('Helvetica', 10))
        self.style.configure('Big.TButton', font=('Helvetica', 12, 'bold'))
        self.style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        self.style.configure('Status.TLabel', font=('Courier', 10), anchor='nw')
        self.style.configure('Inventory.TLabel', font=('Courier', 9), anchor='nw')
        self.create_login_screen()
        log_event('RPGInterface zainicjalizowane.', level='DEBUG', color=COLOR_CYAN)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        log_event('Ekran wyczyszczony.', level='DEBUG')

    def create_login_screen(self):
        self.clear_screen()
        self.current_username = None
        if self.game:
            self.game.player = None
        login_frame = ttk.Frame(self.root, padding='20')
        login_frame.pack(expand=True)
        ttk.Label(login_frame, text='Logowanie / Rejestracja', style='Header.TLabel').pack(pady=10)
        ttk.Label(login_frame, text='Nazwa użytkownika:').pack(pady=5)
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.pack()
        ttk.Label(login_frame, text='Hasło:').pack(pady=5)
        self.password_entry = ttk.Entry(login_frame, show='*', width=30)
        self.password_entry.pack()
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text='Zaloguj', command=self.handle_login, style='Big.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='Zarejestruj', command=self.handle_register, style='Big.TButton').pack(side=tk.LEFT, padx=10)
        self.login_status_label = ttk.Label(login_frame, text='')
        self.login_status_label.pack(pady=10)
        log_event('Utworzono ekran logowania.', level='DEBUG')

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        log_event(f'Próba logowania użytkownika: {username}', level='DEBUG')
        success, message = self.auth.login(username, password)
        self.login_status_label.config(text=message)
        if success:
            self.current_username = username
            self.show_character_or_game_screen()

    def handle_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        log_event(f'Próba rejestracji użytkownika: {username}', level='DEBUG')
        success, message = self.auth.register(username, password)
        self.login_status_label.config(text=message)
        if success:
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            messagebox.showinfo('Rejestracja', 'Rejestracja udana! Możesz się teraz zalogować.')

    def show_character_or_game_screen(self):
        self.clear_screen()
        if self.game.load_game(self.current_username):
            self.create_main_game_screen()
            log_event(f'Gra wczytana dla {self.current_username}, przejście do ekranu gry.', level='INFO')
        else:
            self.create_character_creation_screen()
            log_event(f'Brak zapisu dla {self.current_username} lub błąd wczytania, przejście do tworzenia postaci.', level='INFO')

    def create_character_creation_screen(self):
        self.clear_screen()
        char_frame = ttk.Frame(self.root, padding='20')
        char_frame.pack(expand=True)
        ttk.Label(char_frame, text='Stwórz Postać', style='Header.TLabel').pack(pady=10)
        ttk.Label(char_frame, text='Nazwa Postaci:').pack(pady=5)
        self.char_name_entry = ttk.Entry(char_frame, width=30)
        self.char_name_entry.pack()
        if self.current_username:
            self.char_name_entry.insert(0, self.current_username)
        ttk.Label(char_frame, text='Wybierz klasę:').pack(pady=5)
        self.class_var = tk.StringVar(value='Wojownik')
        ttk.Radiobutton(char_frame, text='Wojownik (HP:100, Atk:10, Def:5)', variable=self.class_var, value='Wojownik').pack(anchor=tk.W)
        ttk.Radiobutton(char_frame, text='Mag (HP:70, Atk:8+broń, Def:3)', variable=self.class_var, value='Mag').pack(anchor=tk.W)
        ttk.Button(char_frame, text='Rozpocznij Grę', command=self.handle_start_new_game, style='Big.TButton').pack(pady=20)
        ttk.Button(char_frame, text='Wróć do logowania', command=self.create_login_screen).pack()
        log_event('Utworzono ekran tworzenia postaci.', level='DEBUG')

    def handle_start_new_game(self):
        char_name = self.char_name_entry.get()
        char_class = self.class_var.get()
        if not char_name:
            messagebox.showerror('Błąd', 'Nazwa postaci nie może być pusta.')
            return
        log_event(f'Rozpoczęcie nowej gry: Imię={char_name}, Klasa={char_class}', level='INFO')
        self.game.create_new_player(char_name, char_class)
        self.create_main_game_screen()

    def create_main_game_screen(self):
        self.clear_screen()
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_frame, weight=3)
        ttk.Label(left_frame, text='Log Gry:', style='Header.TLabel').pack(anchor=tk.NW)
        self.log_text = scrolledtext.ScrolledText(left_frame, height=20, width=70, wrap=tk.WORD, state=tk.DISABLED, font=('Arial', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        status_frame = ttk.Frame(left_frame)
        status_frame.pack(fill=tk.X, pady=5)
        self.player_status_label = ttk.Label(status_frame, text='Status Gracza:', style='Status.TLabel', justify=tk.LEFT)
        self.player_status_label.pack(anchor=tk.NW, fill=tk.X, pady=2)
        self.enemy_status_label = ttk.Label(status_frame, text='Status Wroga:', style='Status.TLabel', justify=tk.LEFT)
        self.enemy_status_label.pack(anchor=tk.NW, fill=tk.X, pady=2)
        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=2)
        actions_frame = ttk.LabelFrame(right_frame, text='Akcje Główne', padding=10)
        actions_frame.pack(fill=tk.X, pady=5)
        self.explore_button = ttk.Button(actions_frame, text='Eksploruj', command=self.game.explore)
        self.explore_button.pack(fill=tk.X, pady=2)
        self.save_button = ttk.Button(actions_frame, text='Zapisz Grę', command=lambda: self.game.save_game(self.current_username))
        self.save_button.pack(fill=tk.X, pady=2)
        self.logout_button = ttk.Button(actions_frame, text='Wyloguj', command=self.create_login_screen)
        self.logout_button.pack(fill=tk.X, pady=2)
        self.combat_frame = ttk.LabelFrame(right_frame, text='Walka', padding=10)
        self.combat_frame.pack(fill=tk.X, pady=5)
        self.attack_button = ttk.Button(self.combat_frame, text='Atakuj', command=lambda: self.game.player_action_combat('attack'))
        self.attack_button.pack(fill=tk.X, pady=2)
        self.block_button = ttk.Button(self.combat_frame, text='Blokuj', command=lambda: self.game.player_action_combat('block'))
        self.block_button.pack(fill=tk.X, pady=2)
        self.use_potion_button = ttk.Button(self.combat_frame, text='Użyj Mikstury (Walka)', command=self.handle_use_potion_combat)
        self.use_potion_button.pack(fill=tk.X, pady=2)
        self.flee_button = ttk.Button(self.combat_frame, text='Uciekaj', command=self.game.flee_combat)
        self.flee_button.pack(fill=tk.X, pady=2)
        self.update_combat_buttons_visibility(False)
        inventory_frame = ttk.LabelFrame(right_frame, text='Ekwipunek', padding=10)
        inventory_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.inventory_text = scrolledtext.ScrolledText(inventory_frame, height=10, width=45, wrap=tk.WORD, state=tk.DISABLED, font=('Courier', 9))
        self.inventory_text.pack(fill=tk.BOTH, expand=True, pady=5)
        item_action_frame = ttk.Frame(inventory_frame)
        item_action_frame.pack(fill=tk.X)
        ttk.Label(item_action_frame, text='Nr:').pack(side=tk.LEFT, padx=(0, 2))
        self.item_entry = ttk.Entry(item_action_frame, width=4)
        self.item_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.item_entry.insert(0, '1')
        self.use_item_button = ttk.Button(item_action_frame, text='Użyj/Wyposaż', command=self.handle_use_inventory_item)
        self.use_item_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        log_event('Utworzono główny ekran gry.', level='DEBUG')
        if self.game.player:
            self.game.update_gui()
            if self.game.is_in_combat:
                self.update_combat_buttons_visibility(True)
        else:
            self.log_message('Błąd krytyczny: Brak danych gracza na głównym ekranie gry. Spróbuj wczytać grę ponownie lub stwórz nową postać.')
            log_event('Krytyczny błąd: Brak gracza na ekranie gry.', level='ERROR', color=COLOR_CYAN)

    def handle_use_inventory_item(self):
        item_num_str = self.item_entry.get()
        log_event(f'GUI: Próba użycia/wyposażenia przedmiotu z ekwipunku nr: {item_num_str}', level='DEBUG')
        self.game.use_inventory_item(item_num_str)

    def handle_use_potion_combat(self):
        if not self.game.player or not self.game.is_in_combat:
            return
        potions_in_inventory = [(i, item.name) for i, item in enumerate(self.game.player.inventory) if isinstance(item, Potion)]
        if not potions_in_inventory:
            self.log_message('Nie masz żadnych mikstur w ekwipunku.')
            return
        potion_name_to_use = simpledialog.askstring('Użyj Mikstury', 'Wpisz nazwę mikstury do użycia:', parent=self.root)
        if potion_name_to_use:
            log_event(f"GUI: Próba użycia mikstury '{potion_name_to_use}' w walce.", level='DEBUG')
            self.game.player_action_combat('use_potion', potion_name_to_use)
        else:
            self.log_message('Anulowano użycie mikstury.')

    def log_message(self, message):
        if hasattr(self, 'log_text'):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
        else:
            print(f'GUI_LOG_FALLBACK: {message}')

    def update_status_labels(self, player_status, enemy_status, inventory_listing):
        if hasattr(self, 'player_status_label'):
            self.player_status_label.config(text=player_status)
        if hasattr(self, 'enemy_status_label'):
            self.enemy_status_label.config(text=enemy_status)
        if hasattr(self, 'inventory_text'):
            self.inventory_text.config(state=tk.NORMAL)
            self.inventory_text.delete(1.0, tk.END)
            self.inventory_text.insert(tk.END, inventory_listing)
            self.inventory_text.config(state=tk.DISABLED)

    def update_combat_buttons_visibility(self, is_combat_active):
        if hasattr(self, 'attack_button'):
            can_act_in_combat = is_combat_active and self.game.player and self.game.player.is_alive()
            combat_button_state = tk.NORMAL if can_act_in_combat else tk.DISABLED
            self.attack_button.config(state=combat_button_state)
            self.block_button.config(state=combat_button_state)
            self.use_potion_button.config(state=combat_button_state)
            self.flee_button.config(state=combat_button_state)
            can_explore = not is_combat_active and self.game.player and self.game.player.is_alive()
            explore_state = tk.NORMAL if can_explore else tk.DISABLED
            self.explore_button.config(state=explore_state)
            can_save = not is_combat_active and self.game.player and self.game.player.is_alive()
            self.save_button.config(state=tk.NORMAL if can_save else tk.DISABLED)
            can_use_inventory = self.game.player and self.game.player.is_alive()
            if hasattr(self, 'use_item_button'):
                self.use_item_button.config(state=tk.NORMAL if can_use_inventory else tk.DISABLED)
