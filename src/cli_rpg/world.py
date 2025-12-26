"""World module for creating and managing game locations."""

import logging
import random
from typing import Optional, Tuple
from cli_rpg.models.location import Location
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.npc import NPC
from cli_rpg.world_grid import WorldGrid, OPPOSITE_DIRECTIONS

logger = logging.getLogger(__name__)


# Fallback location templates for when AI is unavailable
# Each template has a name pattern and descriptions based on direction
FALLBACK_LOCATION_TEMPLATES = [
    {
        "name_patterns": ["Wilderness", "Wild Plains", "Open Land", "Frontier"],
        "descriptions": [
            "An untamed wilderness stretches before you. The land here is wild and unexplored.",
            "Tall grass sways in the breeze across this open expanse. Few have traveled this way.",
            "The frontier beckons with promise of adventure. The path ahead is uncertain.",
        ]
    },
    {
        "name_patterns": ["Rocky Outcrop", "Stone Ridge", "Craggy Hills", "Boulder Field"],
        "descriptions": [
            "Large rocks and boulders dot the landscape. This terrain is rough but passable.",
            "A ridge of ancient stones rises from the earth. The rocks seem weathered by time.",
            "Craggy hills create an uneven terrain. Something about this place feels ancient.",
        ]
    },
    {
        "name_patterns": ["Misty Hollow", "Foggy Vale", "Shadowed Dell", "Dim Glade"],
        "descriptions": [
            "A mysterious mist hangs low over this hollow. Visibility is limited here.",
            "Shadows gather in this secluded dell. The air is cool and still.",
            "Fog drifts lazily through this vale. Sounds seem muffled and distant.",
        ]
    },
    {
        "name_patterns": ["Grassy Meadow", "Sunny Fields", "Rolling Hills", "Green Expanse"],
        "descriptions": [
            "A peaceful meadow extends in all directions. Wildflowers bloom among the grass.",
            "Rolling hills covered in lush grass create a gentle landscape.",
            "Sunlight warms this open field. It seems a good place to rest.",
        ]
    },
    {
        "name_patterns": ["Dense Thicket", "Tangled Woods", "Overgrown Path", "Wild Grove"],
        "descriptions": [
            "Thick vegetation crowds the path here. Branches reach out like grasping fingers.",
            "An overgrown grove where nature has reclaimed the land. Travel is slow but possible.",
            "Tangled underbrush makes movement difficult. This area sees few visitors.",
        ]
    },
]


def generate_fallback_location(
    direction: str,
    source_location: Location,
    target_coords: Tuple[int, int]
) -> Location:
    """Generate a fallback location when AI is unavailable.

    Creates a template-based location with appropriate name, description,
    coordinates, and connections. The generated location will always have
    at least one frontier exit for future expansion.

    Args:
        direction: The direction of travel from source (e.g., "north")
        source_location: The location the player is coming from
        target_coords: The (x, y) coordinates for the new location

    Returns:
        A new Location instance with proper connections
    """
    # Select a random template
    template = random.choice(FALLBACK_LOCATION_TEMPLATES)

    # Generate unique name with coordinate suffix to ensure uniqueness
    base_name = random.choice(template["name_patterns"])
    # Add coordinate suffix for uniqueness (e.g., "Wilderness (1, 2)")
    location_name = f"{base_name} ({target_coords[0]}, {target_coords[1]})"

    # Select random description
    description = random.choice(template["descriptions"])

    # Calculate back connection direction
    back_direction = OPPOSITE_DIRECTIONS[direction]

    # Create the new location
    new_location = Location(
        name=location_name,
        description=description,
        connections={back_direction: source_location.name},
        coordinates=target_coords
    )

    # Add at least one frontier exit for future expansion
    # Exclude the back direction and any direction that might conflict
    available_directions = [
        d for d in Location.VALID_DIRECTIONS
        if d != back_direction
    ]

    if available_directions:
        # Add 1-2 dangling exits for expansion
        num_exits = random.randint(1, min(2, len(available_directions)))
        chosen_exits = random.sample(available_directions, num_exits)
        for exit_dir in chosen_exits:
            placeholder_name = f"Unexplored {exit_dir.title()}"
            new_location.add_connection(exit_dir, placeholder_name)

    logger.info(f"Generated fallback location '{location_name}' at {target_coords}")
    return new_location


# Import AI components (optional)
try:
    from cli_rpg.ai_service import AIService
    from cli_rpg.ai_world import create_ai_world
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIService = None  # type: ignore[misc, assignment]
    create_ai_world = None  # type: ignore[assignment]


def create_default_world() -> tuple[dict[str, Location], str]:
    """Create and return the default game world with 6 locations.

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: "Town Square" (the default starting location)

    The default world consists of:
    - Town Square: Overworld landmark at (0, 0) with connections north to Forest
      and east to Cave. Contains sub-locations: Market District, Guard Post, Town Well.
    - Market District: Sub-location of Town Square, contains Merchant NPC
    - Guard Post: Sub-location of Town Square, contains Guard NPC
    - Town Well: Sub-location of Town Square, atmospheric location
    - Forest: Northern location at (0, 1) with connection south to Town Square
    - Cave: Eastern location at (1, 0) with connection west to Town Square
    """
    # Create WorldGrid for consistent spatial representation
    grid = WorldGrid()

    # Create Town Square as overworld landmark with sub-locations
    town_square = Location(
        name="Town Square",
        description="A bustling town square with a fountain in the center. Pathways lead to various districts.",
        is_overworld=True,
        is_safe_zone=True,
        sub_locations=["Market District", "Guard Post", "Town Well"],
        entry_point="Market District"
    )

    # Create Forest as overworld landmark with sub-locations (danger zone)
    forest = Location(
        name="Forest",
        description="A vast, dark forest stretches before you. Ancient trees tower overhead, their canopy blocking most sunlight. Multiple paths wind deeper into the woods.",
        is_overworld=True,
        is_safe_zone=False,  # Danger zone
        sub_locations=["Forest Edge", "Deep Woods", "Ancient Grove"],
        entry_point="Forest Edge"
    )

    # Create Millbrook Village as overworld landmark with sub-locations (safe zone)
    millbrook = Location(
        name="Millbrook Village",
        description="A small rural village surrounded by wheat fields. Smoke rises from cottage chimneys, and the sound of a blacksmith's hammer echoes through the air.",
        is_overworld=True,
        is_safe_zone=True,
        sub_locations=["Village Square", "Inn", "Blacksmith"],
        entry_point="Village Square"
    )

    # Create Abandoned Mines as overworld dungeon with sub-locations (danger zone)
    abandoned_mines = Location(
        name="Abandoned Mines",
        description="A dark entrance yawns in the hillside, wooden beams rotting at the threshold. The clang of pickaxes once echoed here, but now only silence and the occasional rumble from deep below.",
        is_overworld=True,
        is_safe_zone=False,  # Danger zone
        category="dungeon",
        sub_locations=["Mine Entrance", "Upper Tunnels", "Flooded Level", "Boss Chamber"],
        entry_point="Mine Entrance"
    )

    # Create Ironhold City as overworld landmark with sub-locations (safe zone)
    ironhold_city = Location(
        name="Ironhold City",
        description="A massive walled city of stone and steel. Towers rise above fortified walls, and the streets bustle with merchants, soldiers, and citizens from across the realm.",
        is_overworld=True,
        is_safe_zone=True,
        sub_locations=["Ironhold Market", "Castle Ward", "Slums", "Temple Quarter"],
        entry_point="Ironhold Market"
    )

    cave = Location(
        name="Cave",
        description="A dark cave with damp walls. You can hear water dripping somewhere deeper inside.",
        hidden_secrets=[
            {
                "type": "hidden_treasure",
                "description": "A glinting gemstone wedged in a crack in the cave wall.",
                "threshold": 13,
                "discovered": False
            }
        ]
    )

    # Place locations on grid (coordinates determine connections automatically)
    # Town Square at origin (0, 0)
    grid.add_location(town_square, 0, 0)
    # Forest is north of Town Square (0, 1)
    grid.add_location(forest, 0, 1)
    # Cave is east of Town Square (1, 0)
    grid.add_location(cave, 1, 0)
    # Millbrook Village is west of Town Square (-1, 0)
    grid.add_location(millbrook, -1, 0)
    # Abandoned Mines is north of Cave (1, 1)
    grid.add_location(abandoned_mines, 1, 1)
    # Ironhold City is south of Town Square (0, -1)
    grid.add_location(ironhold_city, 0, -1)

    # Create default merchant shop
    potion = Item(
        name="Health Potion",
        description="Restores 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25
    )
    sword = Item(
        name="Iron Sword",
        description="A sturdy blade",
        item_type=ItemType.WEAPON,
        damage_bonus=5
    )
    armor = Item(
        name="Leather Armor",
        description="Light protection",
        item_type=ItemType.ARMOR,
        defense_bonus=3
    )
    torch = Item(
        name="Torch",
        description="A wooden torch that provides light in dark places",
        item_type=ItemType.CONSUMABLE,
        light_duration=5
    )
    lockpick = Item(
        name="Lockpick",
        description="A thin metal tool for bypassing locks. Rogues only.",
        item_type=ItemType.CONSUMABLE,
        heal_amount=0
    )
    camping_supplies = Item(
        name="Camping Supplies",
        description="Essential supplies for camping in the wilderness",
        item_type=ItemType.CONSUMABLE,
        heal_amount=0
    )
    stamina_potion = Item(
        name="Stamina Potion",
        description="A refreshing brew that restores physical energy",
        item_type=ItemType.CONSUMABLE,
        stamina_restore=25
    )

    shop_items = [
        ShopItem(item=potion, buy_price=50),
        ShopItem(item=sword, buy_price=100),
        ShopItem(item=armor, buy_price=80),
        ShopItem(item=torch, buy_price=15),
        ShopItem(item=lockpick, buy_price=30),
        ShopItem(item=camping_supplies, buy_price=40),  # Spec: 40 gold in Market District
        ShopItem(item=stamina_potion, buy_price=30),  # Spec: 30 gold, 25 stamina restore
    ]
    shop = Shop(name="General Store", inventory=shop_items)
    merchant = NPC(
        name="Merchant",
        description="A friendly shopkeeper with various wares",
        dialogue="Welcome, traveler! Take a look at my goods.",
        is_merchant=True,
        shop=shop,
        greetings=[
            "Welcome, traveler! Take a look at my goods.",
            "Ah, a customer! What can I get for you today?",
            "Come in, come in! Best prices in town!",
        ]
    )

    # Create Guard NPC
    guard = NPC(
        name="Guard",
        description="A vigilant town guard keeping watch over the area",
        dialogue="Stay out of trouble, adventurer.",
        greetings=[
            "Stay out of trouble, adventurer.",
            "The roads have been dangerous lately.",
            "Keep your weapons sheathed in town.",
        ]
    )

    # Create sub-locations for Town Square
    market_district = Location(
        name="Market District",
        description="Colorful market stalls line the cobblestone streets. The smell of fresh bread mingles with exotic spices.",
        parent_location="Town Square",
        is_safe_zone=True,
        connections={}  # No cardinal exits for sub-locations
    )
    market_district.npcs.append(merchant)

    guard_post = Location(
        name="Guard Post",
        description="A fortified stone building where the town guard keeps watch. Weapons and armor hang on the walls.",
        parent_location="Town Square",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "lore_hint",
                "description": "Scratched tally marks on the wall count recent monster sightings in the forest.",
                "threshold": 12,
                "discovered": False
            }
        ]
    )
    guard_post.npcs.append(guard)

    town_well = Location(
        name="Town Well",
        description="An ancient stone well in a quiet corner of town. Moss grows between the weathered stones.",
        parent_location="Town Square",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "hidden_treasure",
                "description": "A loose stone conceals a small pouch of forgotten coins.",
                "threshold": 10,
                "discovered": False
            }
        ]
    )

    # Create sub-locations for Forest (all danger zones)
    forest_edge = Location(
        name="Forest Edge",
        description="The forest boundary where civilization meets wilderness. Dappled sunlight still penetrates here, but the path ahead grows darker.",
        parent_location="Forest",
        is_safe_zone=False,
        category="forest",
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "trap",
                "description": "A concealed snare trap lies hidden among the fallen leaves.",
                "threshold": 12,
                "discovered": False
            }
        ]
    )

    deep_woods = Location(
        name="Deep Woods",
        description="Towering trees block out the sky. Strange sounds echo through the underbrush, and the air is thick with the scent of decay and growth.",
        parent_location="Forest",
        is_safe_zone=False,
        category="forest",
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "hidden_door",
                "description": "An overgrown path, nearly invisible, leads to a hidden clearing.",
                "threshold": 14,
                "discovered": False
            }
        ]
    )

    ancient_grove = Location(
        name="Ancient Grove",
        description="A mystical clearing surrounded by impossibly old trees. An ancient presence watches from the shadows, and the air thrums with primal power.",
        parent_location="Forest",
        is_safe_zone=False,
        category="forest",
        connections={},  # No cardinal exits for sub-locations
        boss_enemy="elder_treant",
        treasures=[
            {
                "name": "Mossy Chest",
                "description": "An ancient chest covered in moss, half-buried beneath the roots of a great tree",
                "locked": True,
                "difficulty": 2,  # +10% bonus (relatively easy)
                "opened": False,
                "items": [
                    {"name": "Forest Gem", "description": "A pulsing green gem that glows with forest magic", "item_type": "misc"},
                    {"name": "Health Potion", "description": "Restores 25 HP", "item_type": "consumable", "heal_amount": 25}
                ],
                "requires_key": None
            }
        ],
        hidden_secrets=[
            {
                "type": "lore_hint",
                "description": "Ancient runes carved into the bark tell of a guardian spirit bound to protect this grove.",
                "threshold": 15,
                "discovered": False
            }
        ]
    )

    # Create Hermit NPC (recruitable)
    hermit = NPC(
        name="Hermit",
        description="A weathered old man in tattered robes who has lived in the forest for decades",
        dialogue="The forest speaks to those who listen...",
        is_recruitable=True,
        greetings=[
            "The forest speaks to those who listen...",
            "Few venture this deep. You have courage... or foolishness.",
            "The trees have eyes, traveler. They've watched you since you entered.",
        ]
    )
    ancient_grove.npcs.append(hermit)

    # Create NPCs for Millbrook Village
    elder = NPC(
        name="Elder",
        description="A wise old woman who has lived in Millbrook all her life",
        dialogue="The old ways are not forgotten here, traveler.",
        greetings=[
            "The old ways are not forgotten here, traveler.",
            "Welcome to Millbrook. We are simple folk, but kind.",
            "I have seen much in my years. Perhaps I can share some wisdom.",
        ]
    )

    # Create innkeeper shop with supplies for travelers
    village_potion = Item(
        name="Health Potion",
        description="Restores 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25
    )
    village_camping_supplies = Item(
        name="Camping Supplies",
        description="Essential supplies for camping in the wilderness",
        item_type=ItemType.CONSUMABLE,
        heal_amount=0
    )
    village_torch = Item(
        name="Torch",
        description="A wooden torch that provides light in dark places",
        item_type=ItemType.CONSUMABLE,
        light_duration=5
    )
    innkeeper_shop_items = [
        ShopItem(item=village_potion, buy_price=45),  # Slightly cheaper than town
        ShopItem(item=village_camping_supplies, buy_price=30),  # Spec: 30 gold rural discount
        ShopItem(item=village_torch, buy_price=12),
    ]
    innkeeper_shop = Shop(name="Millbrook Inn Supplies", inventory=innkeeper_shop_items)

    innkeeper = NPC(
        name="Innkeeper",
        description="A jovial man with a hearty laugh who runs the village inn",
        dialogue="Rest your weary bones, friend!",
        is_merchant=True,
        shop=innkeeper_shop,
        is_recruitable=True,
        greetings=[
            "Rest your weary bones, friend!",
            "A traveler! Come, warm yourself by the fire.",
            "We have the best ale in the region, I promise you that!",
        ]
    )

    # Create Blacksmith shop with weapons and armor
    steel_sword = Item(
        name="Steel Sword",
        description="A well-crafted blade from the village smithy",
        item_type=ItemType.WEAPON,
        damage_bonus=8
    )
    chainmail = Item(
        name="Chainmail",
        description="Interlocking metal rings providing solid protection",
        item_type=ItemType.ARMOR,
        defense_bonus=6
    )
    iron_helmet = Item(
        name="Iron Helmet",
        description="A sturdy helmet forged in the village",
        item_type=ItemType.ARMOR,
        defense_bonus=2
    )
    blacksmith_items = [
        ShopItem(item=steel_sword, buy_price=150),
        ShopItem(item=chainmail, buy_price=200),
        ShopItem(item=iron_helmet, buy_price=75),
    ]
    blacksmith_shop = Shop(name="Village Smithy", inventory=blacksmith_items)

    blacksmith_npc = NPC(
        name="Blacksmith",
        description="A muscular woman covered in soot, working the forge",
        dialogue="Looking for steel? You've come to the right place.",
        is_merchant=True,
        shop=blacksmith_shop,
        greetings=[
            "Looking for steel? You've come to the right place.",
            "I forge the finest blades in the region.",
            "Need something repaired? Or perhaps a new weapon?",
        ]
    )

    # Create sub-locations for Millbrook Village (all safe zones)
    village_square = Location(
        name="Village Square",
        description="A humble village square with a weathered wooden well at its center. Villagers go about their daily routines.",
        parent_location="Millbrook Village",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "lore_hint",
                "description": "A worn inscription on the well reads: 'May the harvest never fail.'",
                "threshold": 10,
                "discovered": False
            }
        ]
    )
    village_square.npcs.append(elder)

    inn = Location(
        name="Inn",
        description="A cozy inn with a roaring fireplace. The smell of fresh bread and ale fills the air.",
        parent_location="Millbrook Village",
        is_safe_zone=True,
        connections={}  # No cardinal exits for sub-locations
    )
    inn.npcs.append(innkeeper)

    blacksmith_loc = Location(
        name="Blacksmith",
        description="A hot, smoky workshop filled with weapons, armor, and tools. The forge glows orange.",
        parent_location="Millbrook Village",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "hidden_treasure",
                "description": "Coins hidden in the cold ashes of an unused corner of the forge.",
                "threshold": 12,
                "discovered": False
            }
        ]
    )
    blacksmith_loc.npcs.append(blacksmith_npc)

    # Create Old Miner NPC for Abandoned Mines
    old_miner = NPC(
        name="Old Miner",
        description="A grizzled old man with coal-stained hands and haunted eyes",
        dialogue="These mines... they took everything from us. Something woke up down there.",
        greetings=[
            "These mines... they took everything from us. Something woke up down there.",
            "You're not thinking of going deeper, are you? Foolish...",
            "I was the last one out. I still hear the screams some nights.",
        ]
    )

    # Create sub-locations for Abandoned Mines (all danger zones)
    mine_entrance = Location(
        name="Mine Entrance",
        description="The first chamber inside the mines. Abandoned mining equipment rusts in the corners, and old torches hang unlit on the walls. A cold draft blows from deeper within.",
        parent_location="Abandoned Mines",
        is_safe_zone=False,
        category="dungeon",
        connections={},  # No cardinal exits for sub-locations
        treasures=[
            {
                "name": "Rusted Strongbox",
                "description": "A heavy iron strongbox, its lock corroded but still functional",
                "locked": True,
                "difficulty": 3,  # No bonus/penalty (medium)
                "opened": False,
                "items": [
                    {"name": "Mining Pick", "description": "A sturdy mining pick that can double as a weapon", "item_type": "weapon", "damage_bonus": 4},
                    {"name": "Miner's Lantern", "description": "A small lantern that provides lasting light", "item_type": "consumable", "light_duration": 8}
                ],
                "requires_key": None
            }
        ]
    )
    mine_entrance.npcs.append(old_miner)

    upper_tunnels = Location(
        name="Upper Tunnels",
        description="Narrow passages carved through solid rock. The ceiling is low, and the walls are marked with old chisel strikes. Occasional cave-ins have blocked some paths.",
        parent_location="Abandoned Mines",
        is_safe_zone=False,
        category="dungeon",
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "trap",
                "description": "An unstable section of ceiling ready to collapse at the slightest disturbance.",
                "threshold": 14,
                "discovered": False
            }
        ]
    )

    flooded_level = Location(
        name="Flooded Level",
        description="The lower tunnels have flooded with dark, stagnant water. Wooden walkways float precariously, and the sound of dripping echoes endlessly. Something moves beneath the surface.",
        parent_location="Abandoned Mines",
        is_safe_zone=False,
        category="dungeon",
        connections={},  # No cardinal exits for sub-locations
        boss_enemy="drowned_overseer",  # Drowned mine overseer boss encounter
        hidden_secrets=[
            {
                "type": "hidden_treasure",
                "description": "A waterproof cache submerged beneath a loose plank contains mining payroll.",
                "threshold": 16,
                "discovered": False
            }
        ]
    )

    boss_chamber = Location(
        name="Boss Chamber",
        description="A vast natural cavern at the deepest point of the mines. Ancient crystals embedded in the walls give off an eerie glow. The bones of unlucky miners litter the ground. An ancient stone guardian looms in the darkness.",
        parent_location="Abandoned Mines",
        is_safe_zone=False,
        category="dungeon",
        connections={},  # No cardinal exits for sub-locations
        boss_enemy="stone_sentinel",  # Guaranteed boss encounter on first entry
        hidden_secrets=[
            {
                "type": "lore_hint",
                "description": "An ancient warning etched into the crystal reads: 'Disturb not the guardian's slumber.'",
                "threshold": 18,
                "discovered": False
            }
        ]
    )

    # Create luxury shop for Ironhold Market
    greater_health_potion = Item(
        name="Greater Health Potion",
        description="Restores 50 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=50
    )
    fine_steel_sword = Item(
        name="Steel Sword",
        description="A masterfully forged blade of the finest steel",
        item_type=ItemType.WEAPON,
        damage_bonus=10
    )
    plate_armor = Item(
        name="Plate Armor",
        description="Heavy plate armor offering excellent protection",
        item_type=ItemType.ARMOR,
        defense_bonus=10
    )
    luxury_shop_items = [
        ShopItem(item=greater_health_potion, buy_price=100),
        ShopItem(item=fine_steel_sword, buy_price=200),
        ShopItem(item=plate_armor, buy_price=350),
    ]
    luxury_shop = Shop(name="Ironhold Emporium", inventory=luxury_shop_items)

    # Create NPCs for Ironhold City
    wealthy_merchant = NPC(
        name="Wealthy Merchant",
        description="A richly dressed merchant dealing in fine goods and luxury items",
        dialogue="Welcome to Ironhold! Only the finest wares for discerning customers.",
        is_merchant=True,
        shop=luxury_shop,
        greetings=[
            "Welcome to Ironhold! Only the finest wares for discerning customers.",
            "Ah, you have the look of someone with coin to spend.",
            "My goods are the best in the realm. Quality comes at a price, of course.",
        ]
    )

    captain_of_guard = NPC(
        name="Captain of the Guard",
        description="A stern, battle-scarred officer in gleaming armor",
        dialogue="Ironhold stands strong. We keep the peace here, adventurer.",
        greetings=[
            "Ironhold stands strong. We keep the peace here, adventurer.",
            "The city walls have never been breached. Not on my watch.",
            "Report any suspicious activity to the guard post immediately.",
        ]
    )

    beggar = NPC(
        name="Beggar",
        description="A ragged figure huddled in the shadows, eyes sharp despite appearances",
        dialogue="Spare a coin? I know things, traveler... things that might interest you.",
        is_recruitable=True,
        greetings=[
            "Spare a coin? I know things, traveler... things that might interest you.",
            "The streets see everything, friend. I could be useful to you.",
            "Don't let the rags fool you. I've survived these alleys for years.",
        ]
    )

    priest = NPC(
        name="Priest",
        description="A serene figure in white robes, offering blessings and comfort to all",
        dialogue="May the light guide your path, traveler. The temple welcomes all.",
        greetings=[
            "May the light guide your path, traveler. The temple welcomes all.",
            "Peace be upon you, child. Have you come seeking healing?",
            "The divine watches over Ironhold. And over you, should you wish it.",
        ]
    )

    # Create sub-locations for Ironhold City (all safe zones)
    ironhold_market = Location(
        name="Ironhold Market",
        description="A grand marketplace beneath towering stone arches. Merchants from distant lands hawk exotic goods while city guards patrol the crowded stalls.",
        parent_location="Ironhold City",
        is_safe_zone=True,
        connections={}  # No cardinal exits for sub-locations
    )
    ironhold_market.npcs.append(wealthy_merchant)

    castle_ward = Location(
        name="Castle Ward",
        description="The noble district of Ironhold, where magnificent mansions line cobblestone streets. The city garrison is headquartered here.",
        parent_location="Ironhold City",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "lore_hint",
                "description": "A coded message in a noble's dropped letter hints at political intrigue.",
                "threshold": 16,
                "discovered": False
            }
        ]
    )
    castle_ward.npcs.append(captain_of_guard)

    slums = Location(
        name="Slums",
        description="A maze of narrow alleys and ramshackle buildings. The poor and desperate eke out a living in the shadow of the city's wealth.",
        parent_location="Ironhold City",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "hidden_door",
                "description": "A secret passage behind a loose board leads to the thieves' underground network.",
                "threshold": 14,
                "discovered": False
            }
        ]
    )
    slums.npcs.append(beggar)

    temple_quarter = Location(
        name="Temple Quarter",
        description="A peaceful district of temples and shrines. Incense smoke drifts through the air, and the sound of hymns echoes from within the grand cathedral.",
        parent_location="Ironhold City",
        is_safe_zone=True,
        connections={},  # No cardinal exits for sub-locations
        hidden_secrets=[
            {
                "type": "hidden_treasure",
                "description": "An old offering box behind a loose flagstone contains forgotten donations.",
                "threshold": 11,
                "discovered": False
            }
        ]
    )
    temple_quarter.npcs.append(priest)

    # Build world dictionary from grid plus sub-locations
    world = grid.as_dict()
    # Town Square sub-locations
    world["Market District"] = market_district
    world["Guard Post"] = guard_post
    world["Town Well"] = town_well
    # Forest sub-locations
    world["Forest Edge"] = forest_edge
    world["Deep Woods"] = deep_woods
    world["Ancient Grove"] = ancient_grove
    # Millbrook Village sub-locations
    world["Village Square"] = village_square
    world["Inn"] = inn
    world["Blacksmith"] = blacksmith_loc
    # Abandoned Mines sub-locations
    world["Mine Entrance"] = mine_entrance
    world["Upper Tunnels"] = upper_tunnels
    world["Flooded Level"] = flooded_level
    world["Boss Chamber"] = boss_chamber
    # Ironhold City sub-locations
    world["Ironhold Market"] = ironhold_market
    world["Castle Ward"] = castle_ward
    world["Slums"] = slums
    world["Temple Quarter"] = temple_quarter

    # Return world dictionary and starting location (backward compatible)
    return (world, "Town Square")


def create_world(
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy",
    strict: bool = True
) -> tuple[dict[str, Location], str]:
    """Create a game world, using AI if available.

    Args:
        ai_service: Optional AIService for AI-generated world
        theme: World theme (default: "fantasy")
        strict: If True (default), AI generation failures raise exceptions.
                If False, falls back to default world on AI error.

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: Name of the starting location in the world

    Raises:
        Exception: If strict=True and AI generation fails
    """
    if ai_service is not None and AI_AVAILABLE:
        if strict:
            # Strict mode: let exceptions propagate
            logger.info("Attempting to create AI-generated world (strict mode)")
            world, starting_location = create_ai_world(ai_service, theme=theme)
            return (world, starting_location)
        else:
            # Non-strict mode: fallback to default on error
            try:
                logger.info("Attempting to create AI-generated world")
                world, starting_location = create_ai_world(ai_service, theme=theme)
                return (world, starting_location)
            except Exception as e:
                logger.warning(f"AI world generation failed: {e}")
                logger.info("Falling back to default world")
                world, starting_location = create_default_world()
                return (world, starting_location)
    else:
        # Use default world
        world, starting_location = create_default_world()
        return (world, starting_location)
