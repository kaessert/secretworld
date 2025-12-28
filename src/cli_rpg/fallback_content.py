"""FallbackContentProvider for deterministic content when AI is unavailable.

Provides expanded template-based fallback content for rooms, NPCs, items, and quests.
Uses seeded RNG for reproducibility. Templates are category-specific.

This module centralizes all fallback content generation that ContentLayer needs
when AIService is unavailable or fails.
"""

import random
from dataclasses import dataclass, field
from cli_rpg.procedural_interiors import RoomType


# =============================================================================
# Room Name Templates (6+ per RoomType)
# =============================================================================

ROOM_NAMES: dict[RoomType, list[str]] = {
    RoomType.ENTRY: [
        "Entrance Chamber",
        "Entry Hall",
        "Threshold",
        "Vestibule",
        "Gateway",
        "Antechamber",
    ],
    RoomType.CORRIDOR: [
        "Dark Corridor",
        "Narrow Passage",
        "Stone Hallway",
        "Winding Path",
        "Dusty Tunnel",
        "Long Gallery",
    ],
    RoomType.CHAMBER: [
        "Ancient Chamber",
        "Dusty Room",
        "Stone Chamber",
        "Silent Hall",
        "Forgotten Room",
        "Vaulted Chamber",
    ],
    RoomType.BOSS_ROOM: [
        "Boss Lair",
        "Inner Sanctum",
        "Throne Room",
        "Final Chamber",
        "Heart of Darkness",
        "Lord's Chamber",
    ],
    RoomType.TREASURE: [
        "Treasure Vault",
        "Hidden Cache",
        "Gilded Chamber",
        "Hoard Room",
        "Secret Treasury",
        "Jewel Room",
    ],
    RoomType.PUZZLE: [
        "Puzzle Room",
        "Trial Chamber",
        "Enigma Hall",
        "Test of Wits",
        "Riddle Chamber",
        "Challenge Room",
    ],
}


# =============================================================================
# Room Description Templates (per RoomType x Category)
# =============================================================================

ROOM_DESCRIPTIONS: dict[RoomType, dict[str, list[str]]] = {
    RoomType.ENTRY: {
        "dungeon": [
            "The entrance to the dungeon. Dark passages stretch ahead.",
            "A foreboding entrance descends into darkness below.",
            "Cold air rushes from the dungeon depths.",
        ],
        "cave": [
            "The cave mouth opens into darkness. Strange echoes surround you.",
            "Stalactites hang from the cave entrance like teeth.",
            "Damp stone walls mark the beginning of the cavern.",
        ],
        "ruins": [
            "Crumbling stones mark the entrance to these ancient ruins.",
            "Vines cover the broken archway leading into the ruins.",
            "Weathered carvings frame the entrance to this forgotten place.",
        ],
        "temple": [
            "Sacred symbols adorn the threshold of this holy place.",
            "Incense still lingers at the temple entrance.",
            "Faded prayers are carved into the entrance pillars.",
        ],
        "tomb": [
            "A heavy stone door guards the entrance to the tomb.",
            "Ancient warnings are carved above the tomb entrance.",
            "The air grows cold as you enter this place of the dead.",
        ],
        "mine": [
            "Old support beams frame the mine entrance.",
            "Abandoned mining carts rest near the shaft entrance.",
            "The smell of dust and ore fills the mine entrance.",
        ],
        "crypt": [
            "Stone stairs descend into the crypt below.",
            "Cobwebs cover the iron gate to the crypt.",
            "Faint whispers seem to emanate from the crypt entrance.",
        ],
        "tower": [
            "The tower's base opens to a spiraling staircase.",
            "Light filters down from windows above.",
            "The tower entrance is marked with arcane symbols.",
        ],
        "monastery": [
            "Worn steps lead into the quiet monastery.",
            "A bell tower rises above the monastery entrance.",
            "Peace settles over you at the monastery threshold.",
        ],
        "shrine": [
            "A small doorway leads into the ancient shrine.",
            "Offerings are scattered near the shrine entrance.",
            "Holy symbols mark the entrance to this sacred place.",
        ],
        "town": [
            "You enter the town through its main gate.",
            "Busy streets stretch before you as you enter.",
            "The town square opens up before you.",
        ],
        "village": [
            "A simple path leads into the quiet village.",
            "Thatched roofs come into view as you enter.",
            "Friendly faces greet you at the village entrance.",
        ],
        "city": [
            "Grand gates mark the entrance to this bustling city.",
            "The city walls tower above as you enter.",
            "Crowds surge through the city entrance.",
        ],
        "settlement": [
            "A simple perimeter marks the settlement entrance.",
            "Makeshift structures surround the settlement entrance.",
            "You enter the small settlement through a gap in the fence.",
        ],
        "outpost": [
            "Guards watch from the outpost towers as you approach.",
            "The outpost gate creaks open to admit you.",
            "Fortified walls protect the outpost entrance.",
        ],
        "camp": [
            "Tents spread out before you as you enter the camp.",
            "Campfires dot the camp entrance.",
            "The smell of cooking food wafts from the camp.",
        ],
        "tavern": [
            "Warm light spills from the tavern door.",
            "Laughter and music drift from within.",
            "The smell of ale greets you at the entrance.",
        ],
        "shop": [
            "A small bell rings as you open the shop door.",
            "Wares are displayed in the shop window.",
            "The shopkeeper looks up as you enter.",
        ],
        "inn": [
            "A cozy fire welcomes you at the inn entrance.",
            "The innkeeper waves from behind the counter.",
            "Weary travelers rest in the inn's common room.",
        ],
        "default": [
            "The entrance to this place. Adventure awaits within.",
            "A threshold beckons you forward.",
            "The way ahead opens before you.",
        ],
    },
    RoomType.CORRIDOR: {
        "dungeon": [
            "A narrow passage with damp walls. Shadows dance at the edges of your vision.",
            "The corridor stretches into darkness ahead.",
            "Water drips from the dungeon ceiling above.",
        ],
        "cave": [
            "A rocky tunnel twists through the darkness. Water drips somewhere nearby.",
            "The cave passage narrows and widens unpredictably.",
            "Phosphorescent moss provides faint light here.",
        ],
        "ruins": [
            "A partially collapsed hallway. Rubble crunches underfoot.",
            "Broken columns line this ancient corridor.",
            "Faded murals cover the ruined walls.",
        ],
        "temple": [
            "A processional corridor lined with faded murals.",
            "Candle niches line the temple hallway.",
            "Sacred images watch from the corridor walls.",
        ],
        "tomb": [
            "A dusty passage lined with burial alcoves.",
            "The corridor is flanked by sealed coffins.",
            "Ancient names are carved into the tomb walls.",
        ],
        "mine": [
            "Wooden beams support the mine tunnel.",
            "Old ore cart tracks run along the passage.",
            "The tunnel shows signs of recent excavation.",
        ],
        "crypt": [
            "Stone alcoves hold ancient remains.",
            "The crypt corridor is cold and silent.",
            "Names of the dead are carved into the walls.",
        ],
        "tower": [
            "A spiraling stairway connects the tower floors.",
            "Arrow slits provide glimpses of the world below.",
            "The tower passage winds ever upward.",
        ],
        "monastery": [
            "A quiet cloister connects the monastery halls.",
            "Prayer bells echo through the corridor.",
            "Monks' cells line the monastery passage.",
        ],
        "shrine": [
            "A narrow passage connects the shrine chambers.",
            "Votive offerings line the corridor walls.",
            "The air grows more sacred as you proceed.",
        ],
        "town": [
            "A busy street connects the town districts.",
            "Market stalls line the thoroughfare.",
            "Townspeople bustle through the streets.",
        ],
        "village": [
            "A dirt path winds between village homes.",
            "Chickens scatter as you walk the village lane.",
            "Simple cottages line the village road.",
        ],
        "city": [
            "A grand avenue stretches through the city.",
            "Street vendors call out their wares.",
            "The city street teems with activity.",
        ],
        "settlement": [
            "A muddy path connects the settlement structures.",
            "Makeshift shelters line the way.",
            "The settlement path is rutted with cart tracks.",
        ],
        "outpost": [
            "A covered walkway connects the outpost buildings.",
            "Guards patrol the outpost passages.",
            "The outpost corridor is utilitarian and bare.",
        ],
        "camp": [
            "A path winds between the camp tents.",
            "Campfires light the way through camp.",
            "Soldiers rest along the camp paths.",
        ],
        "tavern": [
            "A narrow hallway leads to the private rooms.",
            "The tavern corridor smells of old ale.",
            "Patrons stumble through the tavern hall.",
        ],
        "shop": [
            "Shelves of goods line the shop aisles.",
            "The shop corridor is crowded with merchandise.",
            "A back passage leads to the storeroom.",
        ],
        "inn": [
            "A creaky hallway leads to the guest rooms.",
            "Worn carpet runs along the inn corridor.",
            "Doors to guest rooms line the passage.",
        ],
        "default": [
            "A connecting passage leading deeper into the structure.",
            "The corridor stretches onward.",
            "The way forward lies through this passage.",
        ],
    },
    RoomType.CHAMBER: {
        "dungeon": [
            "A larger room with crumbling pillars. Something valuable might be hidden here.",
            "The dungeon chamber is cold and damp.",
            "Ancient chains hang from the chamber walls.",
        ],
        "cave": [
            "A cavern opens up around you. Stalactites hang from the ceiling.",
            "Crystal formations glitter in the cave chamber.",
            "An underground pool fills part of the cavern.",
        ],
        "ruins": [
            "An ancient chamber, its original purpose lost to time.",
            "Broken furniture litters the ruined room.",
            "Faded tapestries hang from the crumbling walls.",
        ],
        "temple": [
            "A meditation chamber with worn prayer cushions.",
            "Temple relics are displayed in this sacred room.",
            "Candles illuminate the temple chamber.",
        ],
        "tomb": [
            "A burial chamber with ornate sarcophagi.",
            "Grave goods surround the central tomb.",
            "The tomb chamber is eerily silent.",
        ],
        "mine": [
            "A mined-out chamber with exposed ore veins.",
            "Mining equipment lies abandoned in the chamber.",
            "Support beams crisscross the mine chamber ceiling.",
        ],
        "crypt": [
            "A vault filled with ancient coffins.",
            "The crypt chamber holds the remains of nobility.",
            "Dust motes dance in the dim crypt light.",
        ],
        "tower": [
            "A circular tower room with narrow windows.",
            "Arcane apparatus fills the tower chamber.",
            "Books and scrolls line the tower room walls.",
        ],
        "monastery": [
            "A simple chamber used for contemplation.",
            "Prayer mats cover the monastery floor.",
            "Religious texts are displayed on the chamber walls.",
        ],
        "shrine": [
            "A sacred chamber housing holy relics.",
            "Offerings pile before the shrine altar.",
            "Divine light seems to fill this sacred space.",
        ],
        "town": [
            "A town building serves as a gathering place.",
            "Citizens conduct their business here.",
            "The town hall is a hub of activity.",
        ],
        "village": [
            "A simple village home with rustic furnishings.",
            "The village elder's cottage is cozy and warm.",
            "Handmade goods fill the village dwelling.",
        ],
        "city": [
            "A city building with ornate decorations.",
            "The grand hall impresses with its scale.",
            "Noble furnishings adorn the city chamber.",
        ],
        "settlement": [
            "A makeshift structure serves as shelter.",
            "The settlement building is rough but functional.",
            "Supplies are stored in the settlement warehouse.",
        ],
        "outpost": [
            "A military barracks houses the garrison.",
            "Weapons racks line the outpost armory.",
            "Maps cover the walls of the command room.",
        ],
        "camp": [
            "A large tent serves as a meeting place.",
            "The camp command tent is organized and busy.",
            "Supplies are inventoried in the camp storage.",
        ],
        "tavern": [
            "A private dining room for special guests.",
            "The tavern's back room is quiet and secluded.",
            "A storage room holds barrels of ale.",
        ],
        "shop": [
            "The shopkeeper's private quarters lie beyond.",
            "A workshop for crafting and repairs.",
            "Rare goods are stored in the back room.",
        ],
        "inn": [
            "A guest room offers rest to weary travelers.",
            "The inn's common room is warm and welcoming.",
            "A private suite provides luxury accommodation.",
        ],
        "default": [
            "A spacious room with signs of ancient habitation.",
            "The chamber holds secrets of the past.",
            "Something of interest may be found here.",
        ],
    },
    RoomType.BOSS_ROOM: {
        "dungeon": [
            "A massive chamber where something powerful lurks.",
            "The dungeon lord's throne dominates this chamber.",
            "Dark power emanates from this final chamber.",
        ],
        "cave": [
            "A vast underground dome. The beast's lair awaits.",
            "Bones of previous victims litter the cave floor.",
            "The cave creature's nest fills this chamber.",
        ],
        "ruins": [
            "The heart of the ruins. An ancient guardian protects this place.",
            "The ruin's master awaits in this final chamber.",
            "Ancient magic swirls around the guardian's throne.",
        ],
        "temple": [
            "The inner sanctum. A sacred guardian challenges all who enter.",
            "The temple's divine protector watches from above.",
            "Holy power guards this most sacred space.",
        ],
        "tomb": [
            "The king's burial chamber. His spirit guards it still.",
            "An ancient pharaoh's sarcophagus dominates the room.",
            "The tomb lord's power fills this chamber.",
        ],
        "mine": [
            "The deepest shaft. Something terrible has made its home here.",
            "A massive creature guards the richest ore deposits.",
            "The mine's depths hide a terrible secret.",
        ],
        "crypt": [
            "The master vampire's coffin rests here.",
            "The crypt lord's power chills the very air.",
            "Undead guardians surround their master's resting place.",
        ],
        "tower": [
            "The tower's apex. The wizard awaits.",
            "Arcane energy crackles around the tower master's throne.",
            "The mage's power is strongest at the tower's height.",
        ],
        "monastery": [
            "The abbot's chamber. A corrupted guardian waits.",
            "Dark power has twisted the monastery's heart.",
            "The fallen monk awaits in meditation.",
        ],
        "shrine": [
            "The inner shrine. The god's avatar manifests here.",
            "Divine wrath protects the shrine's holiest chamber.",
            "The shrine guardian tests all who enter.",
        ],
        "default": [
            "A final chamber where danger awaits.",
            "The lair of something powerful and ancient.",
            "Your greatest challenge awaits in this chamber.",
        ],
    },
    RoomType.TREASURE: {
        "dungeon": [
            "A hidden vault filled with the spoils of past adventurers.",
            "Gold coins are scattered across the dungeon floor.",
            "Treasure chests line the vault walls.",
        ],
        "cave": [
            "A glittering grotto where precious things have accumulated.",
            "Crystal formations hide valuable gems within.",
            "A dragon's hoard lies scattered across the cave.",
        ],
        "ruins": [
            "A treasure room protected by ancient wards.",
            "Artifacts of a lost civilization fill this vault.",
            "The ruins' greatest treasures are stored here.",
        ],
        "temple": [
            "An offering chamber filled with sacred relics.",
            "Temple treasures gleam in the candlelight.",
            "Devotees' gifts fill the temple treasury.",
        ],
        "tomb": [
            "Grave goods surround the royal sarcophagus.",
            "The pharaoh's treasures were meant for the afterlife.",
            "Jewels and gold were buried with the dead.",
        ],
        "mine": [
            "A rich vein of precious ore runs through the wall.",
            "Unrefined gems litter the mine floor.",
            "The miners struck a rich deposit here.",
        ],
        "crypt": [
            "Noble treasures were entombed with the dead.",
            "Ancient coins and jewelry fill the burial niches.",
            "The crypt's wealthiest inhabitants rest here.",
        ],
        "tower": [
            "The wizard's private treasury holds magical artifacts.",
            "Enchanted items glow on the tower shelves.",
            "Rare components and treasures fill this room.",
        ],
        "monastery": [
            "The monastery's reliquary holds sacred treasures.",
            "Ancient religious artifacts are stored here.",
            "Donations to the monastery have accumulated here.",
        ],
        "shrine": [
            "Offerings to the gods fill the shrine vault.",
            "Sacred treasures are kept in the shrine's heart.",
            "Divine relics of immense power are stored here.",
        ],
        "default": [
            "A chamber where valuable items have been stored.",
            "Treasure awaits those brave enough to claim it.",
            "Riches gleam in the darkness of this chamber.",
        ],
    },
    RoomType.PUZZLE: {
        "dungeon": [
            "A room with strange mechanisms. A test of wit awaits.",
            "Pressure plates cover the dungeon floor.",
            "Levers and switches line the puzzle room walls.",
        ],
        "cave": [
            "A chamber with peculiar rock formations. Something seems off.",
            "Natural formations create a maze-like pattern.",
            "Cave crystals pulse with hidden energy.",
        ],
        "ruins": [
            "An ancient trial chamber. The builders left puzzles for intruders.",
            "Carved symbols form an ancient riddle.",
            "Mechanical traps guard the ruin's secrets.",
        ],
        "temple": [
            "A room of trials. Only the worthy may pass.",
            "Religious symbols must be arranged correctly.",
            "The temple tests your faith and wisdom.",
        ],
        "tomb": [
            "A trapped chamber protects the burial vault.",
            "Ancient mechanisms guard the tomb's secrets.",
            "The dead set riddles for the living.",
        ],
        "mine": [
            "A collapsed section requires careful navigation.",
            "Mining equipment must be used to clear the way.",
            "The mine shaft requires clever problem-solving.",
        ],
        "crypt": [
            "Coffins must be arranged to open the way.",
            "Names of the dead hold the key to progress.",
            "Ancient rituals must be performed correctly.",
        ],
        "tower": [
            "Magical wards require the right sequence to disable.",
            "Arcane symbols must be activated in order.",
            "The wizard's security system tests intruders.",
        ],
        "monastery": [
            "A meditation puzzle tests your inner peace.",
            "Prayer sequences must be performed correctly.",
            "The monks' riddles guard their secrets.",
        ],
        "shrine": [
            "Divine trials test the faithful.",
            "Sacred rituals must be performed to proceed.",
            "The gods test those who seek their blessing.",
        ],
        "default": [
            "A puzzle room designed to test intruders.",
            "Your wits will be tested in this chamber.",
            "Only the clever will find their way forward.",
        ],
    },
}


# =============================================================================
# NPC Templates (by role)
# =============================================================================

NPC_NAMES: dict[str, list[str]] = {
    "merchant": [
        "Traveling Merchant",
        "Local Trader",
        "Exotic Goods Vendor",
        "Specialty Dealer",
        "Wandering Peddler",
        "Caravan Trader",
    ],
    "guard": [
        "Town Guard",
        "Patrol Captain",
        "Gate Keeper",
        "Night Watchman",
        "Veteran Soldier",
        "Watch Commander",
    ],
    "quest_giver": [
        "Village Elder",
        "Mysterious Sage",
        "Desperate Villager",
        "Curious Scholar",
        "Worried Parent",
        "Local Mayor",
    ],
    "villager": [
        "Humble Farmer",
        "Local Craftsman",
        "Friendly Innkeeper",
        "Traveling Bard",
        "Weary Traveler",
        "Simple Peasant",
    ],
    "elder": [
        "Wise Elder",
        "Ancient Sage",
        "Village Patriarch",
        "Council Leader",
        "Tribal Chief",
        "Retired Hero",
    ],
    "blacksmith": [
        "Master Smith",
        "Forge Worker",
        "Weapon Crafter",
        "Armor Smith",
        "Apprentice Smith",
        "Dwarven Smith",
    ],
    "innkeeper": [
        "Jolly Innkeeper",
        "Tavern Master",
        "Barkeep",
        "Inn Proprietor",
        "Retired Adventurer",
        "Hospitable Host",
    ],
    "default": [
        "Mysterious Stranger",
        "Local Resident",
        "Passing Traveler",
        "Unknown Figure",
        "Silent Observer",
        "Curious Onlooker",
    ],
}

NPC_DESCRIPTIONS: dict[str, list[str]] = {
    "merchant": [
        "A weathered traveler with goods from distant lands.",
        "A shrewd trader always looking for a deal.",
        "A merchant with an eye for quality merchandise.",
        "A peddler carrying a pack full of wares.",
    ],
    "guard": [
        "A vigilant protector keeping watch for trouble.",
        "A battle-scarred warrior in worn armor.",
        "A stern-faced soldier with a ready weapon.",
        "A dutiful guard patrolling their assigned post.",
    ],
    "quest_giver": [
        "An anxious figure seeking help with a problem.",
        "Someone with an air of urgency about them.",
        "A person in need of a capable adventurer.",
        "A worried soul with a tale of woe.",
    ],
    "villager": [
        "An ordinary person going about their daily life.",
        "A hardworking resident of this community.",
        "A friendly face among the locals.",
        "A simple soul with simple concerns.",
    ],
    "elder": [
        "A wise figure with years of experience evident in their eyes.",
        "An ancient keeper of local knowledge and history.",
        "A respected leader whose counsel is valued.",
        "A sage whose wisdom spans many generations.",
    ],
    "blacksmith": [
        "A muscular craftsman with soot-stained hands.",
        "A skilled metalworker surrounded by tools.",
        "A forge master whose weapons are legendary.",
        "An artisan dedicated to their craft.",
    ],
    "innkeeper": [
        "A welcoming host with a warm smile.",
        "A busy publican serving food and drink.",
        "A seasoned tavern keeper who has seen much.",
        "A hospitable soul who makes travelers feel at home.",
    ],
    "default": [
        "A person of unknown purpose.",
        "Someone who catches your attention.",
        "A figure watching you with interest.",
        "An individual with their own story to tell.",
    ],
}

NPC_DIALOGUES: dict[str, list[str]] = {
    "merchant": [
        "Care to see my wares? I have goods from across the realm.",
        "Looking to buy or sell? I offer fair prices.",
        "Step right up! Quality merchandise at reasonable prices.",
        "Ah, a customer! Let me show you what I have.",
    ],
    "guard": [
        "Stay out of trouble, traveler.",
        "Keep your weapons sheathed within the walls.",
        "I'm watching you. No funny business.",
        "Move along. Nothing to see here.",
    ],
    "quest_giver": [
        "Please, I need help! Will you hear my plea?",
        "You look capable. I have a task that needs doing.",
        "Adventurer! I have a proposition for you.",
        "Thank the gods you're here. I have a problem only you can solve.",
    ],
    "villager": [
        "Good day to you, traveler.",
        "Passing through, are you? Safe travels.",
        "Haven't seen you around here before.",
        "Welcome to our humble community.",
    ],
    "elder": [
        "Wisdom comes with patience, young one.",
        "I have seen much in my years. Perhaps I can help.",
        "Listen well, for I speak of ancient matters.",
        "The old ways still have power, if you know where to look.",
    ],
    "blacksmith": [
        "Need your gear repaired? I'm the best in the region.",
        "Looking for a new weapon? I forge only the finest.",
        "The heat of the forge never bothers me.",
        "Quality steel and honest work, that's my motto.",
    ],
    "innkeeper": [
        "Welcome, weary traveler! Rest and refreshment await.",
        "A room for the night? Or perhaps a hot meal?",
        "Make yourself comfortable. We have everything you need.",
        "First drink's on the house for a new face!",
    ],
    "default": [
        "...",
        "Is there something you need?",
        "I have nothing to say to you.",
        "Perhaps we'll speak another time.",
    ],
}


# =============================================================================
# Item Templates (by type)
# =============================================================================

ITEM_TEMPLATES: dict[str, dict[str, list[dict]]] = {
    "weapon": {
        "dungeon": [
            {"name": "Ancient Blade", "description": "A weapon from a forgotten age.", "damage_bonus": 4},
            {"name": "Rusted Sword", "description": "Old but still deadly.", "damage_bonus": 2},
            {"name": "Dark Dagger", "description": "A blade touched by shadow.", "damage_bonus": 3},
        ],
        "cave": [
            {"name": "Crystal Sword", "description": "Forged from cave crystals.", "damage_bonus": 3},
            {"name": "Stalactite Dagger", "description": "Sharp as the cave itself.", "damage_bonus": 2},
            {"name": "Miner's Pick", "description": "A tool turned weapon.", "damage_bonus": 2},
        ],
        "ruins": [
            {"name": "Relic Blade", "description": "An ancient weapon of power.", "damage_bonus": 5},
            {"name": "Crumbling Sword", "description": "Old but enchanted.", "damage_bonus": 3},
            {"name": "Stone Axe", "description": "Primitive but effective.", "damage_bonus": 2},
        ],
        "temple": [
            {"name": "Holy Mace", "description": "Blessed by the temple priests.", "damage_bonus": 4},
            {"name": "Sacred Sword", "description": "A weapon of divine origin.", "damage_bonus": 5},
            {"name": "Ritual Dagger", "description": "Used in temple ceremonies.", "damage_bonus": 2},
        ],
        "default": [
            {"name": "Iron Sword", "description": "A simple but effective blade.", "damage_bonus": 3},
            {"name": "Battle Axe", "description": "A warrior's trusted weapon.", "damage_bonus": 4},
            {"name": "Steel Dagger", "description": "Quick and sharp.", "damage_bonus": 2},
        ],
    },
    "armor": {
        "dungeon": [
            {"name": "Dungeon Guard Armor", "description": "Worn by ancient guardians.", "defense_bonus": 3},
            {"name": "Shadow Cloak", "description": "Helps blend into darkness.", "defense_bonus": 2},
            {"name": "Iron Shield", "description": "Dented but sturdy.", "defense_bonus": 2},
        ],
        "cave": [
            {"name": "Crystal Armor", "description": "Made from cave crystals.", "defense_bonus": 4},
            {"name": "Stone Shield", "description": "Heavy but protective.", "defense_bonus": 3},
            {"name": "Miner's Helm", "description": "Protects from falling rocks.", "defense_bonus": 1},
        ],
        "ruins": [
            {"name": "Ancient Armor", "description": "Armor from a lost civilization.", "defense_bonus": 4},
            {"name": "Gilded Shield", "description": "Decorated but functional.", "defense_bonus": 3},
            {"name": "Relic Helm", "description": "An artifact of protection.", "defense_bonus": 2},
        ],
        "temple": [
            {"name": "Blessed Robes", "description": "Infused with divine protection.", "defense_bonus": 3},
            {"name": "Sacred Shield", "description": "Bears holy symbols.", "defense_bonus": 4},
            {"name": "Temple Guard Armor", "description": "Worn by the faithful.", "defense_bonus": 3},
        ],
        "default": [
            {"name": "Leather Armor", "description": "Basic but reliable protection.", "defense_bonus": 2},
            {"name": "Chain Mail", "description": "Interlocking metal rings.", "defense_bonus": 3},
            {"name": "Steel Shield", "description": "A warrior's defense.", "defense_bonus": 2},
        ],
    },
    "consumable": {
        "dungeon": [
            {"name": "Health Potion", "description": "Restores vitality.", "heal_amount": 25},
            {"name": "Antidote", "description": "Cures poison.", "heal_amount": 10},
            {"name": "Torch", "description": "Lights the way.", "heal_amount": 0},
        ],
        "cave": [
            {"name": "Cave Mushroom", "description": "Restores some health.", "heal_amount": 15},
            {"name": "Spring Water", "description": "Refreshing and healing.", "heal_amount": 10},
            {"name": "Glowing Moss", "description": "Provides faint light.", "heal_amount": 0},
        ],
        "ruins": [
            {"name": "Ancient Elixir", "description": "A powerful healing potion.", "heal_amount": 35},
            {"name": "Dust of Ages", "description": "Has mysterious properties.", "heal_amount": 5},
            {"name": "Relic Fragment", "description": "May have magical uses.", "heal_amount": 0},
        ],
        "temple": [
            {"name": "Holy Water", "description": "Blessed by the priests.", "heal_amount": 30},
            {"name": "Sacred Incense", "description": "Calms the spirit.", "heal_amount": 10},
            {"name": "Blessed Bread", "description": "Nourishing and healing.", "heal_amount": 20},
        ],
        "default": [
            {"name": "Health Potion", "description": "Restores health.", "heal_amount": 20},
            {"name": "Mana Potion", "description": "Restores magical energy.", "heal_amount": 0},
            {"name": "Bandage", "description": "Basic wound care.", "heal_amount": 10},
        ],
    },
    "misc": {
        "dungeon": [
            {"name": "Rusted Key", "description": "Opens something somewhere."},
            {"name": "Dungeon Map", "description": "Shows part of the layout."},
            {"name": "Ancient Coin", "description": "Currency from another age."},
        ],
        "cave": [
            {"name": "Glowing Crystal", "description": "Emanates faint light."},
            {"name": "Bat Guano", "description": "Useful for alchemy."},
            {"name": "Cave Pearl", "description": "A rare natural formation."},
        ],
        "ruins": [
            {"name": "Ancient Tome", "description": "Contains forgotten knowledge."},
            {"name": "Relic Shard", "description": "Part of something greater."},
            {"name": "Gilded Amulet", "description": "An ornate piece of jewelry."},
        ],
        "temple": [
            {"name": "Sacred Relic", "description": "An object of worship."},
            {"name": "Prayer Beads", "description": "Used in meditation."},
            {"name": "Temple Token", "description": "Grants access to sacred areas."},
        ],
        "default": [
            {"name": "Mysterious Object", "description": "Its purpose is unclear."},
            {"name": "Old Key", "description": "Opens something, perhaps."},
            {"name": "Strange Trinket", "description": "May have value to someone."},
        ],
    },
}


# =============================================================================
# Quest Templates (by category)
# =============================================================================

QUEST_TEMPLATES: dict[str, list[dict]] = {
    "dungeon": [
        {
            "name": "Clear the Depths",
            "description": "Eliminate the threat lurking in the dungeon.",
            "objective_type": "kill",
            "target": "Dungeon Boss",
        },
        {
            "name": "Retrieve the Artifact",
            "description": "Find the ancient relic hidden below.",
            "objective_type": "collect",
            "target": "Ancient Artifact",
        },
        {
            "name": "Explore the Unknown",
            "description": "Map the unexplored sections of the dungeon.",
            "objective_type": "explore",
            "target": "Dungeon Depths",
        },
    ],
    "cave": [
        {
            "name": "Hunt the Beast",
            "description": "Slay the creature terrorizing the caves.",
            "objective_type": "kill",
            "target": "Cave Beast",
        },
        {
            "name": "Mining Expedition",
            "description": "Collect rare crystals from the cave depths.",
            "objective_type": "collect",
            "target": "Rare Crystal",
        },
        {
            "name": "Find the Lost Miner",
            "description": "Locate the missing miner in the caves.",
            "objective_type": "talk",
            "target": "Lost Miner",
        },
    ],
    "ruins": [
        {
            "name": "Uncover the Past",
            "description": "Explore the ancient ruins and discover their secrets.",
            "objective_type": "explore",
            "target": "Ancient Ruins",
        },
        {
            "name": "Defeat the Guardian",
            "description": "Overcome the ancient guardian protecting the ruins.",
            "objective_type": "kill",
            "target": "Ruin Guardian",
        },
        {
            "name": "Recover the Relic",
            "description": "Find the priceless artifact within the ruins.",
            "objective_type": "collect",
            "target": "Lost Relic",
        },
    ],
    "temple": [
        {
            "name": "Temple Trials",
            "description": "Complete the sacred trials of the temple.",
            "objective_type": "explore",
            "target": "Inner Sanctum",
        },
        {
            "name": "Purify the Temple",
            "description": "Cleanse the temple of its corruption.",
            "objective_type": "kill",
            "target": "Temple Corruption",
        },
        {
            "name": "Speak to the Oracle",
            "description": "Seek wisdom from the temple oracle.",
            "objective_type": "talk",
            "target": "Temple Oracle",
        },
    ],
    "town": [
        {
            "name": "Help the Townsfolk",
            "description": "Assist the town with various tasks.",
            "objective_type": "talk",
            "target": "Town Elder",
        },
        {
            "name": "Gather Supplies",
            "description": "Collect supplies for the town's needs.",
            "objective_type": "collect",
            "target": "Town Supplies",
        },
        {
            "name": "Patrol the Streets",
            "description": "Help guard the town from threats.",
            "objective_type": "explore",
            "target": "Town Streets",
        },
    ],
    "default": [
        {
            "name": "A Simple Task",
            "description": "Complete a straightforward objective.",
            "objective_type": "explore",
            "target": "Destination",
        },
        {
            "name": "Eliminate the Threat",
            "description": "Deal with a dangerous enemy.",
            "objective_type": "kill",
            "target": "Enemy",
        },
        {
            "name": "Retrieve the Item",
            "description": "Find and return a lost object.",
            "objective_type": "collect",
            "target": "Lost Item",
        },
    ],
}


# =============================================================================
# FallbackContentProvider Class
# =============================================================================


@dataclass
class FallbackContentProvider:
    """Provides fallback content using seeded RNG for determinism.

    This class generates content for rooms, NPCs, items, and quests when
    AI generation is unavailable. All output is deterministic based on
    the seed provided at initialization.

    Attributes:
        seed: Random seed for deterministic generation.
    """

    seed: int
    _rng: "random.Random" = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the random number generator with the provided seed."""
        self._rng = random.Random(self.seed)

    def get_room_content(self, room_type: RoomType, category: str) -> dict:
        """Generate room name and description.

        Args:
            room_type: The type of room (ENTRY, CORRIDOR, CHAMBER, etc.)
            category: The location category (dungeon, cave, temple, etc.)

        Returns:
            Dict with 'name' and 'description' keys.
        """
        # Get name from room type templates
        names = ROOM_NAMES.get(room_type, ["Unknown Chamber"])
        name = self._rng.choice(names)

        # Get description from room type + category templates
        desc_by_category = ROOM_DESCRIPTIONS.get(room_type, {})
        category_lower = category.lower() if category else "default"

        # Try category-specific, fall back to default
        descriptions = desc_by_category.get(category_lower)
        if not descriptions:
            descriptions = desc_by_category.get("default", ["A mysterious chamber."])

        description = self._rng.choice(descriptions)

        return {"name": name, "description": description}

    def get_npc_content(self, role: str, category: str) -> dict:
        """Generate NPC name, description, and dialogue.

        Args:
            role: The NPC's role (merchant, guard, quest_giver, etc.)
            category: The location category for context.

        Returns:
            Dict with 'name', 'description', and 'dialogue' keys.
        """
        role_lower = role.lower() if role else "default"

        # Get name from role templates
        names = NPC_NAMES.get(role_lower, NPC_NAMES["default"])
        name = self._rng.choice(names)

        # Get description from role templates
        descriptions = NPC_DESCRIPTIONS.get(role_lower, NPC_DESCRIPTIONS["default"])
        description = self._rng.choice(descriptions)

        # Get dialogue from role templates
        dialogues = NPC_DIALOGUES.get(role_lower, NPC_DIALOGUES["default"])
        dialogue = self._rng.choice(dialogues)

        return {"name": name, "description": description, "dialogue": dialogue}

    def get_item_content(self, item_type: str, category: str) -> dict:
        """Generate item name, description, and stats.

        Args:
            item_type: Type of item (weapon, armor, consumable, misc)
            category: The location category for thematic content.

        Returns:
            Dict with 'name', 'description', 'item_type', and relevant stats.
        """
        item_type_lower = item_type.lower() if item_type else "misc"
        category_lower = category.lower() if category else "default"

        # Get templates for this item type
        type_templates = ITEM_TEMPLATES.get(item_type_lower, ITEM_TEMPLATES["misc"])

        # Get category-specific items or default
        items = type_templates.get(category_lower, type_templates.get("default", []))
        if not items:
            items = type_templates.get("default", [{"name": "Unknown Item", "description": "A mysterious object."}])

        item = self._rng.choice(items)

        # Build result with item_type
        result = {
            "name": item.get("name", "Unknown Item"),
            "description": item.get("description", "A mysterious object."),
            "item_type": item_type_lower,
        }

        # Add type-specific stats
        if "damage_bonus" in item:
            result["damage_bonus"] = item["damage_bonus"]
        if "defense_bonus" in item:
            result["defense_bonus"] = item["defense_bonus"]
        if "heal_amount" in item:
            result["heal_amount"] = item["heal_amount"]

        return result

    def get_quest_content(self, category: str) -> dict:
        """Generate quest name, description, and objective.

        Args:
            category: The location category for thematic quests.

        Returns:
            Dict with 'name', 'description', 'objective_type', and 'target'.
        """
        category_lower = category.lower() if category else "default"

        # Get quests for this category or default
        quests = QUEST_TEMPLATES.get(category_lower, QUEST_TEMPLATES["default"])
        quest = self._rng.choice(quests)

        return {
            "name": quest["name"],
            "description": quest["description"],
            "objective_type": quest["objective_type"],
            "target": quest["target"],
        }
