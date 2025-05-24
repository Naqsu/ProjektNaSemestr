from utils import log_event, format_currency, clamp, COLOR_GREEN

class Item:

    def __init__(self, name, description, value):
        self.name = name
        self.description = description
        self.value = value

    def __str__(self):
        return f'{self.name}: {self.description} (Wartość: {format_currency(self.value)})'

    def use(self, target):
        log_event(f"Próba użycia przedmiotu '{self.name}' na '{(target.name if hasattr(target, 'name') else target)}', który nie ma zdefiniowanej akcji 'use'.", level='WARNING')
        return False

class Weapon(Item):

    def __init__(self, name, description, value, damage, damage_dice=None):
        super().__init__(name, description, value)
        self.damage = damage
        self.damage_dice = damage_dice

    def __str__(self):
        dice_info = f' ({self.damage_dice})' if self.damage_dice else ''
        return f'{super().__str__()} (Bazowe obrażenia: {self.damage}{dice_info})'

class Armor(Item):

    def __init__(self, name, description, value, defense):
        super().__init__(name, description, value)
        self.defense = defense

    def __str__(self):
        return f'{super().__str__()} (Obrona: {self.defense})'

class Potion(Item):

    def __init__(self, name, description, value, heal_amount, effect=None, duration=0):
        super().__init__(name, description, value)
        self.heal_amount = heal_amount
        self.effect = effect
        self.duration = duration

    def __str__(self):
        details = []
        if self.heal_amount > 0:
            details.append(f'Leczenie: {self.heal_amount} HP')
        if self.effect:
            if isinstance(self.effect, dict):
                details.append(f'Efekt: +{self.effect['amount']} do {self.effect['stat']}' + (f' na {self.duration} tur' if self.duration > 0 else ''))
            else:
                details.append(f'Efekt: {self.effect.replace('_', ' ').capitalize()}')
        return f'{super().__str__()} ({(', '.join(details) if details else 'Brak specjalnych efektów')})'

    def use(self, target):
        used_successfully = False
        log_message_for_gui = []
        if self.heal_amount > 0 and hasattr(target, 'hp') and hasattr(target, 'max_hp'):
            hp_before = target.hp
            target.hp = clamp(target.hp + self.heal_amount, 0, target.max_hp)
            healed_amount = target.hp - hp_before
            if healed_amount > 0:
                msg = f'{target.name} używa {self.name} i leczy {healed_amount} HP (do {target.hp}/{target.max_hp}).'
                log_event(msg, level='INFO', color=COLOR_GREEN)
                log_message_for_gui.append(msg)
                used_successfully = True
            elif hp_before == target.max_hp:
                msg = f'{target.name} próbował użyć {self.name}, ale ma już pełne HP.'
                log_event(msg, level='INFO')
                log_message_for_gui.append(msg)
                used_successfully = True
            else:
                msg = f'{target.name} próbował użyć {self.name}, ale nie przyniosło to efektu leczniczego.'
                log_event(msg, level='WARNING')
                log_message_for_gui.append(msg)
        if self.effect:
            effect_msg = f'{target.name} odczuwa dodatkowy efekt mikstury {self.name} ({self.effect}).'
            log_event(effect_msg, level='INFO')
            log_message_for_gui.append(effect_msg)
            used_successfully = True
        if not used_successfully:
            no_effect_msg = f'{self.name} nie może być użyty na {target.name} lub nie ma zdefiniowanego efektu w tej sytuacji.'
            log_event(no_effect_msg, level='WARNING')
            return (False, no_effect_msg)
        return (True, ' '.join(log_message_for_gui))

DEFAULT_WEAPONS = {
    "splintered_club": Weapon("Drzazgowa Pałka", "Kawałek drewna, ledwo trzymający się kupy.", 1, 1, "1d2"),
    "kitchen_knife": Weapon("Nóż Kuchenny", "Zabrany w pośpiechu, lepszy niż nic.", 2, 1, "1d3"),
    "rusty_dagger": Weapon("Zardzewiały Sztylet", "Mały i szybki, ale niezbyt mocny.", 3, 2, "1d4"),
    "old_sword": Weapon("Stary Miecz", "Podstawowy miecz dla początkującego wojownika.", 0, 3, "1d6"),
    "hunting_spear_tip": Weapon("Grot Włóczni Myśliwskiej", "Sam grot, bez drzewca. Niewygodny.", 4, 2, "1d4"),
    "apprentice_staff_branch": Weapon("Gałąź Kostura Ucznia", "Złamany kostur, wciąż trochę magii.", 0, 2, "1d4+2"),
    "sling_with_pebbles": Weapon("Proca z Kamieniami", "Dziecięca zabawka, ale kamień może zaboleć.", 2, 1, "1d3"),
    "iron_dagger": Weapon("Żelazny Sztylet", "Solidny sztylet, dobry do szybkich cięć.", 15, 3, "1d4+1"),
    "iron_sword": Weapon("Żelazny Miecz", "Solidny miecz, dobrze wyważony.", 25, 4, "1d8"),
    "steel_axe": Weapon("Stalowy Topór", "Ciężki topór, zdolny przebić pancerz.", 30, 5, "1d10"),
    "mages_wand": Weapon("Różdżka Maga", "Różdżka skupiająca energię magiczną.", 35, 3, "1d6+3"),
    "oak_staff": Weapon("Dębowy Kostur", "Solidny kostur, wzmacniający proste zaklęcia.", 28, 4, "1d8+1"),
    "short_bow": Weapon("Krótki Łuk", "Zgrabny łuk dla zwiadowcy.", 20, 3, "1d6+1"),
    "spiked_mace": Weapon("Kolczasta Maczuga", "Drewniana maczuga z żelaznymi kolcami.", 22, 4, "2d4"),
    "war_hammer_light": Weapon("Lekki Młot Bojowy", "Mniejsza wersja młota bojowego.", 26, 4, "1d8+1"),
    "knights_arming_sword": Weapon("Miecz Rycerski Krótki", "Standardowa broń rycerza.", 60, 6, "1d10+2"),
    "elven_shortsword": Weapon("Elficki Krótki Miecz", "Lekki i ostry, dzieło elfów.", 70, 5, "1d8+3"),
    "dwarven_waraxe": Weapon("Krasnoludzki Topór Bojowy", "Solidny i niezawodny, jak jego twórcy.", 75, 7, "1d12+1"),
    "crystal_focus_staff": Weapon("Kryształowy Kostur Skupiający", "Kostur z magicznym kryształem na szczycie.", 80, 5, "2d6+3"),
    "longbow": Weapon("Długi Łuk", "Potężny łuk wymagający siły i wprawy.", 55, 5, "1d8+2"),
    "morning_star": Weapon("Gwiazda Zaranna", "Kolczasta kula na łańcuchu, przymocowana do rękojeści.", 65, 6, "2d6"),
    "obsidian_dagger": Weapon("Obsydianowy Sztylet", "Niezwykle ostry sztylet z wulkanicznego szkła.", 50, 4, "1d6+2"),
    "masterwork_longsword": Weapon("Mistrzowski Długi Miecz", "Perfekcyjnie wykonany miecz.", 150, 8, "2d8+2"),
    "great_axe_of_cleaving": Weapon("Wielki Topór Rąbiący", "Ogromny topór, zdolny przeciąć wroga na pół.", 160, 10, "2d10"),
    "archmages_battle_staff": Weapon("Bojowy Kostur Arcymaga", "Kostur nasycony potężnymi zaklęciami ofensywnymi.", 180, 7, "3d6+3"),
    "composite_bow": Weapon("Łuk Kompozytowy", "Zaawansowana konstrukcja, zapewniająca dużą siłę strzału.", 140, 7, "1d10+3"),
    "flanged_mace": Weapon("Buława Pierzasta", "Ciężka buława z metalowymi piórami, idealna przeciw pancerzom.", 130, 9, "2d8"),
    "shadowsteel_rapier": Weapon("Rapier z Cieniostali", "Smukły i szybki rapier, wykuty z rzadkiego metalu.", 170, 6, "1d8+4"),
    "blade_of_the_ancients": Weapon("Ostrze Starożytnych", "Legendarny miecz, pulsujący tajemną energią.", 500, 12, "3d8+5"),
    "axe_of_the_berserker_lord": Weapon("Topór Władcy Berserkerów", "Topór, który zdaje się szeptać obietnice rzezi.", 550, 15, "2d12+5"),
    "staff_of_the_cosmos": Weapon("Laska Kosmosu", "Fragment gwiazdy oprawiony w kostur, władający niepojętą mocą.", 600, 10, "4d6+6"),
    "dragons_breath_bow": Weapon("Łuk Smoczego Oddechu", "Łuk, którego strzały płoną ogniem.", 450, 10, "2d10+4"),
    "sunken_trident_of_depths": Weapon("Zatopiony Trójząb Głębin", "Trójząb odnaleziony w morskich otchłaniach.", 480, 11, "3d6+3"),
}

DEFAULT_ARMORS = {
    "rags": Armor("Łachmany", "Resztki ubrań, prawie bez ochrony.", 1, 0),
    "thick_clothes": Armor("Grube Ubranie", "Kilka warstw materiału, trochę lepiej niż nic.", 2, 1),
    "leather_vest_worn": Armor("Znoszona Skórzana Kamizelka", "Podstawowa ochrona, widziała lepsze dni.", 0, 2),
    "cloth_robe_simple": Armor("Prosta Płócienna Szata", "Lekka szata, oferująca minimalną ochronę.", 0, 1),
    "wooden_buckler": Armor("Drewniana Puklerz", "Mała tarcza z drewna.", 3, 1),
    "studded_leather_jerkin": Armor("Ćwiekowany Skórzany Kaftan", "Wzmocniona skórzana zbroja.", 20, 4),
    "chainmail_shirt": Armor("Koszula Kolcza", "Zapewnia dobrą ochronę przed cięciami.", 30, 6),
    "mages_apprentice_robe": Armor("Szata Ucznia Maga", "Szata utkana z prostych magicznych nici.", 25, 3),
    "iron_helmet_basic": Armor("Prosty Żelazny Hełm", "Chroni głowę przed lekkimi ciosami.", 15, 2),
    "reinforced_leather_armor": Armor("Wzmocniona Zbroja Skórzana", "Grubsza skóra z metalowymi płytkami.", 28, 5),
    "full_leather_armor": Armor("Pełna Zbroja Skórzana", "Kompletny strój ze skóry, dobrze dopasowany.", 55, 7),
    "steel_cuirass": Armor("Stalowy Kirys", "Solidna ochrona tułowia.", 70, 9),
    "enchanted_robe": Armor("Zaklęta Szata", "Szata nasycona podstawowymi zaklęciami ochronnymi.", 60, 5),
    "knights_helmet": Armor("Hełm Rycerski", "Solidny hełm zapewniający dobrą ochronę głowy.", 40, 4),
    "scale_mail": Armor("Zbroja Łuskowa", "Pancerz złożony z wielu małych, nachodzących na siebie płytek.", 65, 8),
    "plate_armor_standard": Armor("Standardowa Zbroja Płytowa", "Kompletna zbroja płytowa, doskonała ochrona.", 150, 13),
    "shadow_weave_robe": Armor("Szata z Cienistej Tkaniny", "Lekka szata, która zdaje się pochłaniać światło i ciosy.", 160, 9),
    "dwarven_plate": Armor("Krasnoludzka Zbroja Płytowa", "Niezwykle wytrzymała, choć ciężka.", 170, 15),
    "elven_chainmail_fine": Armor("Elficka Kolczuga Zacna", "Lekka, wytrzymała i piękna.", 140, 11),
    "tower_shield": Armor("Tarcza Wieżowa", "Ogromna tarcza zapewniająca znakomitą osłonę.", 100, 7),
    "armor_of_the_guardian": Armor("Zbroja Strażnika", "Legendarna zbroja, która sama zdaje się chronić nosiciela.", 500, 20),
    "robes_of_the_archlich": Armor("Szaty Arcylisza", "Szaty utkane z dusz i koszmarów, zapewniające mroczną ochronę.", 550, 15),
    "dragonscale_full_plate": Armor("Pełna Zbroja ze Smoczych Łusek", "Pancerz wykuty z łusek prastarego smoka.", 600, 25),
    "aegis_of_the_fallen_god": Armor("Egida Upadłego Boga", "Tarcza nasycona boską esencją, niemal niezniszczalna.", 450, 18),
    "celestial_battle_robe": Armor("Niebiańska Szata Bojowa", "Szata tkana ze światła gwiazd, dla świętych wojowników.", 520, 17),
}

DEFAULT_POTIONS = {
    "weak_healing_draught": Potion("Słaby Wywar Leczniczy", "Mętny płyn, leczy drobne zadrapania.", 5, 15),
    "small_health_potion": Potion("Mała Mikstura Zdrowia", "Przywraca trochę zdrowia.", 10, 30),
    "medium_health_potion": Potion("Średnia Mikstura Zdrowia", "Przywraca znaczną ilość zdrowia.", 25, 60),
    "large_health_potion": Potion("Duża Mikstura Zdrowia", "Całkowicie regeneruje większość ran.", 50, 120),
    "elixir_of_pure_healing": Potion("Eliksir Czystego Leczenia", "Krystalicznie czysty płyn, przywraca pełnię sił.", 100, 250),
    "troll_blood_potion": Potion("Mikstura Krwi Trolla", "Gęsta i cuchnąca, przyspiesza regenerację.", 70, 90, effect="regeneracja_lekka", duration=3),
    "potion_of_minor_strength": Potion("Mikstura Pomniejszej Siły", "Lekko zwiększa siłę fizyczną.", 30, 0, effect={"stat": "attack_power", "amount": 2}, duration=3),
    "potion_of_ogres_strength": Potion("Mikstura Siły Ogra", "Znacząco zwiększa siłę fizyczną.", 70, 0, effect={"stat": "attack_power", "amount": 5}, duration=3),
    "potion_of_cats_grace": Potion("Mikstura Kociej Zwinności", "Zwiększa zręczność i uniki.", 35, 0, effect={"stat": "defense_power", "amount": 2, "type": "dodge"}, duration=3),
    "potion_of_iron_skin": Potion("Mikstura Żelaznej Skóry", "Utwardza skórę, zwiększając odporność na ciosy.", 40, 0, effect={"stat": "defense_power", "amount": 3}, duration=3),
    "potion_of_mages_insight": Potion("Mikstura Wnikliwości Maga", "Wzmacnia koncentrację i moc magiczną.", 45, 0, effect={"stat": "magic_power", "amount": 4}, duration=3),
    "potion_of_heroism": Potion("Mikstura Heroizmu", "Wypełnia odwagą i zwiększa wszystkie zdolności bojowe.", 150, 20, effect="wszystkie_staty_boost", duration=2),
    "antidote_weak": Potion("Słabe Antidotum", "Neutralizuje łagodne trucizny.", 15, 0, effect="cure_mild_poison"),
    "antidote_strong": Potion("Mocne Antidotum", "Neutralizuje silne trucizny.", 40, 0, effect="cure_strong_poison"),
    "potion_of_invisibility_short": Potion("Mikstura Krótkiej Niewidzialności", "Zapewnia niewidzialność na krótki czas.", 60, 0, effect="invisibility", duration=2),
    "potion_of_water_breathing": Potion("Mikstura Wodnego Oddechu", "Pozwala oddychać pod wodą.", 20, 0, effect="water_breathing", duration=5),
    "philter_of_love_fake": Potion("Fałszywy Napój Miłosny", "Pachnie truskawkami. Nie działa.", 5, 0, effect="placebo"),
}

DEFAULT_MISC_ITEMS = {
    "iron_ore": Item("Ruda Żelaza", "Kawałek rudy żelaza, do przetopienia.", 3),
    "goblin_ear": Item("Ucho Goblina", "Popularne trofeum, czasem skupowane.", 1),
    "wolf_pelt": Item("Skóra Wilka", "Dobrej jakości skóra, nadaje się na ubrania.", 5),
    "spider_silk": Item("Pajęczy Jedwab", "Delikatny, ale wytrzymały jedwab.", 8),
    "glowing_mushroom": Item("Świecący Grzyb", "Grzyb emitujący słabe światło, używany w alchemii.", 4),
    "herbs_common": Item("Zwykłe Zioła", "Mieszanka pospolitych ziół leczniczych.", 2),
    "rare_flower_petal": Item("Płatek Rzadkiego Kwiatu", "Składnik potężnych mikstur.", 15),
    "chipped_gemstone": Item("Wyszczerbiony Klejnot", "Mały, uszkodzony klejnot.", 7),
    "flawed_ruby": Item("Skażony Rubin", "Rubin z wewnętrznymi skazami.", 20),
    "sapphire_small": Item("Mały Szafir", "Błyszczący niebieski kamień.", 50),
    "emerald_decent": Item("Przyzwoity Szmaragd", "Piękny zielony klejnot.", 120),
    "diamond_perfect_tiny": Item("Malutki Idealny Diament", "Nawet mały diament jest cenny.", 300),
    "gold_ring_simple": Item("Prosty Złoty Pierścień", "Obrączka ze złota.", 40),
    "silver_necklace_worn": Item("Srebrny Naszyjnik Znoszony", "Kiedyś piękny, teraz trochę zniszczony.", 25),
    "ivory_figurine": Item("Figurka z Kości Słoniowej", "Mała, rzeźbiona figurka.", 75),
    "stale_bread": Item("Czerstwy Chleb", "Twardy, ale jadalny.", 1),
    "dried_meat": Item("Suszone Mięso", "Długo zachowuje świeżość.", 3),
    "apple_red": Item("Czerwone Jabłko", "Soczyste i słodkie.", 2),
    "waterskin": Item("Bukłak z Wodą", "Niezbędny w podróży.", 1),
    "cheap_wine": Item("Tanie Wino", "Kwaśne, ale rozgrzewa.", 4),
    "tattered_scroll": Item("Podarty Zwój", "Nieczytelne pismo na starym pergaminie.", 2),
    "book_local_history": Item("Księga Historii Lokalnej", "Opisuje dzieje najbliższej okolicy.", 10),
    "journal_adventurer": Item("Dziennik Podróżnika", "Zapiski nieznanego poszukiwacza przygód.", 15),
    "map_fragment_unknown": Item("Fragment Nieznanej Mapy", "Część większej mapy, miejsce nie do rozpoznania.", 8),
}

ALL_DEFAULT_ITEMS = {
    **DEFAULT_WEAPONS,
    **DEFAULT_ARMORS,
    **DEFAULT_POTIONS,
    **DEFAULT_MISC_ITEMS
    # te gwiazdki to laczenie slownikow
}