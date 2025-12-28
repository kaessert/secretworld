"""FallbackContentProvider for deterministic content when AI is unavailable.

Provides expanded template-based fallback content for rooms, NPCs, items, and quests.
Uses seeded RNG for reproducibility. Templates are category-specific.

This module centralizes all fallback content generation that ContentLayer needs
when AIService is unavailable or fails.
"""

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from cli_rpg.procedural_interiors import RoomType

if TYPE_CHECKING:
    from cli_rpg.procedural_quests import QuestTemplateType


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
        # Wilderness POI categories
        "grove": [
            "A small clearing opens in the forest canopy.",
            "Ancient trees form a natural archway into the grove.",
            "Dappled sunlight filters through the leaves above.",
        ],
        "waystation": [
            "A simple shelter offers respite from travel.",
            "A weathered signpost marks this waystation.",
            "Travelers have left marks on the waystation walls.",
        ],
        "campsite": [
            "The remains of a campfire mark this resting spot.",
            "A cleared area provides shelter from the elements.",
            "Signs of previous camps dot this location.",
        ],
        "hollow": [
            "A hidden depression in the terrain opens before you.",
            "Thick vegetation conceals this secluded hollow.",
            "The hollow feels strangely protected from the outside.",
        ],
        "overlook": [
            "A scenic viewpoint reveals the lands below.",
            "Rocky outcrops form a natural viewing platform.",
            "The wind carries distant sounds to this overlook.",
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
        # Wilderness POI categories
        "grove": [
            "A winding path leads between ancient trees.",
            "Ferns brush against you as you walk the trail.",
            "Roots crisscross the forest floor.",
        ],
        "waystation": [
            "A covered walkway connects the waystation areas.",
            "Cobblestones mark the path between shelters.",
            "Traveler's graffiti decorates the passage walls.",
        ],
        "campsite": [
            "A worn path circles the central campfire.",
            "Gear and supplies line the campsite path.",
            "Footprints mark well-trodden routes through camp.",
        ],
        "hollow": [
            "A narrow trail winds deeper into the hollow.",
            "Overhanging branches form a natural tunnel.",
            "The path descends further into the secluded area.",
        ],
        "overlook": [
            "A rocky path leads along the overlook's edge.",
            "Stone steps carved into the cliff face.",
            "The trail offers glimpses of the vista below.",
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
        # Wilderness POI categories
        "grove": [
            "A peaceful clearing surrounded by ancient trees.",
            "Wildflowers carpet the grove floor.",
            "A natural spring bubbles up from the ground.",
        ],
        "waystation": [
            "A simple rest area with basic amenities.",
            "Storage for travelers' supplies fills the room.",
            "A small hearth provides warmth to weary travelers.",
        ],
        "campsite": [
            "A sheltered area with a fire pit at center.",
            "Sleeping areas have been prepared around the camp.",
            "Supplies and equipment are stored here.",
        ],
        "hollow": [
            "A secluded space hidden from the outside world.",
            "Moss covers the rocks in this sheltered hollow.",
            "The air is still and quiet in this hidden place.",
        ],
        "overlook": [
            "A flat platform offering panoramic views.",
            "Wind-carved rocks create natural seating.",
            "The vista stretches to the distant horizon.",
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
            {"name": "Dungeon Guard Armor", "description": "Worn by ancient guardians.", "defense_bonus": 3, "armor_weight": "heavy"},
            {"name": "Shadow Cloak", "description": "Helps blend into darkness.", "defense_bonus": 2, "armor_weight": "light"},
            {"name": "Iron Shield", "description": "Dented but sturdy.", "defense_bonus": 2, "armor_weight": "medium"},
        ],
        "cave": [
            {"name": "Crystal Armor", "description": "Made from cave crystals.", "defense_bonus": 4, "armor_weight": "heavy"},
            {"name": "Stone Shield", "description": "Heavy but protective.", "defense_bonus": 3, "armor_weight": "heavy"},
            {"name": "Miner's Helm", "description": "Protects from falling rocks.", "defense_bonus": 1, "armor_weight": "light"},
        ],
        "ruins": [
            {"name": "Ancient Armor", "description": "Armor from a lost civilization.", "defense_bonus": 4, "armor_weight": "heavy"},
            {"name": "Gilded Shield", "description": "Decorated but functional.", "defense_bonus": 3, "armor_weight": "medium"},
            {"name": "Relic Helm", "description": "An artifact of protection.", "defense_bonus": 2, "armor_weight": "light"},
        ],
        "temple": [
            {"name": "Blessed Robes", "description": "Infused with divine protection.", "defense_bonus": 3, "armor_weight": "light"},
            {"name": "Sacred Shield", "description": "Bears holy symbols.", "defense_bonus": 4, "armor_weight": "medium"},
            {"name": "Temple Guard Armor", "description": "Worn by the faithful.", "defense_bonus": 3, "armor_weight": "medium"},
        ],
        "default": [
            {"name": "Leather Armor", "description": "Basic but reliable protection.", "defense_bonus": 2, "armor_weight": "light"},
            {"name": "Chain Mail", "description": "Interlocking metal rings.", "defense_bonus": 3, "armor_weight": "medium"},
            {"name": "Steel Shield", "description": "A warrior's defense.", "defense_bonus": 2, "armor_weight": "medium"},
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
    "holy_symbol": {
        "temple": [
            {"name": "Sacred Relic of Light", "description": "A powerful holy symbol blessed by high priests.", "divine_power": 5},
            {"name": "Divine Emblem", "description": "An emblem radiating divine energy.", "divine_power": 4},
            {"name": "Blessed Talisman", "description": "A talisman infused with holy power.", "divine_power": 3},
            {"name": "Temple Holy Symbol", "description": "A standard symbol of the faith.", "divine_power": 2},
        ],
        "ruins": [
            {"name": "Ancient Holy Relic", "description": "A holy symbol from a forgotten age.", "divine_power": 4},
            {"name": "Relic of the Old Faith", "description": "Bears symbols of an ancient religion.", "divine_power": 3},
            {"name": "Crumbling Holy Icon", "description": "Old but still carries divine essence.", "divine_power": 2},
        ],
        "dungeon": [
            {"name": "Recovered Holy Symbol", "description": "A holy symbol reclaimed from darkness.", "divine_power": 3},
            {"name": "Guardian's Talisman", "description": "Once worn by a holy guardian.", "divine_power": 2},
        ],
        "default": [
            {"name": "Simple Holy Symbol", "description": "A wooden holy symbol of humble origin.", "divine_power": 2},
            {"name": "Blessed Pendant", "description": "A small pendant blessed by a cleric.", "divine_power": 1},
            {"name": "Holy Talisman", "description": "A basic talisman of faith.", "divine_power": 2},
        ],
    },
}


# =============================================================================
# Quest Templates (by category)
# =============================================================================

# =============================================================================
# Treasure Chest Templates (by category)
# =============================================================================

TREASURE_CHEST_NAMES: dict[str, list[str]] = {
    "dungeon": ["Iron Chest", "Dusty Strongbox", "Forgotten Coffer"],
    "cave": ["Stone Chest", "Crystal Box", "Hidden Cache"],
    "ruins": ["Ancient Chest", "Ruined Coffer", "Gilded Box"],
    "temple": ["Sacred Chest", "Offering Box", "Blessed Container"],
    "forest": ["Mossy Chest", "Hollow Log Cache", "Vine-Covered Box"],
    # Wilderness POI categories
    "grove": ["Root Cache", "Druid's Box", "Hidden Hollow"],
    "waystation": ["Traveler's Chest", "Supply Crate", "Wayside Cache"],
    "campsite": ["Supply Chest", "Camp Stash", "Abandoned Pack"],
    "hollow": ["Concealed Box", "Hidden Stash", "Secret Cache"],
    "overlook": ["Stone Cache", "Windswept Chest", "Lookout Stash"],
    "default": ["Treasure Chest", "Wooden Chest", "Old Coffer"],
}

TREASURE_CHEST_DESCRIPTIONS: dict[str, list[str]] = {
    "dungeon": [
        "An old chest left behind by previous adventurers.",
        "A dusty container sealed for ages.",
        "A forgotten strongbox covered in cobwebs.",
    ],
    "cave": [
        "A chest hidden among the rocks.",
        "A stone container wedged in a crevice.",
        "A cache concealed by cave formations.",
    ],
    "ruins": [
        "An ancient container from a forgotten era.",
        "A weathered chest bearing ancient symbols.",
        "A relic box from a lost civilization.",
    ],
    "temple": [
        "A sacred chest placed as an offering.",
        "A blessed container holding temple treasures.",
        "A ceremonial box with holy engravings.",
    ],
    "forest": [
        "A chest concealed by overgrown vegetation.",
        "A mossy container hidden beneath roots.",
        "A cache tucked away in a hollow tree.",
    ],
    # Wilderness POI categories
    "grove": [
        "A chest nestled among gnarled tree roots.",
        "A box hidden beneath a canopy of leaves.",
        "A cache left by forest dwellers.",
    ],
    "waystation": [
        "A chest left by passing travelers.",
        "A supply crate forgotten by merchants.",
        "A cache tucked under a wayside bench.",
    ],
    "campsite": [
        "A chest abandoned by previous campers.",
        "A supply stash near the fire pit.",
        "Gear left behind by travelers.",
    ],
    "hollow": [
        "A box concealed in the shadowy hollow.",
        "A stash hidden deep in the secluded space.",
        "A cache protected by thick underbrush.",
    ],
    "overlook": [
        "A chest wedged between weathered rocks.",
        "A cache overlooking the vista below.",
        "A box left by previous visitors.",
    ],
    "default": [
        "A mysterious treasure chest.",
        "An old chest waiting to be opened.",
        "A container holding unknown treasures.",
    ],
}

# Treasure loot tables per location category
# Items are selected randomly to populate treasure chests
TREASURE_LOOT_TABLES: dict[str, list[dict]] = {
    "dungeon": [
        {"name": "Ancient Blade", "item_type": "weapon", "damage_bonus": 4},
        {"name": "Rusted Key", "item_type": "misc"},
        {"name": "Health Potion", "item_type": "consumable", "heal_amount": 25},
    ],
    "cave": [
        {"name": "Glowing Crystal", "item_type": "misc"},
        {"name": "Cave Spider Venom", "item_type": "consumable", "heal_amount": 15},
        {"name": "Miner's Pickaxe", "item_type": "weapon", "damage_bonus": 3},
    ],
    "ruins": [
        {"name": "Ancient Tome", "item_type": "misc"},
        {"name": "Gilded Amulet", "item_type": "armor", "defense_bonus": 2, "armor_weight": "light"},
        {"name": "Relic Dust", "item_type": "consumable", "mana_restore": 20},
    ],
    "temple": [
        {"name": "Holy Water", "item_type": "consumable", "heal_amount": 30},
        {"name": "Sacred Relic", "item_type": "misc"},
        {"name": "Blessed Medallion", "item_type": "armor", "defense_bonus": 3, "armor_weight": "light"},
        {"name": "Temple Holy Symbol", "item_type": "holy_symbol", "divine_power": 2},
        {"name": "Blessed Talisman", "item_type": "holy_symbol", "divine_power": 3},
    ],
    "forest": [
        {"name": "Forest Gem", "item_type": "misc"},
        {"name": "Herbal Remedy", "item_type": "consumable", "heal_amount": 20},
        {"name": "Wooden Bow", "item_type": "weapon", "damage_bonus": 3},
    ],
    "default": [
        {"name": "Gold Coins", "item_type": "misc"},
        {"name": "Health Potion", "item_type": "consumable", "heal_amount": 20},
        {"name": "Iron Dagger", "item_type": "weapon", "damage_bonus": 2},
    ],
}


# =============================================================================
# Branch Name/Description Templates (by template_type x branch_id)
# Used by procedural_quests.generate_branches_for_template()
# =============================================================================

BRANCH_NAME_TEMPLATES: dict[str, dict[str, str]] = {
    "kill_boss": {
        "kill": "Eliminate {target}",
        "persuade": "Convince {target}",
        "betray": "Join {target}",
    },
    "kill_mobs": {
        "kill": "Exterminate {target}",
        "lure": "Drive Away {target}",
    },
    "collect": {
        "collect": "Gather {target}",
        "buy": "Purchase {target}",
    },
    "talk": {
        "talk": "Speak with {target}",
        "intimidate": "Threaten {target}",
    },
    "explore": {
        "explore": "Chart {target}",
        "scout": "Survey {target}",
    },
    "escort": {
        "escort": "Protect {target}",
        "abandon": "Leave {target}",
    },
    "fetch": {
        "fetch": "Retrieve {target}",
        "substitute": "Replace {target}",
    },
}

BRANCH_DESCRIPTION_TEMPLATES: dict[str, dict[str, str]] = {
    "kill_boss": {
        "kill": "Defeat {target} in combat to end the threat permanently.",
        "persuade": "Use diplomacy to convince {target} to stand down.",
        "betray": "Switch sides and join {target} for a greater reward.",
    },
    "kill_mobs": {
        "kill": "Eliminate all {target} to clear the area.",
        "lure": "Use bait or traps to drive {target} away without killing.",
    },
    "collect": {
        "collect": "Gather the required {target} from the area.",
        "buy": "Purchase {target} from merchants to save time.",
    },
    "talk": {
        "talk": "Have a peaceful conversation with {target}.",
        "intimidate": "Use threats to force {target} to comply.",
    },
    "explore": {
        "explore": "Carefully explore and map {target}.",
        "scout": "Quickly survey {target} from a distance.",
    },
    "escort": {
        "escort": "Safely guide {target} to their destination.",
        "abandon": "Leave {target} to their fate.",
    },
    "fetch": {
        "fetch": "Find and bring back the real {target}.",
        "substitute": "Provide a fake replacement for {target}.",
    },
}


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
# Quest Target Pools (by QuestTemplateType string value)
# These are used by procedural_quests.py for fallback content generation.
# =============================================================================

QUEST_TARGET_POOLS: dict[str, dict[str, list[str]]] = {
    "kill_boss": {
        "dungeon": ["Dark Lord", "Dungeon Master", "Shadow King", "Bone Tyrant"],
        "cave": ["Cave Beast", "Giant Spider", "Stone Golem", "Crystal Wurm"],
        "ruins": ["Ancient Guardian", "Ruin Spirit", "Forgotten King", "Spectral Warden"],
        "temple": ["Corrupted High Priest", "Temple Avatar", "Fallen Deity", "Dark Acolyte"],
        "default": ["Fearsome Monster", "Ancient Evil", "Dark Entity", "Dreaded Beast"],
    },
    "kill_mobs": {
        "dungeon": ["Skeletons", "Goblins", "Undead", "Cultists"],
        "cave": ["Cave Spiders", "Bats", "Cave Trolls", "Slimes"],
        "ruins": ["Stone Guardians", "Ghosts", "Haunted Spirits", "Animated Armor"],
        "temple": ["Corrupted Priests", "Temple Guards", "Zealots", "Possessed Monks"],
        "default": ["Monsters", "Creatures", "Enemies", "Beasts"],
    },
    "collect": {
        "dungeon": ["Ancient Coins", "Dungeon Keys", "Old Scrolls", "Rusty Relics"],
        "cave": ["Rare Crystals", "Cave Mushrooms", "Glowing Gems", "Spider Silk"],
        "ruins": ["Artifacts", "Relic Shards", "Ancient Texts", "Gilded Fragments"],
        "temple": ["Sacred Relics", "Holy Symbols", "Prayer Beads", "Blessed Incense"],
        "town": ["Supplies", "Trade Goods", "Merchant Wares", "Crafting Materials"],
        "village": ["Herbs", "Farm Produce", "Handmade Goods", "Wild Berries"],
        "default": ["Valuable Items", "Rare Objects", "Collectibles", "Treasures"],
    },
    "explore": {
        "dungeon": ["Deep Chambers", "Hidden Vault", "Lower Depths", "Secret Passage"],
        "cave": ["Crystal Cavern", "Underground Lake", "Deep Tunnels", "Hidden Grotto"],
        "ruins": ["Lost Library", "Ancient Temple", "Forgotten Halls", "Crumbled Tower"],
        "temple": ["Inner Sanctum", "Sacred Grove", "Holy Shrine", "Prayer Chamber"],
        "default": ["Unknown Region", "Unexplored Area", "Hidden Place", "Secret Location"],
    },
    "talk": {
        "dungeon": ["Imprisoned Sage", "Lost Explorer", "Dungeon Hermit", "Escaped Prisoner"],
        "cave": ["Lost Miner", "Cave Hermit", "Stranded Traveler", "Trapped Scholar"],
        "ruins": ["Ancient Ghost", "Ruin Scholar", "Old Guardian", "Spectral Historian"],
        "temple": ["Temple Oracle", "High Priest", "Sacred Keeper", "Wise Monk"],
        "town": ["Town Elder", "Local Sage", "Guild Master", "Merchant Lord"],
        "village": ["Village Elder", "Wise Woman", "Local Healer", "Old Farmer"],
        "default": ["Mysterious Figure", "Wise Elder", "Knowledgeable One", "Hidden Sage"],
    },
    "escort": {
        "temple": ["Pilgrim", "Acolyte", "Sacred Messenger", "Holy Traveler"],
        "town": ["Merchant", "Noble", "Traveler", "Diplomat"],
        "village": ["Farmer", "Child", "Elderly Villager", "Young Apprentice"],
        "default": ["Refugee", "Survivor", "Wanderer", "Lost Soul"],
    },
    "fetch": {
        "town": ["Medicine", "Important Letter", "Trade Goods", "Legal Documents"],
        "village": ["Herbal Remedy", "Lost Heirloom", "Farm Supplies", "Family Keepsake"],
        "temple": ["Sacred Text", "Holy Relic", "Blessed Water", "Temple Offering"],
        "default": ["Valuable Package", "Important Item", "Requested Object", "Precious Cargo"],
    },
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

    def get_treasure_content(
        self, category: str, distance: int = 1, z_level: int = 0
    ) -> dict:
        """Generate treasure chest name, description, and loot items.

        Args:
            category: Location category (dungeon, cave, temple, etc.)
            distance: Manhattan distance from entry (affects difficulty)
            z_level: Z-level of the location (negative = deeper, affects difficulty)

        Returns:
            Dict with 'name', 'description', 'difficulty', and 'items' list.
        """
        category_lower = category.lower() if category else "default"

        # Get chest name
        names = TREASURE_CHEST_NAMES.get(category_lower, TREASURE_CHEST_NAMES["default"])
        name = self._rng.choice(names)

        # Get chest description
        descriptions = TREASURE_CHEST_DESCRIPTIONS.get(
            category_lower, TREASURE_CHEST_DESCRIPTIONS["default"]
        )
        description = self._rng.choice(descriptions)

        # Get loot table
        loot_table = TREASURE_LOOT_TABLES.get(
            category_lower, TREASURE_LOOT_TABLES["default"]
        )

        # Select 1-2 items from loot table
        num_items = self._rng.randint(1, min(2, len(loot_table)))
        items = self._rng.sample(loot_table, num_items)

        # Lock difficulty scales with distance and depth (minimum 1)
        # abs(z_level) because z_level is negative for deeper levels
        difficulty = max(1, distance + abs(z_level) + self._rng.randint(0, 1))

        return {
            "name": name,
            "description": description,
            "difficulty": difficulty,
            "items": [item.copy() for item in items],
        }

    def get_quest_target(self, template_type: str, category: str) -> str:
        """Get a random target name for a quest template type.

        Uses the QUEST_TARGET_POOLS to select an appropriate target
        based on the template type and location category.

        Args:
            template_type: The QuestTemplateType value string
                (e.g., "kill_boss", "collect", "explore").
            category: The location category (dungeon, cave, temple, etc.)

        Returns:
            A target name string appropriate for the quest type and category.
        """
        type_pools = QUEST_TARGET_POOLS.get(template_type, QUEST_TARGET_POOLS.get("explore", {}))
        category_lower = category.lower() if category else "default"

        targets = type_pools.get(category_lower)
        if not targets:
            targets = type_pools.get("default", ["Target"])

        return self._rng.choice(targets)

    def get_branch_content(
        self, template_type: str, branch_id: str, target: str, category: str
    ) -> dict:
        """Generate branch name and description for a quest branch.

        Uses BRANCH_NAME_TEMPLATES and BRANCH_DESCRIPTION_TEMPLATES to
        create thematic content for quest branches.

        Args:
            template_type: The QuestTemplateType value string (e.g., "kill_boss").
            branch_id: The branch identifier (e.g., "kill", "persuade").
            target: The quest target name to substitute into templates.
            category: The location category for context (not currently used).

        Returns:
            Dict with 'name' and 'description' keys.
        """
        # Get name template
        name_templates = BRANCH_NAME_TEMPLATES.get(template_type, {})
        name_template = name_templates.get(branch_id, f"{branch_id.capitalize()} {{target}}")
        name = name_template.format(target=target)

        # Ensure name fits QuestBranch constraints (reasonable length)
        if len(name) > 30:
            name = name[:27] + "..."

        # Get description template
        desc_templates = BRANCH_DESCRIPTION_TEMPLATES.get(template_type, {})
        desc_template = desc_templates.get(
            branch_id, f"Complete the {branch_id} objective involving {{target}}."
        )
        description = desc_template.format(target=target)

        # Ensure description fits constraints
        if len(description) > 200:
            description = description[:197] + "..."

        return {"name": name, "description": description}
