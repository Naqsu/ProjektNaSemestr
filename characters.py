
import random
from items import Item, Weapon, Armor, Potion, ALL_DEFAULT_ITEMS
from utils import (
    log_event, roll_dice_expression, clamp, calculate_level_xp_threshold, 
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW, safe_nested_get, generate_random_syllabic_name
)

class Character:
    def __init__(self, name, hp, attack, defense):
        self.name = name if name else generate_random_syllabic_name(min_syl=2, max_syl=3)
        self.max_hp = hp
        self.hp = hp
        self.attack_power = attack 
        self.defense_power = defense
        self.is_blocking = False

    def take_damage(self, damage):
        actual_damage_taken = 0
        log_message_parts = []

        if self.is_blocking:
            effective_defense = self.get_total_defense() * 2 
            reduced_damage = clamp(damage - effective_defense, 0, damage)
            actual_damage_taken = reduced_damage
            msg = f"{self.name} blokuje atak! Obrona: {effective_defense}. Otrzymuje {actual_damage_taken} obrażeń (z {damage})."
            log_event(msg, level="DEBUG", color=COLOR_YELLOW)
            log_message_parts.append(f"{self.name} blokuje i otrzymuje {actual_damage_taken} obrażeń!")
            self.is_blocking = False
        else:
            effective_defense = self.get_total_defense()
            reduced_damage = clamp(damage - effective_defense, 0, damage)
            actual_damage_taken = reduced_damage
            msg = f"{self.name} otrzymuje {actual_damage_taken} obrażeń (z {damage}, obrona: {effective_defense})."
            log_event(msg, level="DEBUG", color=COLOR_RED)
            log_message_parts.append(f"{self.name} otrzymuje {actual_damage_taken} obrażeń.")
        
        self.hp = clamp(self.hp - actual_damage_taken, 0, self.max_hp)
        
        if self.hp == 0:
            log_event(f"{self.name} został pokonany!", level="INFO", color=COLOR_RED)
            log_message_parts.append(f"{self.name} pada nieprzytomny!")
            
        return actual_damage_taken, " ".join(log_message_parts)


    def is_alive(self):
        return self.hp > 0

    def get_total_attack(self):
        return self.attack_power

    def get_total_defense(self):
        return self.defense_power

    def attack_target(self, target):
        if not self.is_alive():
            return None, f"{self.name} nie może atakować, jest nieprzytomny."

        base_damage = self.get_total_attack()
        weapon_damage_roll = 0
        
        if hasattr(self, 'equipped_weapon') and self.equipped_weapon and self.equipped_weapon.damage_dice:
            try:
                weapon_damage_roll = roll_dice_expression(self.equipped_weapon.damage_dice)
                log_event(f"{self.name} rzuca {self.equipped_weapon.damage_dice} dla broni: {weapon_damage_roll}", level="DEBUG")
            except ValueError as e:
                log_event(f"Błąd w notacji kości dla broni {self.equipped_weapon.name}: {e}", level="ERROR", color=COLOR_RED)
                weapon_damage_roll = self.equipped_weapon.damage
        elif hasattr(self, 'equipped_weapon') and self.equipped_weapon:
             weapon_damage_roll = self.equipped_weapon.damage
        else:
            weapon_damage_roll = roll_dice_expression("1d3")

        potential_damage = base_damage + weapon_damage_roll + random.randint(-1,1)
        potential_damage = max(1, potential_damage)

        log_event(f"{self.name} (Atk:{base_damage}) atakuje {target.name} z potencjalnymi obrażeniami: {potential_damage} (broń: {weapon_damage_roll}).", level="INFO")
        
        actual_damage_inflicted, damage_message = target.take_damage(potential_damage)
        
        attack_log_message = f"{self.name} atakuje {target.name}. {damage_message}"
        return actual_damage_inflicted, attack_log_message

    def block(self):
        log_event(f"{self.name} przygotowuje się do bloku!", level="INFO", color=COLOR_YELLOW)
        self.is_blocking = True
        return f"{self.name} przygotowuje się do bloku!"

    def heal(self, amount):
        hp_before = self.hp
        self.hp = clamp(self.hp + amount, 0, self.max_hp)
        healed_amount = self.hp - hp_before
        msg = f"{self.name} leczy się o {healed_amount} HP (do {self.hp}/{self.max_hp})."
        log_event(msg, level="INFO", color=COLOR_GREEN)
        return healed_amount, msg


    def __str__(self):
        return f"{self.name} (HP: {self.hp}/{self.max_hp}, Baz.Atk: {self.attack_power}, Baz.Def: {self.defense_power})"

class Player(Character):
    def __init__(self, name, chosen_class="Wojownik"):
        if chosen_class == "Wojownik":
            super().__init__(name, hp=100, attack=10, defense=5)
            self.equipped_weapon = ALL_DEFAULT_ITEMS["old_sword"]
            self.equipped_armor = ALL_DEFAULT_ITEMS["leather_vest_worn"]
        elif chosen_class == "Mag":
            super().__init__(name, hp=70, attack=8, defense=3) 
            self.equipped_weapon = ALL_DEFAULT_ITEMS["apprentice_staff_branch"]
            self.equipped_armor = ALL_DEFAULT_ITEMS["cloth_robe_simple"]
        else: 
            super().__init__(name, hp=100, attack=10, defense=5)
            self.equipped_weapon = ALL_DEFAULT_ITEMS["old_sword"]
            self.equipped_armor = ALL_DEFAULT_ITEMS["leather_vest_worn"]

        self.inventory = []
        self.gold = 20
        self.xp = 0
        self.level = 1
        self.chosen_class = chosen_class

    def get_total_attack(self):
        return self.attack_power + (self.equipped_weapon.damage if self.equipped_weapon else 0)


    def get_total_defense(self):
        base_defense = self.defense_power
        armor_bonus = self.equipped_armor.defense if self.equipped_armor else 0
        return base_defense + armor_bonus
    
    def add_item(self, item):
        self.inventory.append(item)
        log_event(f"Przedmiot '{item.name}' dodany do ekwipunku gracza '{self.name}'.", level="DEBUG")
        return f"{item.name} dodany do ekwipunku."

    def remove_item(self, item_name):
        for i, item in enumerate(self.inventory):
            if item.name.lower() == item_name.lower():
                removed_item = self.inventory.pop(i)
                log_event(f"Przedmiot '{removed_item.name}' usunięty z ekwipunku gracza '{self.name}'.", level="DEBUG")
                return removed_item
        return None

    def equip_item(self, item_name):
        item_to_equip = None
        item_index = -1
        for i, item_obj in enumerate(self.inventory):
            if item_obj.name.lower() == item_name.lower():
                item_to_equip = item_obj
                item_index = i
                break
        
        if not item_to_equip:
            return f"Nie masz przedmiotu {item_name} w ekwipunku."

        log_msg = ""
        if isinstance(item_to_equip, Weapon):
            if self.equipped_weapon: 
                self.add_item(self.equipped_weapon) 
                log_msg += f" Zdjęto {self.equipped_weapon.name}."
            self.equipped_weapon = item_to_equip
            self.inventory.pop(item_index)
            log_msg = f"Wyposażono {item_to_equip.name}." + log_msg
            log_event(f"Gracz '{self.name}' wyposażył broń: {item_to_equip.name}.", level="INFO")
        elif isinstance(item_to_equip, Armor):
            if self.equipped_armor:
                self.add_item(self.equipped_armor)
                log_msg += f" Zdjęto {self.equipped_armor.name}."
            self.equipped_armor = item_to_equip
            self.inventory.pop(item_index)
            log_msg = f"Wyposażono {item_to_equip.name}." + log_msg
            log_event(f"Gracz '{self.name}' wyposażył zbroję: {item_to_equip.name}.", level="INFO")
        else:
            log_msg = f"{item_to_equip.name} nie jest bronią ani zbroją."
        
        return log_msg

    def use_potion(self, potion_name):
        potion_to_use = None
        potion_index = -1
        for i, item in enumerate(self.inventory):
            if isinstance(item, Potion) and item.name.lower() == potion_name.lower():
                potion_to_use = item
                potion_index = i
                break
        
        if potion_to_use:
            success, message = potion_to_use.use(self) 
            if success:
                self.inventory.pop(potion_index)
                log_event(f"Gracz '{self.name}' użył mikstury '{potion_name}'. {message}", level="INFO")
                return True, message
            else:
                log_event(f"Nie udało się użyć mikstury '{potion_name}' przez gracza '{self.name}'. {message}", level="WARNING")
                return False, message
        else:
            msg = f"Nie masz mikstury {potion_name}."
            log_event(msg, level="INFO")
            return False, msg


    def add_xp(self, amount):
        self.xp += amount
        log_event(f"Gracz '{self.name}' zdobywa {amount} XP. Total XP: {self.xp}", level="INFO")
        gui_message = [f"Zdobywasz {amount} XP."]
        
        xp_needed_for_next_level = calculate_level_xp_threshold(self.level, base_xp=100, factor=1.2, exponent=1.5)
        
        while self.xp >= xp_needed_for_next_level:
            self.level += 1
            self.xp -= xp_needed_for_next_level
            
            self.max_hp += 10
            self.hp = self.max_hp
            self.attack_power += random.randint(1,2)
            self.defense_power += random.randint(0,1)

            level_up_msg = f"Awans na {self.level} poziom! Statystyki wzrosły. HP do {self.max_hp}, Atk do {self.attack_power}, Def do {self.defense_power}."
            log_event(f"Gracz '{self.name}' awansował na poziom {self.level}!", level="INFO", color=COLOR_GREEN)
            gui_message.append(level_up_msg)
            
            xp_needed_for_next_level = calculate_level_xp_threshold(self.level, base_xp=100, factor=1.2, exponent=1.5)
        
        return " ".join(gui_message)
            
    def to_dict(self):
        inventory_data = []
        for item in self.inventory:
            item_key = None
            for key, default_item in ALL_DEFAULT_ITEMS.items():
                if default_item.name == item.name:
                    item_key = key
                    break
            if item_key:
                inventory_data.append({"item_key": item_key})
            else:
                item_data = {"name": item.name, "type": item.__class__.__name__}
                if isinstance(item, Weapon): item_data.update({"damage": item.damage, "damage_dice": item.damage_dice})
                elif isinstance(item, Armor): item_data["defense"] = item.defense
                elif isinstance(item, Potion): item_data.update({"heal_amount": item.heal_amount, "effect": item.effect, "duration": item.duration})
                item_data["description"] = item.description
                item_data["value"] = item.value
                inventory_data.append(item_data)


        equipped_weapon_key = None
        if self.equipped_weapon:
            for key, item_obj in ALL_DEFAULT_ITEMS.items():
                if item_obj.name == self.equipped_weapon.name and isinstance(item_obj, Weapon):
                    equipped_weapon_key = key
                    break
        
        equipped_armor_key = None
        if self.equipped_armor:
            for key, item_obj in ALL_DEFAULT_ITEMS.items():
                if item_obj.name == self.equipped_armor.name and isinstance(item_obj, Armor):
                    equipped_armor_key = key
                    break

        return {
            "name": self.name,
            "chosen_class": self.chosen_class,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack_power": self.attack_power,
            "defense_power": self.defense_power,
            "gold": self.gold,
            "xp": self.xp,
            "level": self.level,
            "inventory": inventory_data,
            "equipped_weapon_key": equipped_weapon_key,
            "equipped_armor_key": equipped_armor_key,
        }

    @classmethod
    def from_dict(cls, data, all_items_reference):
        player = cls(
            safe_nested_get(data, "name", "Bezimienny"), 
            safe_nested_get(data, "chosen_class", "Wojownik")
        )
        player.hp = safe_nested_get(data, "hp", player.max_hp)
        player.max_hp = safe_nested_get(data, "max_hp", player.max_hp)
        player.attack_power = safe_nested_get(data, "attack_power", player.attack_power)
        player.defense_power = safe_nested_get(data, "defense_power", player.defense_power)
        player.gold = safe_nested_get(data, "gold", player.gold)
        player.xp = safe_nested_get(data, "xp", player.xp)
        player.level = safe_nested_get(data, "level", player.level)

        player.inventory = []
        for item_data_entry in safe_nested_get(data, "inventory", []):
            item_key = safe_nested_get(item_data_entry, "item_key")
            if item_key and item_key in all_items_reference:
                player.add_item(all_items_reference[item_key])
            else:
                log_event(f"Nie można odtworzyć przedmiotu z ekwipunku: {item_data_entry}", level="WARNING")


        equipped_weapon_key = safe_nested_get(data, "equipped_weapon_key")
        if equipped_weapon_key and equipped_weapon_key in all_items_reference:
            item_obj = all_items_reference[equipped_weapon_key]
            if isinstance(item_obj, Weapon):
                 player.equipped_weapon = item_obj
            else:
                log_event(f"Próba wyposażenia '{equipped_weapon_key}' jako broń, ale to nie broń.", level="ERROR")
        elif not player.equipped_weapon:
             if player.chosen_class == "Wojownik": player.equipped_weapon = all_items_reference.get("old_sword")
             elif player.chosen_class == "Mag": player.equipped_weapon = all_items_reference.get("apprentice_staff_branch")
            
        equipped_armor_key = safe_nested_get(data, "equipped_armor_key")
        if equipped_armor_key and equipped_armor_key in all_items_reference:
            item_obj = all_items_reference[equipped_armor_key]
            if isinstance(item_obj, Armor):
                 player.equipped_armor = item_obj
            else:
                log_event(f"Próba wyposażenia '{equipped_armor_key}' jako zbroja, ale to nie zbroja.", level="ERROR")
        elif not player.equipped_armor:
            if player.chosen_class == "Wojownik": player.equipped_armor = all_items_reference.get("leather_vest_worn")
            elif player.chosen_class == "Mag": player.equipped_armor = all_items_reference.get("cloth_robe_simple")
        
        return player


class Enemy(Character):
    def __init__(self, name, hp, attack, defense, xp_reward, gold_reward, loot_table=None, attack_dice="1d4"):
        super().__init__(name, hp, attack, defense)
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.loot_table = loot_table if loot_table else []
        self.attack_dice = attack_dice

    def attack_target(self, target):
        if not self.is_alive():
            return None, f"{self.name} nie może atakować, jest pokonany."

        base_damage = self.get_total_attack()
        try:
            weapon_damage_roll = roll_dice_expression(self.attack_dice)
        except ValueError as e:
            log_event(f"Błąd w notacji kości dla ataku wroga {self.name}: {e}", level="ERROR", color=COLOR_RED)
            weapon_damage_roll = random.randint(1, 4)

        potential_damage = base_damage + weapon_damage_roll
        potential_damage = max(1, potential_damage)

        log_event(f"Wróg {self.name} (Atk:{base_damage}) atakuje {target.name} z potencjalnymi obrażeniami: {potential_damage} (kość: {self.attack_dice} -> {weapon_damage_roll}).", level="INFO")
        
        actual_damage_inflicted, damage_message = target.take_damage(potential_damage)
        
        attack_log_message = f"{self.name} atakuje {target.name}. {damage_message}"
        return actual_damage_inflicted, attack_log_message


    def drop_loot(self):
        dropped_items = []
        if self.loot_table:
            for loot_entry in self.loot_table:
                item_ref, chance = loot_entry 
                if random.randint(1, 100) <= chance:
                    if isinstance(item_ref, str) and item_ref in ALL_DEFAULT_ITEMS:
                        dropped_items.append(ALL_DEFAULT_ITEMS[item_ref])
                    elif isinstance(item_ref, Item):
                        dropped_items.append(item_ref)
                    else:
                        log_event(f"Nieznany format łupu dla {self.name}: {item_ref}", level="WARNING")
            
        if dropped_items:
            log_event(f"{self.name} upuszcza łup: {[item.name for item in dropped_items]}", level="INFO", color=COLOR_GREEN)
        return dropped_items