import random
import json
import os
from utils import calculate_level_xp_threshold, log_event, create_directory_if_not_exists, get_weighted_random_choice, roll_dice_expression, format_currency, safe_nested_get, get_percentage_chance, COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_CYAN
from characters import Player, Enemy
from items import ALL_DEFAULT_ITEMS, Potion, Weapon, Armor, Item
SAVE_GAME_DIR = 'savegames'

class Game:

    def __init__(self, gui_callback_log, gui_callback_update_stats, gui_callback_combat_buttons):
        if not create_directory_if_not_exists(SAVE_GAME_DIR):
            log_event(f'Nie udało się utworzyć katalogu zapisu: {SAVE_GAME_DIR}. Zapis może nie działać.', level='ERROR', color=COLOR_RED)
        self.player = None
        self.current_enemy = None
        self.gui_log_message = gui_callback_log
        self.gui_update_stats = gui_callback_update_stats
        self.gui_update_combat_buttons = gui_callback_combat_buttons
        self.is_in_combat = False
        self.available_enemies_definitions = {'goblin_scout': {'name': 'Goblin Zwiadowca', 'hp': 30, 'attack': 3, 'defense': 2, 'xp': 25, 'gold': 10, 'attack_dice': '1d4+1', 'loot_table': [('small_health_potion', 30), ('rusty_dagger', 15)]}, 'orc_grunt': {'name': 'Orkowy Tępak', 'hp': 60, 'attack': 5, 'defense': 4, 'xp': 50, 'gold': 20, 'attack_dice': '1d8+2', 'loot_table': [('iron_sword', 10), ('medium_health_potion', 20), ('wolf_pelt', 40)]}, 'dark_wolf': {'name': 'Mroczny Wilk', 'hp': 45, 'attack': 4, 'defense': 3, 'xp': 35, 'gold': 15, 'attack_dice': '2d4', 'loot_table': [('wolf_pelt', 60), ('chipped_gemstone', 10)]}, 'forest_spider': {'name': 'Leśny Pająk', 'hp': 25, 'attack': 3, 'defense': 1, 'xp': 20, 'gold': 5, 'attack_dice': '1d6', 'loot_table': [('spider_silk', 50), ('antidote_weak', 10)]}}
        self.enemy_spawn_weights = {'goblin_scout': 40, 'orc_grunt': 20, 'dark_wolf': 30, 'forest_spider': 35}
        self.current_location_description = 'Stoisz na rozstaju dróg. Co robisz?'
        log_event('GameService zainicjalizowany.', level='DEBUG')

    def _get_save_path(self, username):
        return os.path.join(SAVE_GAME_DIR, f'{username}_save.json')

    def _log_to_gui(self, message):
        if self.gui_log_message:
            self.gui_log_message(message)

    def create_new_player(self, player_name, player_class):
        self.player = Player(player_name, player_class)
        self._log_to_gui(f'Witaj, {self.player.name}, {self.player.chosen_class}!')
        log_event(f'Utworzono nowego gracza: {player_name}, klasa: {player_class}', color=COLOR_GREEN)
        if player_class == 'Wojownik':
            self.player.add_item(ALL_DEFAULT_ITEMS['small_health_potion'])
        elif player_class == 'Mag':
            self.player.add_item(ALL_DEFAULT_ITEMS['medium_health_potion'])
        self.update_gui()
        return True

    def save_game(self, username):
        if not self.player:
            self._log_to_gui('Nie ma aktywnej gry do zapisania.')
            log_event('Próba zapisu gry bez aktywnego gracza.', level='WARNING')
            return False
        save_path = self._get_save_path(username)
        try:
            player_data = self.player.to_dict()
            game_state = {'player': player_data, 'current_location_description': self.current_location_description, 'version': '1.1'}
            with open(save_path, 'w') as f:
                json.dump(game_state, f, indent=4)
            self._log_to_gui(f'Gra zapisana dla {username}.')
            log_event(f'Gra zapisana do pliku: {save_path}', color=COLOR_GREEN)
            return True
        except Exception as e:
            self._log_to_gui(f'Błąd podczas zapisywania gry: {e}')
            log_event(f"Krytyczny błąd podczas zapisywania gry dla '{username}': {e}", level='ERROR', color=COLOR_RED)
            return False

    def load_game(self, username):
        save_path = self._get_save_path(username)
        if not os.path.exists(save_path):
            self._log_to_gui(f'Nie znaleziono zapisu dla {username}.')
            log_event(f"Nie znaleziono pliku zapisu dla '{username}': {save_path}", level='INFO')
            return False
        try:
            with open(save_path, 'r') as f:
                game_state = json.load(f)
            self.player = Player.from_dict(safe_nested_get(game_state, 'player', {}), ALL_DEFAULT_ITEMS)
            self.current_location_description = safe_nested_get(game_state, 'current_location_description', 'Nieznane miejsce.')
            self._log_to_gui(f'Gra wczytana dla {self.player.name}.')
            log_event(f"Gra wczytana z pliku: {save_path} dla gracza '{self.player.name}'", color=COLOR_GREEN)
            self.update_gui()
            self.is_in_combat = False
            self.current_enemy = None
            self.gui_update_combat_buttons(False)
            return True
        except Exception as e:
            self._log_to_gui(f'Błąd podczas wczytywania gry: {e}')
            log_event(f"Krytyczny błąd podczas wczytywania gry dla '{username}': {e}", level='ERROR', color=COLOR_RED)
            return False

    def explore(self):
        if self.is_in_combat:
            self._log_to_gui('Jesteś w trakcie walki!')
            return
        if not self.player or not self.player.is_alive():
            self._log_to_gui('Nie możesz eksplorować, gdy jesteś pokonany.')
            return
        self._log_to_gui('Rozglądasz się...')
        log_event(f"Gracz '{self.player.name}' eksploruje.", level='INFO')
        event_roll = roll_dice_expression('1d100')
        if event_roll <= 15:
            self.find_item_event()
        elif event_roll <= 75:
            self.start_encounter()
        elif event_roll <= 90:
            self.find_gold_event()
        else:
            self._log_to_gui('Nic ciekawego się nie wydarzyło.')
            log_event('Eksploracja: nic ciekawego.', level='DEBUG')
        self.update_gui()

    def find_item_event(self):
        possible_finds = {item_key: 1 for item_key, item_obj in ALL_DEFAULT_ITEMS.items() if not isinstance(item_obj, (Weapon, Armor)) or item_obj.value < 50}
        possible_finds['small_health_potion'] = 10
        possible_finds['iron_ore'] = 5
        possible_finds['stale_bread'] = 8
        found_item_key = get_weighted_random_choice(possible_finds)
        if found_item_key and found_item_key in ALL_DEFAULT_ITEMS:
            found_item = ALL_DEFAULT_ITEMS[found_item_key]
            self._log_to_gui(f'Znalazłeś {found_item.name}!')
            log_event(f'Gracz znalazł przedmiot: {found_item.name}', level='INFO', color=COLOR_GREEN)
            self.player.add_item(found_item)
        else:
            self._log_to_gui('Coś błysnęło w trawie, ale zniknęło, nim zdążyłeś zareagować.')
            log_event('Nie udało się wylosować przedmiotu podczas eksploracji.', level='DEBUG')

    def find_gold_event(self):
        amount = roll_dice_expression('2d10')
        self.player.gold += amount
        self._log_to_gui(f'Znalazłeś sakiewkę z {format_currency(amount)}!')
        log_event(f'Gracz znalazł {amount} złota.', level='INFO', color=COLOR_GREEN)

    def start_encounter(self):
        if self.is_in_combat:
            return
        if not self.player or not self.player.is_alive():
            return
        chosen_enemy_key = get_weighted_random_choice(self.enemy_spawn_weights)
        if not chosen_enemy_key or chosen_enemy_key not in self.available_enemies_definitions:
            log_event(f"Błąd: Nie udało się wylosować wroga lub definicja '{chosen_enemy_key}' nie istnieje.", level='ERROR', color=COLOR_RED)
            self._log_to_gui('Coś zaszurało w krzakach, ale uciekło.')
            return
        enemy_def = self.available_enemies_definitions[chosen_enemy_key]
        self.current_enemy = Enemy(name=enemy_def['name'], hp=enemy_def['hp'], attack=enemy_def['attack'], defense=enemy_def['defense'], xp_reward=enemy_def['xp'], gold_reward=enemy_def['gold'], loot_table=enemy_def.get('loot_table', []), attack_dice=enemy_def.get('attack_dice', '1d4'))
        self.is_in_combat = True
        self._log_to_gui(f'Spotykasz {self.current_enemy.name}!')
        self._log_to_gui(str(self.current_enemy))
        log_event(f"Rozpoczęto walkę: Gracz '{self.player.name}' vs Wróg '{self.current_enemy.name}'", level='INFO', color=COLOR_YELLOW)
        self.gui_update_combat_buttons(True)
        self.update_gui()

    def player_action_combat(self, action_type, param=None):
        if not self.is_in_combat or not self.player or (not self.current_enemy) or (not self.player.is_alive()):
            log_event('Próba akcji gracza poza walką lub gdy gracz/wróg nie istnieje.', level='WARNING')
            return
        action_message = ''
        if action_type == 'attack':
            _, action_message = self.player.attack_target(self.current_enemy)
        elif action_type == 'block':
            action_message = self.player.block()
        elif action_type == 'use_potion':
            if param:
                success, potion_message = self.player.use_potion(param)
                action_message = potion_message
                if not success:
                    self._log_to_gui(action_message)
                    self.update_gui()
                    return
            else:
                action_message = 'Musisz wybrać miksturę do użycia.'
        else:
            log_event(f'Nieznana akcja gracza w walce: {action_type}', level='ERROR')
            self._log_to_gui('Nieznana akcja.')
            return
        if action_message:
            self._log_to_gui(action_message)
        self.update_gui()
        if not self.current_enemy.is_alive():
            self.end_combat(victory=True)
        elif self.player.is_alive():
            self.enemy_turn()

    def enemy_turn(self):
        if not self.is_in_combat or not self.current_enemy or (not self.current_enemy.is_alive()) or (not self.player.is_alive()):
            return
        action_message = ''
        if self.current_enemy.hp < self.current_enemy.max_hp * 0.3 and get_percentage_chance(30):
            action_message = self.current_enemy.block()
            log_event(f"Wróg '{self.current_enemy.name}' blokuje.", level='DEBUG')
        else:
            _, action_message = self.current_enemy.attack_target(self.player)
            log_event(f"Wróg '{self.current_enemy.name}' atakuje gracza '{self.player.name}'.", level='DEBUG')
        if action_message:
            self._log_to_gui(action_message)
        self.update_gui()
        if not self.player.is_alive():
            self.end_combat(victory=False)

    def flee_combat(self):
        if not self.is_in_combat:
            return
        if get_percentage_chance(50):
            self._log_to_gui('Udało ci się uciec!')
            log_event(f"Gracz '{self.player.name}' uciekł z walki.", level='INFO', color=COLOR_YELLOW)
            self.is_in_combat = False
            self.current_enemy = None
            self.gui_update_combat_buttons(False)
        else:
            self._log_to_gui('Nie udało się uciec! Wróg korzysta z okazji.')
            log_event(f"Graczowi '{self.player.name}' nie udało się uciec.", level='INFO')
            self.enemy_turn()
        self.update_gui()

    def end_combat(self, victory):
        self.is_in_combat = False
        enemy_name = self.current_enemy.name if self.current_enemy else 'Nieznany Wróg'
        if victory and self.player:
            self._log_to_gui(f'Pokonałeś {enemy_name}!')
            xp_message = self.player.add_xp(self.current_enemy.xp_reward)
            self._log_to_gui(xp_message)
            gold_reward = self.current_enemy.gold_reward
            self.player.gold += gold_reward
            self._log_to_gui(f'Zdobywasz {format_currency(gold_reward)}.')
            log_event(f"Gracz '{self.player.name}' pokonał '{enemy_name}'. Zdobyto {self.current_enemy.xp_reward} XP i {gold_reward} złota.", color=COLOR_GREEN)
            dropped_loot = self.current_enemy.drop_loot()
            if dropped_loot:
                self._log_to_gui('Znaleziono łup:')
                for item in dropped_loot:
                    self._log_to_gui(f'- {item.name}')
                    self.player.add_item(item)
        elif not victory and self.player:
            self._log_to_gui(f'{self.player.name} został pokonany przez {enemy_name}. Koniec gry.')
            log_event(f"Gracz '{self.player.name}' został pokonany. GAME OVER.", level='CRITICAL', color=COLOR_RED)
            self.player = None
        self.current_enemy = None
        self.gui_update_combat_buttons(False)
        self.update_gui()

    def get_player_status(self):
        if not self.player:
            return 'Brak gracza.'
        xp_to_next_level = calculate_level_xp_threshold(self.player.level, base_xp=100, factor=1.2, exponent=1.5)
        status = f'Gracz: {self.player.name} ({self.player.chosen_class}) Poziom: {self.player.level}\n'
        status += f'HP: {self.player.hp}/{self.player.max_hp} Złoto: {format_currency(self.player.gold)} XP: {self.player.xp}/{xp_to_next_level}\n'
        status += f'Atak (bazowy): {self.player.attack_power} Obrona (bazowa): {self.player.defense_power}\n'
        if self.player.equipped_weapon:
            weapon_dmg_info = self.player.equipped_weapon.damage_dice if self.player.equipped_weapon.damage_dice else self.player.equipped_weapon.damage
            status += f'Broń: {self.player.equipped_weapon.name} (Obrażenia: {weapon_dmg_info})\n'
        if self.player.equipped_armor:
            status += f'Zbroja: {self.player.equipped_armor.name} (+{self.player.equipped_armor.defense} Obr.)\n'
        return status

    def get_enemy_status(self):
        if self.is_in_combat and self.current_enemy:
            return f'Wróg: {str(self.current_enemy)}'
        return ''

    def get_inventory_listing(self):
        if not self.player or not self.player.inventory:
            return 'Ekwipunek jest pusty.'
        listing = 'Ekwipunek:\n'
        for i, item in enumerate(self.player.inventory):
            listing += f'{i + 1}. {str(item)}\n'
        return listing

    def use_inventory_item(self, item_index_str):
        if not self.player or not self.player.is_alive():
            self._log_to_gui('Nie możesz teraz używać przedmiotów.')
            return
        try:
            item_index = int(item_index_str) - 1
            if 0 <= item_index < len(self.player.inventory):
                item_to_use = self.player.inventory[item_index]
                log_message_for_gui = ''
                if isinstance(item_to_use, Potion):
                    success, message = item_to_use.use(self.player)
                    log_message_for_gui = message
                    if success:
                        self.player.inventory.pop(item_index)
                        log_event(f'Gracz użył {item_to_use.name} poza walką. {message}', level='INFO')
                    else:
                        log_event(f'Nie udało się użyć {item_to_use.name} poza walką. {message}', level='WARNING')
                elif isinstance(item_to_use, (Weapon, Armor)):
                    log_message_for_gui = self.player.equip_item(item_to_use.name)
                else:
                    log_message_for_gui = f'{item_to_use.name} nie jest miksturą, bronią ani zbroją. Nie można go tak użyć.'
                self._log_to_gui(log_message_for_gui)
                self.update_gui()
            else:
                self._log_to_gui('Nieprawidłowy numer przedmiotu.')
        except ValueError:
            self._log_to_gui('Podaj numer przedmiotu.')
        except IndexError:
            self._log_to_gui('Przedmiot o podanym numerze nie istnieje w ekwipunku.')

    def update_gui(self):
        if self.player and self.player.is_alive():
            self.gui_update_stats(self.get_player_status(), self.get_enemy_status(), self.get_inventory_listing())
        elif self.player and (not self.player.is_alive()):
            self.gui_update_stats('GAME OVER', '', 'Twój ekwipunek przepadł w mroku...')
        else:
            self.gui_update_stats('Brak aktywnej gry.', '', '')
