import random
import re
import math
import textwrap
from collections import defaultdict
import datetime
DEBUG_MODE = True
COLOR_RED = '\x1b[91m'
COLOR_GREEN = '\x1b[92m'
COLOR_YELLOW = '\x1b[93m'
COLOR_BLUE = '\x1b[94m'
COLOR_MAGENTA = '\x1b[95m'
COLOR_CYAN = '\x1b[96m'
COLOR_RESET = '\x1b[0m'

def log_event(message, level='INFO', color=None, timestamp=True):
    if level.upper() == 'DEBUG' and (not DEBUG_MODE):
        return
    time_str = f'[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] ' if timestamp else ''
    log_prefix = f'[{level.upper()}]'
    full_message = f'{time_str}{log_prefix} {message}'
    if color:
        full_message = f'{color}{full_message}{COLOR_RESET}'
    print(full_message)

def generate_random_syllabic_name(min_syl=2, max_syl=4, title_chance=0.1):
    vowels = 'aeiouy'
    consonants = 'bcdfghjklmnprstvwz'
    titles = ['Sir', 'Lady', 'Lord', 'Dame', 'Elder', 'Captain']
    name = ''
    num_syllables = random.randint(min_syl, max_syl)
    for i in range(num_syllables):
        syl = ''
        if random.choice([True, False]):
            syl += random.choice(consonants)
            syl += random.choice(vowels)
            if random.random() < 0.2:
                syl += random.choice(vowels)
        else:
            syl += random.choice(vowels)
            syl += random.choice(consonants)
        if i == 0:
            name += syl.capitalize()
        else:
            name += syl
    if random.random() < title_chance:
        name = f'{random.choice(titles)} {name}'
    return name

def truncate_text(text, max_length=100, suffix='...'):
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length - len(suffix)] + suffix

def format_currency(amount, currency_symbol='zł'):
    return f'{amount:.0f} {currency_symbol}'

def text_to_list_of_words(text, lower=False):
    text = re.sub('[^\\w\\s]', '', text)
    if lower:
        text = text.lower()
    return text.split()

def roll_dice_expression(expression):
    original_expression = expression
    expression = expression.lower().replace(' ', '')
    match = re.match('(\\d*)d(\\d+)([+-]\\d+)?', expression)
    if not match:
        raise ValueError(f'Nieprawidłowy format rzutu kostką: {original_expression}')
    num_dice_str, die_type_str, modifier_str = match.groups()
    num_dice = int(num_dice_str) if num_dice_str else 1
    die_type = int(die_type_str)
    modifier = int(modifier_str) if modifier_str else 0
    if num_dice <= 0 or die_type <= 0:
        raise ValueError('Liczba kości i typ kości muszą być dodatnie.')
    total_roll = sum((random.randint(1, die_type) for _ in range(num_dice)))
    return total_roll + modifier

def get_percentage_chance(percentage):
    if not 0 <= percentage <= 100:
        raise ValueError('Procent musi być z zakresu 0-100.')
    return random.randint(0, 99) < percentage

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def calculate_level_xp_threshold(level, base_xp=100, factor=1.5, exponent=2):
    if level <= 0:
        return 0
    return int(base_xp * level ** exponent * factor)

def get_weighted_random_choice(choices_dict):
    if not choices_dict:
        return None
    total_weight = sum(choices_dict.values())
    if total_weight <= 0:
        return random.choice(list(choices_dict.keys()))
    rand_val = random.uniform(0, total_weight)
    cumulative_weight = 0
    for item, weight in choices_dict.items():
        cumulative_weight += weight
        if rand_val <= cumulative_weight:
            return item
    return None

def safe_nested_get(dictionary, keys, default=None):
    if isinstance(keys, str):
        keys = keys.split('.')
    current_level = dictionary
    for key in keys:
        if isinstance(current_level, dict) and key in current_level:
            current_level = current_level[key]
        else:
            return default
    return current_level

def group_by_key(list_of_dicts, key_to_group_by):
    grouped = defaultdict(list)
    for item_dict in list_of_dicts:
        if key_to_group_by in item_dict:
            grouped[item_dict[key_to_group_by]].append(item_dict)
    return dict(grouped)

def create_directory_if_not_exists(dir_path):
    import os
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            log_event(f'Utworzono katalog: {dir_path}', level='DEBUG')
            return True
        except OSError as e:
            log_event(f'Błąd podczas tworzenia katalogu {dir_path}: {e}', level='ERROR', color=COLOR_RED)
            return False
    return True
if __name__ == '__main__':
    log_event('Rozpoczęto testowanie modułu utils.py', color=COLOR_CYAN)
    print('\n--- Testy Tekstowe ---')
    for _ in range(3):
        print(f'Losowe imię: {generate_random_syllabic_name()}')
    print(f'Obcięty tekst: {truncate_text('To jest bardzo długi tekst, który na pewno zostanie obcięty.', 20)}')
    print(f'Sformatowana waluta: {format_currency(1234.56)}')
    print(f'Tekst na słowa: {text_to_list_of_words('Witaj, świecie! Jak się masz?', lower=True)}')
    print('\n--- Testy Matematyczne i Losowe ---')
    print(f'Rzut 2d6+5: {roll_dice_expression('2d6+5')}')
    print(f'Rzut d100: {roll_dice_expression('d100')}')
    print(f'Szansa 50%: {get_percentage_chance(50)}')
    print(f'Clamp(15, 0, 10): {clamp(15, 0, 10)}')
    print(f'XP dla poziomu 10: {calculate_level_xp_threshold(10, factor=1.2, exponent=2.1)}')
    print('\n--- Testy Struktur Danych ---')
    loot_table = {'Złoto': 60, 'Mikstura': 30, 'Miecz': 10}
    print(f'Ważony wybór z {loot_table}: {get_weighted_random_choice(loot_table)}')
    test_dict = {'user': {'profile': {'name': 'Tester', 'age': 99}, 'settings': {'theme': 'dark'}}}
    print(f"Safe get 'user.profile.name': {safe_nested_get(test_dict, 'user.profile.name')}")
    print(f"Safe get 'user.settings.font' (default): {safe_nested_get(test_dict, 'user.settings.font', 'Arial')}")
    data_to_group = [{'category': 'A', 'value': 1}, {'category': 'B', 'value': 2}, {'category': 'A', 'value': 3}, {'category': 'C', 'value': 4}]
    print(f"Grupowanie po 'category': {group_by_key(data_to_group, 'category')}")
    print('\n--- Testy Systemowe/Plikowe ---')
    test_dir = 'temp_test_dir_utils'
    if create_directory_if_not_exists(test_dir):
        log_event(f'Katalog {test_dir} istnieje lub został utworzony.', color=COLOR_GREEN)
    log_event('Zakończono testowanie modułu utils.py', color=COLOR_CYAN)
