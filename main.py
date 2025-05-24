# main.py
import tkinter as tk
from auth import AuthService
from game_logic import Game
from gui import RPGInterface
from utils import log_event, COLOR_CYAN, DEBUG_MODE

def main():
    log_event("Uruchamianie aplikacji RPG...", color=COLOR_CYAN, timestamp=True)
    root = tk.Tk()

    auth_service = AuthService()
    
    app_gui_instance = None

    def gui_log_callback(message):
        if app_gui_instance: app_gui_instance.log_message(message)
        log_event(f"GUI_MSG: {message}", level="DEBUG", timestamp=False)


    def gui_status_update_callback(player_status, enemy_status, inventory_listing):
        if app_gui_instance: app_gui_instance.update_status_labels(player_status, enemy_status, inventory_listing)
            
    def gui_combat_buttons_callback(is_active):
        if app_gui_instance: app_gui_instance.update_combat_buttons_visibility(is_active)

    game_service = Game(
        gui_callback_log=gui_log_callback,
        gui_callback_update_stats=gui_status_update_callback,
        gui_callback_combat_buttons=gui_combat_buttons_callback
    )

    app_gui_instance = RPGInterface(root, auth_service, game_service)

    log_event("Aplikacja RPG zainicjalizowana i uruchomiona.", color=COLOR_CYAN)
    root.mainloop()
    log_event("Aplikacja RPG zakończyła działanie.", color=COLOR_CYAN, timestamp=True)


if __name__ == "__main__":
    main()