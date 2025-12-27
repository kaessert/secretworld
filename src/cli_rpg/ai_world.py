"""AI-powered world generation module."""

import logging
import random
from typing import Optional
from cli_rpg.ai_service import AIService
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.quest import Quest, ObjectiveType
from cli_rpg.world_grid import WorldGrid, SubGrid, DIRECTION_OFFSETS, get_subgrid_bounds
from cli_rpg.location_art import get_fallback_location_ascii_art


# Set up logging
logger = logging.getLogger(__name__)


# Safe zone categories (no random encounters)
SAFE_ZONE_CATEGORIES = {"town", "village", "settlement"}

# Categories that should have bosses in deepest room
BOSS_CATEGORIES = frozenset({"dungeon", "cave", "ruins"})


def _find_furthest_room(
    placed_locations: dict,
    prefer_lowest_z: bool = False
) -> Optional[str]:
    """Find the room furthest from entry (0,0,0) for boss placement.

    Args:
        placed_locations: Dict mapping location names to placement data.
            Each entry should have 'relative_coords' (tuple of 2 or 3) and 'is_entry' (bool).
        prefer_lowest_z: If True, prioritize lowest z-level over Manhattan distance.
            Boss rooms are placed at the deepest level first, then by distance.

    Returns:
        Name of the furthest room, or None if no non-entry rooms exist.
    """
    if prefer_lowest_z:
        # Find the lowest z-level first, then furthest by Manhattan distance at that level
        lowest_z = 0
        candidates = []

        for name, data in placed_locations.items():
            if data.get("is_entry", False):
                continue

            rel_coords = data.get("relative_coords", (0, 0, 0))
            if len(rel_coords) == 2:
                rel_x, rel_y = rel_coords
                rel_z = 0
            else:
                rel_x, rel_y, rel_z = rel_coords

            # Track lowest z-level seen
            if rel_z < lowest_z:
                lowest_z = rel_z
                candidates = [(name, rel_x, rel_y, rel_z)]
            elif rel_z == lowest_z:
                candidates.append((name, rel_x, rel_y, rel_z))

        if not candidates:
            return None

        # Among candidates at lowest z-level, find furthest by Manhattan distance
        max_distance = -1
        furthest_name = None
        for name, rel_x, rel_y, rel_z in candidates:
            distance = abs(rel_x) + abs(rel_y)
            if distance > max_distance:
                max_distance = distance
                furthest_name = name

        return furthest_name
    else:
        # Original 2D behavior: just Manhattan distance from origin
        max_distance = -1
        furthest_name = None
        for name, data in placed_locations.items():
            if data.get("is_entry", False):
                continue

            rel_coords = data.get("relative_coords", (0, 0))
            if len(rel_coords) == 2:
                rel_x, rel_y = rel_coords
            else:
                rel_x, rel_y, _ = rel_coords

            distance = abs(rel_x) + abs(rel_y)
            if distance > max_distance:
                max_distance = distance
                furthest_name = name
        return furthest_name


def _place_treasures(
    placed_locations: dict,
    entry_category: str,
) -> None:
    """Place treasures in non-entry rooms based on area size.

    Modifies placed_locations in-place by adding treasures to Location objects.

    Args:
        placed_locations: Dict mapping location names to placement data.
            Each entry has 'location' (Location), 'relative_coords', 'is_entry'.
        entry_category: Category of the entry location (dungeon, cave, etc.)

    Treasure distribution:
        - 1 chest for 2-3 rooms
        - 2 chests for 4-5 rooms
        - 3 chests for 6+ rooms

    Excludes entry rooms and boss rooms from treasure placement.
    """
    # Only place treasures in appropriate categories
    if entry_category not in TREASURE_CATEGORIES:
        return

    # Collect non-entry, non-boss rooms with their distances from entry
    candidates = []
    for name, data in placed_locations.items():
        if data.get("is_entry", False):
            continue
        loc = data.get("location")
        if loc is None:
            continue
        # Skip boss rooms (boss IS the reward)
        if loc.boss_enemy is not None:
            continue
        # Support both 2D and 3D coordinates
        rel_coords = data.get("relative_coords", (0, 0, 0))
        if len(rel_coords) == 2:
            rel_x, rel_y = rel_coords
            rel_z = 0
        else:
            rel_x, rel_y, rel_z = rel_coords
        distance = abs(rel_x) + abs(rel_y)
        candidates.append((name, distance, rel_z, loc))

    if not candidates:
        return

    # Determine number of chests based on total room count
    total_rooms = len(placed_locations)
    if total_rooms <= 3:
        num_chests = 1
    elif total_rooms <= 5:
        num_chests = 2
    else:
        num_chests = 3

    # Limit to available candidates
    num_chests = min(num_chests, len(candidates))

    # Sort candidates by distance (furthest first for distribution)
    candidates.sort(key=lambda x: -x[1])

    # Select rooms with spread distribution
    # Pick every N-th candidate to spread chests across the area
    step = max(1, len(candidates) // num_chests)
    selected = []
    for i in range(0, len(candidates), step):
        if len(selected) < num_chests:
            selected.append(candidates[i])

    # Create treasures for selected rooms
    for name, distance, z_level, loc in selected:
        treasure = _create_treasure_chest(entry_category, distance, z_level)
        loc.treasures.append(treasure)


def _create_treasure_chest(category: str, distance: int, z_level: int = 0) -> dict:
    """Create a treasure chest with thematic items.

    Args:
        category: Location category (dungeon, cave, etc.)
        distance: Manhattan distance from entry (affects difficulty)
        z_level: Z-level of the location (negative = deeper, affects difficulty)

    Returns:
        Treasure dict with schema matching Location.treasures
    """
    # Get thematic chest name
    chest_names = TREASURE_CHEST_NAMES.get(category, ["Treasure Chest"])
    chest_name = random.choice(chest_names)

    # Get thematic loot
    loot_table = TREASURE_LOOT_TABLES.get(category, TREASURE_LOOT_TABLES["dungeon"])
    # Select 1-2 items from loot table
    num_items = random.randint(1, min(2, len(loot_table)))
    items = random.sample(loot_table, num_items)

    # Lock difficulty scales with distance and depth (minimum 1)
    # abs(z_level) because z_level is negative for deeper levels
    difficulty = max(1, distance + abs(z_level) + random.randint(0, 1))

    # Generate description based on chest name and category
    descriptions = {
        "dungeon": "An old chest left behind by previous adventurers.",
        "cave": "A chest hidden among the rocks.",
        "ruins": "An ancient container from a forgotten era.",
        "temple": "A sacred chest placed as an offering.",
        "forest": "A chest concealed by overgrown vegetation.",
    }
    description = descriptions.get(category, "A mysterious treasure chest.")

    return {
        "name": chest_name,
        "description": description,
        "locked": True,
        "difficulty": difficulty,
        "opened": False,
        "items": [item.copy() for item in items],
        "requires_key": None,
    }


def _infer_hierarchy_from_category(category: Optional[str]) -> tuple[bool, bool]:
    """Infer hierarchy fields from location category.

    Args:
        category: Location category (town, dungeon, forest, etc.)

    Returns:
        Tuple of (is_overworld, is_safe_zone):
        - is_overworld: True for all AI-generated locations (overworld by default)
        - is_safe_zone: True for safe categories (town, village, settlement)
    """
    is_safe = category in SAFE_ZONE_CATEGORIES if category else False
    return (True, is_safe)


def _create_default_merchant_shop(
    terrain_type: Optional[str] = None,
) -> Shop:
    """Create a default shop for AI-generated merchant NPCs.

    Args:
        terrain_type: Optional terrain type for thematic inventory

    Returns:
        Shop with terrain-appropriate items (always includes Health Potion)
    """
    # Health Potion is always included as baseline
    potion = Item(
        name="Health Potion",
        description="Restores 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25
    )
    shop_items = [ShopItem(item=potion, buy_price=50)]

    # Get terrain-specific items
    terrain_key = terrain_type.lower() if terrain_type else "plains"
    terrain_items = TERRAIN_SHOP_ITEMS.get(terrain_key, TERRAIN_SHOP_ITEMS["plains"])

    for name, desc, itype, price, stats in terrain_items:
        item = Item(
            name=name,
            description=desc,
            item_type=itype,
            **stats
        )
        shop_items.append(ShopItem(item=item, buy_price=price))

    shop_name = TERRAIN_SHOP_NAMES.get(terrain_key, "Traveling Wares")
    return Shop(name=shop_name, inventory=shop_items)


# Keywords that indicate a merchant NPC
MERCHANT_KEYWORDS = {"merchant", "trader", "vendor", "shopkeeper", "seller", "dealer"}


# Terrain-specific default shop inventories
# Each terrain has thematic items plus a base Health Potion
# Format: (name, description, item_type, price, stats_dict)
TERRAIN_SHOP_ITEMS: dict[str, list[tuple[str, str, ItemType, int, dict]]] = {
    "mountain": [
        ("Climbing Pick", "Essential for scaling rocky terrain", ItemType.MISC, 45, {}),
        ("Warm Cloak", "Protection against mountain cold", ItemType.ARMOR, 60, {"defense_bonus": 2}),
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
    ],
    "swamp": [
        ("Antidote", "Cures poison", ItemType.CONSUMABLE, 40, {}),
        ("Insect Repellent", "Wards off swamp insects", ItemType.CONSUMABLE, 25, {}),
        ("Wading Boots", "Keeps feet dry in marshland", ItemType.ARMOR, 55, {"defense_bonus": 1}),
    ],
    "desert": [
        ("Water Skin", "Precious water for desert travel", ItemType.CONSUMABLE, 30, {"stamina_restore": 15}),
        ("Sun Cloak", "Protection from harsh desert sun", ItemType.ARMOR, 50, {"defense_bonus": 1}),
        ("Antidote", "Cures poison from desert creatures", ItemType.CONSUMABLE, 40, {}),
    ],
    "forest": [
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Hemp Rope", "Sturdy rope for woodland travel", ItemType.MISC, 25, {}),
        ("Herbalist's Kit", "Basic healing herbs", ItemType.CONSUMABLE, 35, {"heal_amount": 15}),
    ],
    "beach": [
        ("Fishing Net", "For catching coastal fish", ItemType.MISC, 30, {}),
        ("Sturdy Rope", "Sea-worthy rope", ItemType.MISC, 25, {}),
        ("Dried Fish", "Preserved seafood", ItemType.CONSUMABLE, 15, {"heal_amount": 8}),
    ],
    "foothills": [
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Climbing Rope", "For ascending rocky terrain", ItemType.MISC, 35, {}),
        ("Warm Blanket", "Comfort in cool mountain nights", ItemType.MISC, 25, {}),
    ],
    "hills": [
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Walking Staff", "Aids travel over hilly terrain", ItemType.WEAPON, 40, {"damage_bonus": 2}),
        ("Antidote", "Cures poison", ItemType.CONSUMABLE, 40, {}),
    ],
    "plains": [
        ("Travel Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Antidote", "Cures poison", ItemType.CONSUMABLE, 40, {}),
    ],
}

# Terrain-specific shop names for immersion
TERRAIN_SHOP_NAMES: dict[str, str] = {
    "mountain": "Mountain Supplies",
    "swamp": "Swampland Wares",
    "desert": "Desert Provisions",
    "forest": "Woodland Goods",
    "beach": "Coastal Trading Post",
    "foothills": "Hillside Supplies",
    "hills": "Hilltop Wares",
    "plains": "Traveling Wares",
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
        {"name": "Gilded Amulet", "item_type": "armor", "defense_bonus": 2},
        {"name": "Relic Dust", "item_type": "consumable", "mana_restore": 20},
    ],
    "temple": [
        {"name": "Holy Water", "item_type": "consumable", "heal_amount": 30},
        {"name": "Sacred Relic", "item_type": "misc"},
        {"name": "Blessed Medallion", "item_type": "armor", "defense_bonus": 3},
    ],
    "forest": [
        {"name": "Forest Gem", "item_type": "misc"},
        {"name": "Herbal Remedy", "item_type": "consumable", "heal_amount": 20},
        {"name": "Wooden Bow", "item_type": "weapon", "damage_bonus": 3},
    ],
}

# Thematic chest names per category
TREASURE_CHEST_NAMES: dict[str, list[str]] = {
    "dungeon": ["Iron Chest", "Dusty Strongbox", "Forgotten Coffer"],
    "cave": ["Stone Chest", "Crystal Box", "Hidden Cache"],
    "ruins": ["Ancient Chest", "Ruined Coffer", "Gilded Box"],
    "temple": ["Sacred Chest", "Offering Box", "Blessed Container"],
    "forest": ["Mossy Chest", "Hollow Log Cache", "Vine-Covered Box"],
}

# Categories that should have treasure chests placed
TREASURE_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple", "forest"})

# Categories that should have hidden secrets
SECRET_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple", "forest"})

# Categories that should have puzzles (Issue #23)
PUZZLE_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple"})

# Secret templates: (type, description, base_threshold)
SECRET_TEMPLATES: dict[str, list[tuple[str, str, int]]] = {
    "dungeon": [
        ("hidden_treasure", "A loose stone conceals a hidden cache.", 13),
        ("hidden_door", "Faint scratches on the floor suggest a secret passage.", 14),
        ("trap", "A pressure plate lurks beneath the dust.", 12),
        ("lore_hint", "Ancient writing on the wall tells of forgotten secrets.", 11),
    ],
    "cave": [
        ("hidden_treasure", "A glinting gemstone wedged in a crack.", 12),
        ("trap", "Unstable rocks threaten to fall.", 11),
        ("lore_hint", "Primitive drawings depict something deeper in the caves.", 10),
    ],
    "ruins": [
        ("hidden_treasure", "An ornate box buried beneath rubble.", 14),
        ("hidden_door", "A worn section of wall hints at a secret passage.", 15),
        ("lore_hint", "Faded inscriptions speak of the civilization that fell here.", 12),
    ],
    "temple": [
        ("hidden_treasure", "An offering hidden behind the altar.", 13),
        ("trap", "A divine ward protects this sacred place.", 14),
        ("lore_hint", "Sacred texts reveal the temple's true purpose.", 11),
    ],
    "forest": [
        ("hidden_treasure", "A hollow tree conceals a traveler's stash.", 11),
        ("hidden_door", "An overgrown path leads to a hidden clearing.", 13),
        ("trap", "A concealed snare lies among the leaves.", 12),
    ],
}

# Puzzle templates by category (Issue #23)
# Format varies by type:
#   LOCKED_DOOR: (type, name, desc, required_key, hint_threshold, hint_text)
#   LEVER/PRESSURE_PLATE: (type, name, desc, None, hint_threshold, hint_text)
#   RIDDLE: (type, name, desc, riddle_text, riddle_answer, hint_threshold, hint_text)
#   SEQUENCE: (type, name, desc, sequence_ids, hint_threshold, hint_text)
from cli_rpg.models.puzzle import PuzzleType

PUZZLE_TEMPLATES: dict[str, list[tuple]] = {
    "dungeon": [
        # LOCKED_DOOR puzzles
        (PuzzleType.LOCKED_DOOR, "Rusted Iron Door", "A heavy iron door blocks the passage.",
         "Iron Key", 14, "The lock shows signs of rust."),
        (PuzzleType.LOCKED_DOOR, "Ancient Stone Door", "A massive stone door with intricate carvings.",
         "Stone Key", 15, "The keyhole matches ancient stonework."),
        # LEVER puzzles
        (PuzzleType.LEVER, "Wall Lever", "A rusted lever protrudes from the wall.",
         None, 12, "Scratch marks show it can be pulled."),
        (PuzzleType.LEVER, "Chain Mechanism", "Heavy chains hang from a pulley.",
         None, 13, "The chain is worn from use."),
        # PRESSURE_PLATE puzzles
        (PuzzleType.PRESSURE_PLATE, "Floor Plate", "A stone plate slightly raised from the floor.",
         None, 11, "It depresses slightly under weight."),
        # RIDDLE puzzles
        (PuzzleType.RIDDLE, "Stone Guardian", "A statue with glowing eyes blocks the way.",
         "What has keys but no locks?", "piano", 15, "Think of music."),
        (PuzzleType.RIDDLE, "Whispering Face", "A carved face in the wall speaks in riddles.",
         "I have cities but no houses, forests but no trees. What am I?", "map", 14, "Think of representations."),
        # SEQUENCE puzzles
        (PuzzleType.SEQUENCE, "Torch Row", "Four torches line the walls.",
         ["torch_1", "torch_2", "torch_3", "torch_4"], 16, "The murals show a lighting order."),
    ],
    "cave": [
        (PuzzleType.PRESSURE_PLATE, "Cracked Stone", "A cracked stone in the floor.",
         None, 10, "Pressure seems to shift it."),
        (PuzzleType.LEVER, "Crystal Lever", "A lever formed from cave crystal.",
         None, 11, "The crystal glows faintly."),
        (PuzzleType.LOCKED_DOOR, "Boulder Door", "A massive boulder blocks the tunnel.",
         "Cave Key", 13, "There's a keyhole in the rock."),
    ],
    "ruins": [
        (PuzzleType.LOCKED_DOOR, "Sealed Portal", "An ancient portal sealed by magic.",
         "Portal Key", 15, "Glyphs suggest a key exists."),
        (PuzzleType.RIDDLE, "Ancient Oracle", "A spectral figure poses a challenge.",
         "I am always in front of you but can never be seen. What am I?", "future", 14, "Think of time."),
        (PuzzleType.SEQUENCE, "Rune Stones", "Three rune stones glow dimly.",
         ["rune_sun", "rune_moon", "rune_star"], 15, "The ceiling mural shows the order."),
    ],
    "temple": [
        (PuzzleType.RIDDLE, "Sacred Guardian", "A divine statue guards the sanctum.",
         "What is given freely but cannot be bought?", "love", 13, "Think of the heart."),
        (PuzzleType.LEVER, "Altar Mechanism", "A hidden lever behind the altar.",
         None, 12, "The altar can be moved."),
        (PuzzleType.LOCKED_DOOR, "Blessed Gate", "A gate protected by divine wards.",
         "Holy Key", 14, "A blessed key would open it."),
    ],
}


def _generate_secrets_for_location(
    category: str,
    distance: int = 0,
    z_level: int = 0
) -> list[dict]:
    """Generate 1-2 hidden secrets for a location.

    Args:
        category: Location category (dungeon, cave, etc.)
        distance: Distance from entry (affects threshold)
        z_level: Z-level of the location (negative = deeper, affects threshold)

    Returns:
        List of secret dicts matching Location.hidden_secrets schema
    """
    if category not in SECRET_CATEGORIES:
        return []

    templates = SECRET_TEMPLATES.get(category, SECRET_TEMPLATES.get("dungeon", []))
    if not templates:
        return []

    num_secrets = random.randint(1, 2)
    selected = random.sample(templates, min(num_secrets, len(templates)))

    secrets = []
    for secret_type, description, base_threshold in selected:
        # Threshold scales with distance and depth (abs(z_level) for negative z)
        threshold = base_threshold + min(distance, 4) + abs(z_level)
        secret = {
            "type": secret_type,
            "description": description,
            "threshold": threshold,
            "discovered": False,
        }

        if secret_type == "hidden_treasure":
            # Deeper secrets give better rewards
            secret["reward_gold"] = random.randint(10, 30) + (distance * 5) + (abs(z_level) * 10)
        elif secret_type == "trap":
            # Deeper traps are more dangerous
            secret["trap_damage"] = 5 + (distance * 2) + (abs(z_level) * 3)
        elif secret_type == "hidden_door":
            secret["exit_direction"] = random.choice(["north", "south", "east", "west"])

        secrets.append(secret)

    return secrets


def _generate_puzzles_for_location(
    category: str,
    distance: int = 0,
    z_level: int = 0,
    available_directions: Optional[list[str]] = None,
) -> tuple[list, list[str], list[tuple[str, str]]]:
    """Generate 0-2 puzzles for a location.

    Args:
        category: Location category (dungeon, cave, etc.)
        distance: Distance from entry (affects chance and difficulty)
        z_level: Z-level of location (negative = deeper)
        available_directions: Directions that can be blocked

    Returns:
        Tuple of (puzzles, blocked_directions, keys_to_place):
        - puzzles: List of Puzzle objects
        - blocked_directions: List of directions blocked by puzzles
        - keys_to_place: List of (key_name, category) for locked doors
    """
    from cli_rpg.models.puzzle import Puzzle, PuzzleType

    if category not in PUZZLE_CATEGORIES:
        return ([], [], [])

    templates = PUZZLE_TEMPLATES.get(category, [])
    if not templates:
        return ([], [], [])

    # No puzzles at entry (distance=0)
    if distance == 0:
        return ([], [], [])

    # 50% chance of 1 puzzle, 25% chance of 2 puzzles, 25% chance of none
    roll = random.random()
    if roll < 0.25:
        num_puzzles = 0
    elif roll < 0.75:
        num_puzzles = 1
    else:
        num_puzzles = 2

    if num_puzzles == 0:
        return ([], [], [])

    # Use available directions if provided, else default
    directions = list(available_directions) if available_directions else ["north", "south", "east", "west"]
    if not directions:
        return ([], [], [])

    selected = random.sample(templates, min(num_puzzles, len(templates)))
    puzzles = []
    blocked = []
    keys_to_place = []

    for template in selected:
        puzzle_type = template[0]
        # Pick a direction to block
        if not directions:
            break
        target_dir = random.choice(directions)
        directions.remove(target_dir)

        # Scale hint threshold with distance and depth
        base_threshold = template[-2]
        threshold = base_threshold + min(distance, 3) + abs(z_level)
        hint_text = template[-1]

        if puzzle_type == PuzzleType.LOCKED_DOOR:
            # (type, name, desc, required_key, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                required_key=template[3],
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
            keys_to_place.append((template[3], category))
        elif puzzle_type == PuzzleType.LEVER or puzzle_type == PuzzleType.PRESSURE_PLATE:
            # (type, name, desc, None, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
        elif puzzle_type == PuzzleType.RIDDLE:
            # (type, name, desc, riddle_text, riddle_answer, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                riddle_text=template[3],
                riddle_answer=template[4],
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
        elif puzzle_type == PuzzleType.SEQUENCE:
            # (type, name, desc, sequence_ids, threshold, hint)
            puzzle = Puzzle(
                puzzle_type=puzzle_type,
                name=template[1],
                description=template[2],
                sequence_ids=list(template[3]),  # Copy the list
                target_direction=target_dir,
                hint_threshold=threshold,
                hint_text=hint_text,
            )
        else:
            continue

        puzzles.append(puzzle)
        blocked.append(target_dir)

    return (puzzles, blocked, keys_to_place)


def _place_keys_in_earlier_rooms(
    placed_locations: dict,
    keys_to_place: list[tuple[str, str, int]],
) -> None:
    """Place keys in rooms before their corresponding locked doors.

    Args:
        placed_locations: Dict of {name: {location, relative_coords, is_entry}}
        keys_to_place: List of (key_name, category, door_distance) tuples
    """
    for key_name, category, door_distance in keys_to_place:
        # Find valid rooms (distance < door_distance, not entry)
        candidates = []
        for name, data in placed_locations.items():
            if data.get("is_entry", False):
                continue
            loc = data.get("location")
            if loc is None:
                continue
            rel = data.get("relative_coords", (0, 0, 0))
            if len(rel) == 2:
                dist = abs(rel[0]) + abs(rel[1])
            else:
                dist = abs(rel[0]) + abs(rel[1])
            if dist < door_distance:
                candidates.append((name, dist, loc))

        if not candidates:
            # Fall back to entry room
            for name, data in placed_locations.items():
                if data.get("is_entry", False):
                    loc = data.get("location")
                    if loc is not None:
                        candidates.append((name, 0, loc))
                    break

        if candidates:
            # Pick room closest to door distance (more interesting placement)
            candidates.sort(key=lambda x: -x[1])
            _, _, room = candidates[0]

            # Create key item and add to room treasures
            key_item = {
                "name": key_name,
                "description": f"A key that might open something in the {category}.",
                "item_type": "misc",
            }
            # Add as a findable item (not locked chest)
            room.treasures.append({
                "name": f"Hidden {key_name}",
                "description": f"A {key_name.lower()} lies on the ground.",
                "locked": False,
                "difficulty": 0,
                "opened": False,
                "items": [key_item],
                "requires_key": None,
            })


def _create_shop_from_ai_inventory(shop_inventory: list[dict], shop_name: str) -> Optional[Shop]:
    """Create a Shop from AI-generated inventory items.

    Args:
        shop_inventory: List of item dicts with 'name', 'price', and optional:
            - item_type: "weapon", "armor", "consumable", or "misc" (default)
            - damage_bonus: int (for weapons)
            - defense_bonus: int (for armor)
            - heal_amount: int (for consumables)
            - stamina_restore: int (for consumables)
        shop_name: Name for the shop

    Returns:
        Shop with AI items, or None if inventory is empty/invalid
    """
    if not shop_inventory:
        return None

    shop_items = []
    for item_data in shop_inventory:
        try:
            # Determine item type from AI data (case-insensitive)
            type_str = item_data.get("item_type", "misc").lower()
            item_type = {
                "weapon": ItemType.WEAPON,
                "armor": ItemType.ARMOR,
                "consumable": ItemType.CONSUMABLE,
            }.get(type_str, ItemType.MISC)

            # Create item with stats from AI data
            item = Item(
                name=item_data["name"],
                description=f"A {item_data['name'].lower()} available for purchase.",
                item_type=item_type,
                damage_bonus=item_data.get("damage_bonus", 0),
                defense_bonus=item_data.get("defense_bonus", 0),
                heal_amount=item_data.get("heal_amount", 0),
                stamina_restore=item_data.get("stamina_restore", 0),
            )
            shop_items.append(ShopItem(item=item, buy_price=item_data["price"]))
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to create shop item from AI data: {e}")
            continue

    if not shop_items:
        return None

    return Shop(name=shop_name, inventory=shop_items)


def _generate_quest_for_npc(
    ai_service: Optional[AIService],
    npc_name: str,
    location_name: str,
    region_context: Optional[RegionContext],
    world_context: Optional[WorldContext],
    valid_locations: set[str],
    valid_npcs: set[str],
) -> Optional[Quest]:
    """Generate a quest for a quest_giver NPC.

    Uses region landmarks for EXPLORE targets, region theme for coherence.

    Args:
        ai_service: AIService instance for quest generation
        npc_name: Name of the NPC giving the quest
        location_name: Name of the location where NPC is located
        region_context: Optional Layer 2 context with landmarks
        world_context: Optional Layer 1 context with theme
        valid_locations: Set of valid location names (lowercase) for EXPLORE quests
        valid_npcs: Set of valid NPC names (lowercase) for TALK quests

    Returns:
        Quest instance if generation succeeds, None otherwise
    """
    if not ai_service:
        return None

    try:
        # Add region landmarks to valid locations for EXPLORE quests
        quest_valid_locations = set(valid_locations)
        if region_context:
            quest_valid_locations |= {landmark.lower() for landmark in region_context.landmarks}

        # Get theme from world context or default
        theme = world_context.theme if world_context else "fantasy"

        quest_data = ai_service.generate_quest(
            theme=theme,
            npc_name=npc_name,
            player_level=1,  # Default level, scales rewards
            location_name=location_name,
            valid_locations=quest_valid_locations,
            valid_npcs=valid_npcs,
        )

        return Quest(
            name=quest_data["name"],
            description=quest_data["description"],
            objective_type=ObjectiveType(quest_data["objective_type"]),
            target=quest_data["target"],
            target_count=quest_data["target_count"],
            gold_reward=quest_data["gold_reward"],
            xp_reward=quest_data["xp_reward"],
            quest_giver=npc_name,
        )
    except Exception as e:
        logger.warning(f"Failed to generate quest for {npc_name}: {e}")
        return None


def _create_npcs_from_data(
    npcs_data: list[dict],
    ai_service: Optional[AIService] = None,
    location_name: str = "",
    region_context: Optional[RegionContext] = None,
    world_context: Optional[WorldContext] = None,
    valid_locations: Optional[set[str]] = None,
    valid_npcs: Optional[set[str]] = None,
    terrain_type: Optional[str] = None,
) -> list[NPC]:
    """Create NPC objects from parsed NPC data.

    Args:
        npcs_data: List of NPC dictionaries from AI service
        ai_service: Optional AIService for quest generation
        location_name: Name of the location for quest context
        region_context: Optional Layer 2 context for quest generation
        world_context: Optional Layer 1 context for quest generation
        valid_locations: Optional set of valid location names for quests
        valid_npcs: Optional set of valid NPC names for quests
        terrain_type: Optional terrain type for terrain-appropriate shop inventory

    Returns:
        List of NPC objects
    """
    npcs = []
    for npc_data in npcs_data:
        try:
            role = npc_data.get("role", "villager")

            # Infer merchant role from name if not explicitly set
            if role == "villager":
                name_lower = npc_data["name"].lower()
                if any(keyword in name_lower for keyword in MERCHANT_KEYWORDS):
                    role = "merchant"

            is_merchant = role == "merchant"
            is_quest_giver = role == "quest_giver"

            # Create shop for merchant NPCs
            shop = None
            if is_merchant:
                # Try to use AI-generated inventory first
                ai_inventory = npc_data.get("shop_inventory", [])
                if ai_inventory:
                    shop = _create_shop_from_ai_inventory(
                        ai_inventory, f"{npc_data['name']}'s Wares"
                    )
                # Fall back to default shop if AI inventory failed
                if shop is None:
                    shop = _create_default_merchant_shop(terrain_type=terrain_type)

            # Get faction (optional) with role-based defaults
            faction = npc_data.get("faction")

            # Apply default factions by role if not explicitly specified
            if not faction:
                if role == "merchant":
                    faction = "Merchant Guild"
                elif role == "guard":
                    faction = "Town Watch"
                elif role == "quest_giver":
                    faction = "Adventurer's Guild"

            npc = NPC(
                name=npc_data["name"],
                description=npc_data["description"],
                dialogue=npc_data.get("dialogue", "Hello, traveler."),
                is_merchant=is_merchant,
                is_quest_giver=is_quest_giver,
                shop=shop,
                faction=faction
            )

            # Generate quest for quest_giver NPCs
            if is_quest_giver and ai_service:
                quest = _generate_quest_for_npc(
                    ai_service=ai_service,
                    npc_name=npc.name,
                    location_name=location_name,
                    region_context=region_context,
                    world_context=world_context,
                    valid_locations=valid_locations or set(),
                    valid_npcs=valid_npcs or set(),
                )
                if quest:
                    npc.offered_quests.append(quest)

            npcs.append(npc)
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to create NPC from data: {e}")
            continue
    return npcs


def _generate_location_ascii_art(
    ai_service: AIService,
    location_name: str,
    location_description: str,
    location_category: Optional[str],
    theme: str
) -> str:
    """Generate ASCII art for a location using AI with fallback.

    Tries to generate ASCII art using the AI service. If that fails,
    falls back to template-based art from location_art module.

    Args:
        ai_service: AIService instance
        location_name: Name of the location
        location_description: Description of the location
        location_category: Category of the location (town, forest, etc.)
        theme: World theme (e.g., "fantasy", "sci-fi")

    Returns:
        ASCII art string
    """
    try:
        return ai_service.generate_location_ascii_art(
            location_name=location_name,
            location_description=location_description,
            location_category=location_category,
            theme=theme
        )
    except Exception as e:
        logger.debug(f"AI location ASCII art generation failed, using fallback: {e}")
        return get_fallback_location_ascii_art(
            category=location_category,
            location_name=location_name
        )


def get_opposite_direction(direction: str) -> str:
    """Get the opposite direction.
    
    Args:
        direction: A valid direction (north, south, east, west, up, down)
    
    Returns:
        The opposite direction
    
    Raises:
        ValueError: If direction is invalid
    """
    opposites = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
        "up": "down",
        "down": "up"
    }
    
    if direction not in opposites:
        raise ValueError(f"Invalid direction: {direction}")
    
    return opposites[direction]


def generate_subgrid_for_location(
    location: Location,
    ai_service: Optional[AIService],
    theme: str,
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
) -> SubGrid:
    """Generate a SubGrid for an enterable named location on-demand.

    This function creates interior rooms/areas for locations like dungeons,
    caves, towns, etc. that should have enterable interiors but don't yet
    have a SubGrid attached.

    Args:
        location: The parent location to generate a SubGrid for
        ai_service: Optional AI service for content generation
        theme: World theme for generation
        world_context: Optional Layer 1 context for layered generation
        region_context: Optional Layer 2 context for layered generation

    Returns:
        A populated SubGrid with interior locations
    """
    from cli_rpg.world_grid import SubGrid, get_subgrid_bounds
    from cli_rpg.location_art import get_fallback_location_ascii_art

    # Get appropriate bounds for this location category
    bounds = get_subgrid_bounds(location.category)
    sub_grid = SubGrid(bounds=bounds, parent_name=location.name)

    # Try AI generation if available
    area_data = None
    if ai_service is not None:
        try:
            if world_context is not None and region_context is not None:
                # Use layered generation for coherent interiors
                area_data = ai_service.generate_area_with_context(
                    world_context=world_context,
                    region_context=region_context,
                    entry_direction="enter",  # Entering, not a cardinal direction
                    size=5,  # Reasonable interior size
                    terrain_type=location.terrain,
                )
            else:
                # Use basic area generation
                area_data = ai_service.generate_area(
                    theme=theme,
                    sub_theme_hint=f"interior of {location.category or 'building'}",
                    entry_direction="enter",
                    context_locations=[location.name],
                    size=5,
                )
        except Exception as e:
            logger.warning(f"AI area generation failed for {location.name}: {e}")
            area_data = None

    # Use fallback generation if AI failed or unavailable
    if not area_data:
        area_data = _generate_fallback_interior(location)

    # Place locations in SubGrid
    first_location = True
    placed_locations = {}
    all_keys_to_place = []  # Track keys for locked door puzzles

    for loc_data in area_data:
        # Support both 2D and 3D relative coordinates
        rel_coords = loc_data.get("relative_coords", (0, 0, 0))
        if len(rel_coords) == 2:
            rel_x, rel_y = rel_coords
            rel_z = 0
        else:
            rel_x, rel_y, rel_z = rel_coords

        # Check bounds (including z-bounds)
        if not sub_grid.is_within_bounds(rel_x, rel_y, rel_z):
            logger.debug(f"Skipping {loc_data['name']}: outside bounds")
            continue

        # Skip if coordinates occupied
        if sub_grid.get_by_coordinates(rel_x, rel_y, rel_z) is not None:
            continue

        # Generate ASCII art using fallback
        loc_ascii_art = get_fallback_location_ascii_art(
            category=loc_data.get("category", location.category),
            location_name=loc_data["name"]
        )

        # Infer hierarchy fields
        loc_category = loc_data.get("category", location.category)
        _, loc_is_safe_zone = _infer_hierarchy_from_category(loc_category)

        # Create the interior location
        new_loc = Location(
            name=loc_data["name"],
            description=loc_data["description"],
            category=loc_category,
            ascii_art=loc_ascii_art,
            is_overworld=False,  # Interior locations are not overworld
            is_safe_zone=loc_is_safe_zone,
            is_exit_point=first_location,  # First location is entry/exit
        )

        # Add NPCs if present
        if loc_data.get("npcs"):
            location_npcs = _create_npcs_from_data(
                loc_data["npcs"],
                terrain_type=location.terrain,
            )
            for npc in location_npcs:
                new_loc.npcs.append(npc)

        # Add hidden secrets to non-entry rooms
        if not first_location:
            distance = abs(rel_x) + abs(rel_y)
            secrets = _generate_secrets_for_location(loc_category or "dungeon", distance, rel_z)
            new_loc.hidden_secrets.extend(secrets)

            # Add puzzles to non-entry rooms (Issue #23)
            puzzles, blocked, keys = _generate_puzzles_for_location(
                loc_category or "dungeon", distance, rel_z
            )
            new_loc.puzzles.extend(puzzles)
            new_loc.blocked_directions.extend(blocked)
            # Track keys with door distance for placement
            for key_name, key_cat in keys:
                all_keys_to_place.append((key_name, key_cat, distance))

            # Add environmental hazards (Issue #26)
            from cli_rpg.hazards import get_hazards_for_category
            hazards = get_hazards_for_category(loc_category or "dungeon", distance)
            new_loc.hazards.extend(hazards)

        sub_grid.add_location(new_loc, rel_x, rel_y, rel_z)
        placed_locations[loc_data["name"]] = {
            "location": new_loc,
            "relative_coords": (rel_x, rel_y, rel_z),
            "is_entry": first_location,
        }
        first_location = False

    # Place boss in furthest room for dungeon-type categories (prefer lowest z)
    if location.category in BOSS_CATEGORIES and placed_locations:
        boss_room_name = _find_furthest_room(placed_locations, prefer_lowest_z=True)
        if boss_room_name:
            boss_room = sub_grid.get_by_name(boss_room_name)
            if boss_room:
                boss_room.boss_enemy = location.category  # Category-based boss

    # Place treasures in non-entry, non-boss rooms
    if placed_locations:
        _place_treasures(placed_locations, location.category or "dungeon")

    # Place keys for locked door puzzles in earlier rooms (Issue #23)
    if all_keys_to_place:
        _place_keys_in_earlier_rooms(placed_locations, all_keys_to_place)

    return sub_grid


def _generate_fallback_interior(location: Location) -> list[dict]:
    """Generate fallback interior locations when AI is unavailable.

    Creates a simple but functional interior layout based on location category.

    Args:
        location: The parent location to generate interior for

    Returns:
        List of location data dicts with relative_coords
    """
    category = (location.category or "building").lower()

    # Category-specific interior templates
    if category in ("dungeon", "cave", "ruins"):
        return [
            {
                "name": f"{location.name} Entrance",
                "description": f"The entrance to {location.name}. Dark passages stretch ahead.",
                "relative_coords": (0, 0),
                "category": category,
            },
            {
                "name": "Dark Corridor",
                "description": "A narrow passage with damp walls. Shadows dance at the edges of your vision.",
                "relative_coords": (0, 1),
                "category": category,
            },
            {
                "name": "Ancient Chamber",
                "description": "A larger room with crumbling pillars. Something valuable might be hidden here.",
                "relative_coords": (0, 2),
                "category": category,
            },
        ]
    elif category in ("town", "village", "city", "settlement"):
        return [
            {
                "name": f"{location.name} Gate",
                "description": f"The main entrance to {location.name}. Travelers come and go.",
                "relative_coords": (0, 0),
                "category": category,
            },
            {
                "name": "Town Square",
                "description": "The central gathering place. Merchants have set up stalls here.",
                "relative_coords": (0, 1),
                "category": category,
            },
            {
                "name": "Marketplace",
                "description": "A bustling area where goods are bought and sold.",
                "relative_coords": (1, 1),
                "category": category,
            },
        ]
    elif category == "temple":
        return [
            {
                "name": f"{location.name} Entrance",
                "description": f"The sacred entrance to {location.name}. Incense fills the air.",
                "relative_coords": (0, 0),
                "category": category,
            },
            {
                "name": "Prayer Hall",
                "description": "A hall lined with prayer cushions and religious icons.",
                "relative_coords": (0, 1),
                "category": category,
            },
            {
                "name": "Inner Sanctum",
                "description": "The holiest part of the temple. Few are permitted here.",
                "relative_coords": (0, 2),
                "category": category,
            },
        ]
    else:
        # Generic interior for shops, taverns, inns, etc.
        return [
            {
                "name": f"{location.name} Interior",
                "description": f"Inside {location.name}. The space is well-maintained.",
                "relative_coords": (0, 0),
                "category": category,
            },
            {
                "name": "Back Room",
                "description": "A private area at the back of the establishment.",
                "relative_coords": (0, 1),
                "category": category,
            },
        ]


def create_ai_world(
    ai_service: AIService,
    theme: str = "fantasy",
    starting_location_name: str = "Town Square",
    initial_size: int = 3
) -> tuple[dict[str, Location], str]:
    """Create an AI-generated world using grid-based placement.

    Args:
        ai_service: AIService instance for generating locations
        theme: World theme (e.g., "fantasy", "sci-fi")
        starting_location_name: Name for the starting location
        initial_size: Target number of locations to generate

    Returns:
        Tuple of (world, starting_location) where:
        - world: Dictionary mapping location names to Location instances
        - starting_location: Actual name of the starting location (may differ from parameter)

    Raises:
        AIServiceError: If generation fails
        ValueError: If generated locations fail validation
    """
    grid = WorldGrid()

    # Track coordinates for each location we place
    coord_queue = []  # List of (name, x, y, direction, suggested_target)

    # Generate starting location
    logger.info(f"Generating starting location: {starting_location_name}")
    starting_data = ai_service.generate_location(
        theme=theme,
        context_locations=[],
        source_location=None,
        direction=None
    )

    # Generate ASCII art for starting location
    starting_ascii_art = _generate_location_ascii_art(
        ai_service=ai_service,
        location_name=starting_data["name"],
        location_description=starting_data["description"],
        location_category=starting_data.get("category"),
        theme=theme
    )

    # Infer hierarchy fields from category
    starting_category = starting_data.get("category")
    is_overworld, is_safe_zone = _infer_hierarchy_from_category(starting_category)

    # Create starting location at origin (0, 0)
    # Note: No connections field - navigation is coordinate-based via WorldGrid
    starting_location = Location(
        name=starting_data["name"],
        description=starting_data["description"],
        category=starting_category,
        ascii_art=starting_ascii_art,
        is_overworld=is_overworld,
        is_safe_zone=is_safe_zone
    )
    grid.add_location(starting_location, 0, 0)

    # Add default merchant NPC to starting location for shop access
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
    shop_items = [
        ShopItem(item=potion, buy_price=50),
        ShopItem(item=sword, buy_price=100),
        ShopItem(item=armor, buy_price=80)
    ]
    shop = Shop(name="General Store", inventory=shop_items)
    merchant = NPC(
        name="Merchant",
        description="A friendly shopkeeper with various wares",
        dialogue="Welcome, traveler! Take a look at my goods.",
        is_merchant=True,
        shop=shop
    )
    starting_location.npcs.append(merchant)

    # Add quest giver NPC to starting location
    quest_giver = NPC(
        name="Town Elder",
        description="A wise figure who knows of many adventures",
        dialogue="Ah, a new adventurer! I may have tasks for you.",
        is_quest_giver=True,
        offered_quests=[]
    )
    starting_location.npcs.append(quest_giver)

    # Add AI-generated NPCs to starting location (if any)
    ai_npcs = _create_npcs_from_data(starting_data.get("npcs", []))
    for npc in ai_npcs:
        starting_location.npcs.append(npc)

    # Queue ALL cardinal directions for exploration (WFC will filter passability)
    # Connections are determined by terrain, not AI suggestions
    for direction in DIRECTION_OFFSETS:
        dx, dy = DIRECTION_OFFSETS[direction]
        coord_queue.append((starting_location.name, 0 + dx, 0 + dy, direction, None))

    # Generate connected locations up to initial_size
    generated_count = 1
    attempts = 0
    max_attempts = initial_size * 3  # Prevent infinite loops

    while generated_count < initial_size and coord_queue and attempts < max_attempts:
        attempts += 1

        # Get next position to generate
        source_name, target_x, target_y, direction, suggested_name = coord_queue.pop(0)

        # Skip if position already occupied
        if grid.get_by_coordinates(target_x, target_y) is not None:
            continue

        # Skip if name already exists
        if suggested_name in grid:
            continue

        # Note: direction is always in DIRECTION_OFFSETS because we filter
        # at lines 125 and 178 when adding to the queue

        try:
            # Generate new location
            logger.info(f"Generating location at ({target_x}, {target_y}) from {source_name}")
            location_data = ai_service.generate_location(
                theme=theme,
                context_locations=list(grid.keys()),
                source_location=source_name,
                direction=direction
            )

            # Generate ASCII art for the new location
            new_ascii_art = _generate_location_ascii_art(
                ai_service=ai_service,
                location_name=location_data["name"],
                location_description=location_data["description"],
                location_category=location_data.get("category"),
                theme=theme
            )

            # Infer hierarchy fields from category
            new_category = location_data.get("category")
            new_is_overworld, new_is_safe_zone = _infer_hierarchy_from_category(new_category)

            # Create location (no connections - navigation is coordinate-based)
            new_location = Location(
                name=location_data["name"],
                description=location_data["description"],
                category=new_category,
                ascii_art=new_ascii_art,
                is_overworld=new_is_overworld,
                is_safe_zone=new_is_safe_zone
            )

            # Add AI-generated NPCs to the new location
            location_npcs = _create_npcs_from_data(location_data.get("npcs", []))
            for npc in location_npcs:
                new_location.npcs.append(npc)

            # Add to grid if name is unique (WorldGrid handles connections)
            if new_location.name not in grid:
                grid.add_location(new_location, target_x, target_y)
                generated_count += 1

                # Queue all cardinal directions from new location (WFC handles terrain passability)
                opposite = get_opposite_direction(direction)
                for new_dir in DIRECTION_OFFSETS:
                    if new_dir != opposite:  # Skip back-connection direction
                        dx, dy = DIRECTION_OFFSETS[new_dir]
                        coord_queue.append((new_location.name, target_x + dx, target_y + dy, new_dir, None))
            else:
                logger.debug(f"Duplicate location name generated: {new_location.name}")

        except Exception as e:
            logger.warning(f"Failed to generate location: {e}")
            continue

    logger.info(f"Generated world with {len(grid)} locations")

    # Note: No need to add dangling exits - coordinate-based navigation
    # allows movement to any adjacent coordinate (frontier exits are implicit)

    # Get the actual starting location name (first generated location)
    actual_starting_location = starting_location.name

    return (grid.as_dict(), actual_starting_location)


def expand_world(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str,
    target_coords: Optional[tuple[int, int]] = None,
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
    terrain_type: Optional[str] = None
) -> dict[str, Location]:
    """Expand world by generating a new location.

    Args:
        world: Existing world dictionary
        ai_service: AIService instance
        from_location: Source location name
        direction: Direction to expand in
        theme: World theme
        target_coords: Optional target coordinates for the new location.
                       If provided, the new location will be placed at these
                       coordinates. Otherwise, coordinates are calculated from
                       the source location.
        world_context: Optional Layer 1 context for layered generation
        region_context: Optional Layer 2 context for layered generation
        terrain_type: Optional terrain type (e.g., "desert", "forest") for coherent generation

    Returns:
        Updated world dictionary (same object, modified in place)

    Raises:
        ValueError: If source location not found or direction invalid
        AIServiceError: If generation fails
    """
    # Validate inputs
    if from_location not in world:
        raise ValueError(f"Location '{from_location}' not found in world")

    if direction not in Location.VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid direction '{direction}'. Must be one of: "
            f"{', '.join(sorted(Location.VALID_DIRECTIONS))}"
        )

    # Generate new location - use layered approach if contexts provided
    logger.info(f"Expanding world: {direction} from {from_location}")
    if world_context is not None and region_context is not None:
        # Gather neighboring locations for spatial coherence
        neighboring_locations: list[dict] = []
        if target_coords is not None:
            for dir_name, (dx, dy) in DIRECTION_OFFSETS.items():
                neighbor_coords = (target_coords[0] + dx, target_coords[1] + dy)
                for loc in world.values():
                    if loc.coordinates == neighbor_coords:
                        neighboring_locations.append({
                            "name": loc.name,
                            "direction": dir_name
                        })
                        break

        # Use layered generation (Layer 3 for location, Layer 4 for NPCs)
        location_data = ai_service.generate_location_with_context(
            world_context=world_context,
            region_context=region_context,
            source_location=from_location,
            direction=direction,
            terrain_type=terrain_type,
            neighboring_locations=neighboring_locations if neighboring_locations else None
        )
        # Generate NPCs separately (Layer 4) - only for named locations
        # Unnamed locations (is_named=False) don't spawn NPCs - they're terrain filler
        is_named = location_data.get("is_named", True)  # Default True for backward compat
        if is_named:
            npcs_data = ai_service.generate_npcs_for_location(
                world_context=world_context,
                location_name=location_data["name"],
                location_description=location_data["description"],
                location_category=location_data.get("category")
            )
            location_data["npcs"] = npcs_data
        else:
            location_data["npcs"] = []
    else:
        # Use original generation
        location_data = ai_service.generate_location(
            theme=theme,
            context_locations=list(world.keys()),
            source_location=from_location,
            direction=direction
        )

    # Generate ASCII art for the new location
    new_ascii_art = _generate_location_ascii_art(
        ai_service=ai_service,
        location_name=location_data["name"],
        location_description=location_data["description"],
        location_category=location_data.get("category"),
        theme=theme
    )

    # Determine coordinates for the new location
    source_loc = world[from_location]
    if target_coords is not None:
        # Use explicitly provided target coordinates
        new_coordinates = target_coords
    elif source_loc.coordinates is not None and direction in DIRECTION_OFFSETS:
        # Calculate from source location
        dx, dy = DIRECTION_OFFSETS[direction]
        new_coordinates = (source_loc.coordinates[0] + dx, source_loc.coordinates[1] + dy)
    else:
        new_coordinates = None

    # Infer hierarchy fields from category
    new_category = location_data.get("category")
    new_is_overworld, new_is_safe_zone = _infer_hierarchy_from_category(new_category)

    # Create new location with coordinates
    # Note: No connections field - navigation is coordinate-based
    new_location = Location(
        name=location_data["name"],
        description=location_data["description"],
        coordinates=new_coordinates,
        category=new_category,
        ascii_art=new_ascii_art,
        is_overworld=new_is_overworld,
        is_safe_zone=new_is_safe_zone
    )

    # Add AI-generated NPCs to the new location
    location_npcs = _create_npcs_from_data(
        location_data.get("npcs", []),
        terrain_type=terrain_type,
    )
    for npc in location_npcs:
        new_location.npcs.append(npc)

    # Add hidden secrets to named locations with appropriate categories
    if new_category in SECRET_CATEGORIES:
        secrets = _generate_secrets_for_location(new_category, distance=0)
        new_location.hidden_secrets.extend(secrets)

    # Add to world
    world[new_location.name] = new_location

    # Note: No connections needed - navigation is coordinate-based via WorldGrid

    logger.info(f"Added location '{new_location.name}' to world")
    return world


def expand_area(
    world: dict[str, Location],
    ai_service: AIService,
    from_location: str,
    direction: str,
    theme: str,
    target_coords: tuple[int, int],
    size: int = 5,
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None,
    terrain_type: Optional[str] = None,
    category_hint: Optional[str] = None,
) -> dict[str, Location]:
    """Expand world by generating an entire thematic area (4-7 locations).

    This function generates a cluster of connected locations at the target
    coordinates, placing them on the grid and connecting them to the source
    location.

    Args:
        world: Existing world dictionary
        ai_service: AIService instance with generate_area capability
        from_location: Source location name (where player is coming from)
        direction: Direction of expansion from source
        theme: World theme for generation
        target_coords: Coordinates where the entry location should be placed
        size: Target number of locations in the area (4-7, default 5)
        world_context: Optional Layer 1 context for layered generation
        region_context: Optional Layer 2 context for layered generation
                       (Note: area generation currently uses generate_area which
                       doesn't support layered contexts - contexts are passed
                       through to expand_world fallback)
        terrain_type: Optional terrain type (e.g., "desert", "forest") for coherent generation
        category_hint: Optional category hint from clustering (e.g., "village", "dungeon")

    Returns:
        Updated world dictionary (same object, modified in place)

    Raises:
        ValueError: If source location not found or direction invalid
        AIServiceError: If generation fails
    """
    # Validate inputs
    if from_location not in world:
        raise ValueError(f"Location '{from_location}' not found in world")

    if direction not in Location.VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid direction '{direction}'. Must be one of: "
            f"{', '.join(sorted(Location.VALID_DIRECTIONS))}"
        )

    # Generate area sub-theme hint based on source location and category_hint
    # Category hint from clustering biases toward similar location types
    import random

    # Category-specific sub-theme hints for clustering
    category_sub_themes = {
        "village": ["farming village", "fishing hamlet", "market town", "rural settlement"],
        "town": ["trading post", "crossroads town", "fortified settlement", "merchant hub"],
        "city": ["great city", "ancient metropolis", "walled city", "capital district"],
        "dungeon": ["dark dungeon", "underground complex", "ancient crypt", "forgotten prison"],
        "cave": ["deep cavern", "underground network", "crystal cave", "beast lair"],
        "ruins": ["ancient ruins", "fallen temple", "forgotten citadel", "crumbling fortress"],
        "temple": ["sacred temple", "divine sanctuary", "holy shrine", "pilgrimage site"],
        "shrine": ["forest shrine", "roadside shrine", "spirit altar", "sacred grove"],
        "monastery": ["mountain monastery", "secluded abbey", "order's sanctuary", "hermit refuge"],
    }

    if category_hint and category_hint in category_sub_themes:
        sub_theme_hints = category_sub_themes[category_hint]
    else:
        sub_theme_hints = [
            "mystical forest", "ancient ruins", "haunted grounds",
            "mountain pass", "coastal region", "underground cavern",
            "enchanted garden", "abandoned settlement", "wild frontier"
        ]
    sub_theme = random.choice(sub_theme_hints)

    # Generate the area
    logger.info(f"Expanding area: {direction} from {from_location} with theme '{sub_theme}'")

    if world_context is not None and region_context is not None:
        # Use layered generation for coherent areas
        area_data = ai_service.generate_area_with_context(
            world_context=world_context,
            region_context=region_context,
            entry_direction=direction,
            size=size,
            terrain_type=terrain_type
        )
    else:
        # Fall back to monolithic generation
        area_data = ai_service.generate_area(
            theme=theme,
            sub_theme_hint=sub_theme,
            entry_direction=direction,
            context_locations=list(world.keys()),
            size=size
        )

    if not area_data:
        logger.debug("No area data generated, falling back to single location")
        return expand_world(
            world=world,
            ai_service=ai_service,
            from_location=from_location,
            direction=direction,
            theme=theme,
            target_coords=target_coords,
            world_context=world_context,
            region_context=region_context,
            terrain_type=terrain_type
        )

    # Place area locations on the grid
    opposite = get_opposite_direction(direction)
    entry_name = None
    placed_locations = {}
    all_keys_to_place = []  # Track keys for locked door puzzles

    # First pass: create Location objects and calculate absolute coordinates
    for loc_data in area_data:
        # Support both 2D and 3D relative coordinates
        rel_coords = loc_data["relative_coords"]
        if len(rel_coords) == 2:
            rel_x, rel_y = rel_coords
            rel_z = 0
        else:
            rel_x, rel_y, rel_z = rel_coords

        abs_x = target_coords[0] + rel_x
        abs_y = target_coords[1] + rel_y

        # Skip if coordinates already occupied (only check for entry locations at z=0)
        if rel_z == 0:
            existing = None
            for loc in world.values():
                if loc.coordinates == (abs_x, abs_y):
                    existing = loc
                    break

            if existing is not None:
                logger.debug(
                    f"Skipping {loc_data['name']}: coordinates ({abs_x}, {abs_y}) "
                    f"already occupied by {existing.name}"
                )
                continue

        # Skip if name already exists
        if loc_data["name"] in world:
            logger.debug(f"Skipping duplicate location name: {loc_data['name']}")
            continue

        # Generate ASCII art using fallback (to avoid extra API calls for area locations)
        loc_ascii_art = get_fallback_location_ascii_art(
            category=loc_data.get("category"),
            location_name=loc_data["name"]
        )

        # Infer hierarchy fields from category
        loc_category = loc_data.get("category")
        _, loc_is_safe_zone = _infer_hierarchy_from_category(loc_category)

        # Determine if this is the entry location (at relative 0,0,0)
        is_entry = (rel_x == 0 and rel_y == 0 and rel_z == 0)

        # Entry location is overworld, sub-locations are not
        loc_is_overworld = is_entry

        # Create the location with hierarchy fields
        # Note: No connections field - navigation is coordinate-based via SubGrid
        new_loc = Location(
            name=loc_data["name"],
            description=loc_data["description"],
            coordinates=(abs_x, abs_y),
            category=loc_category,
            ascii_art=loc_ascii_art,
            is_overworld=loc_is_overworld,
            is_safe_zone=loc_is_safe_zone
        )

        # Add AI-generated NPCs to the location - only for named locations
        # Unnamed locations (is_named=False) don't spawn NPCs - they're terrain filler
        if loc_data.get("is_named", True):
            location_npcs = _create_npcs_from_data(
                loc_data.get("npcs", []),
                terrain_type=terrain_type,
            )
            for npc in location_npcs:
                new_loc.npcs.append(npc)

        # Add hidden secrets to non-entry rooms
        if not is_entry:
            distance = abs(rel_x) + abs(rel_y)
            secrets = _generate_secrets_for_location(loc_category or "dungeon", distance, rel_z)
            new_loc.hidden_secrets.extend(secrets)

            # Add puzzles to non-entry rooms (Issue #23)
            puzzles, blocked, keys = _generate_puzzles_for_location(
                loc_category or "dungeon", distance, rel_z
            )
            new_loc.puzzles.extend(puzzles)
            new_loc.blocked_directions.extend(blocked)
            # Track keys with door distance for placement
            for key_name, key_cat in keys:
                all_keys_to_place.append((key_name, key_cat, distance))

        placed_locations[loc_data["name"]] = {
            "location": new_loc,
            "coords": (abs_x, abs_y),
            "relative_coords": (rel_x, rel_y, rel_z),
            "is_entry": is_entry
        }

        # Track entry location (at relative 0,0)
        if is_entry:
            entry_name = loc_data["name"]

    # If no entry location was placed, fall back to single location expansion
    if entry_name is None and placed_locations:
        # Use first placed location as entry
        entry_name = next(iter(placed_locations.keys()))
        # Mark first location as entry (overworld)
        placed_locations[entry_name]["location"].is_overworld = True
        placed_locations[entry_name]["is_entry"] = True
    elif not placed_locations:
        logger.debug("No locations could be placed, falling back to single location")
        return expand_world(
            world=world,
            ai_service=ai_service,
            from_location=from_location,
            direction=direction,
            theme=theme,
            target_coords=target_coords,
            world_context=world_context,
            region_context=region_context,
            terrain_type=terrain_type
        )

    # Set up hierarchy relationships between entry and sub-locations
    if entry_name is not None:
        entry_loc = placed_locations[entry_name]["location"]
        sub_location_names = []

        for name, data in placed_locations.items():
            if not data.get("is_entry", False):
                # This is a sub-location - set parent reference
                data["location"].parent_location = entry_name
                sub_location_names.append(name)

        # Set entry's sub_locations list and entry_point
        entry_loc.sub_locations = sub_location_names
        if sub_location_names:
            entry_loc.entry_point = sub_location_names[0]

    # Note: No second pass for connections needed - navigation is coordinate-based

    # Add locations to world - use SubGrid for sub-locations
    if entry_name is not None and len(placed_locations) > 1:
        entry_loc = placed_locations[entry_name]["location"]

        # Get appropriate bounds based on entry location category
        entry_category = entry_loc.category
        bounds = get_subgrid_bounds(entry_category)
        sub_grid = SubGrid(bounds=bounds, parent_name=entry_name)

        # Add sub-locations to SubGrid (not to world)
        first_subloc = True
        for name, data in placed_locations.items():
            if data.get("is_entry", False):
                continue  # Skip entry, it goes to world

            loc = data["location"]
            # Support both 2D and 3D relative coordinates
            rel_coords = data["relative_coords"]
            if len(rel_coords) == 2:
                rel_x, rel_y = rel_coords
                rel_z = 0
            else:
                rel_x, rel_y, rel_z = rel_coords

            # Check SubGrid bounds before adding (including z-bounds)
            if not sub_grid.is_within_bounds(rel_x, rel_y, rel_z):
                logger.debug(
                    f"Skipping {name}: coords ({rel_x}, {rel_y}, {rel_z}) outside SubGrid bounds "
                    f"{sub_grid.bounds}"
                )
                continue

            # Clear overworld coordinates (sub-locations get SubGrid coords)
            loc.coordinates = None

            # First sub-location is exit point (entry into the SubGrid)
            loc.is_exit_point = first_subloc
            first_subloc = False

            sub_grid.add_location(loc, rel_x, rel_y, rel_z)

        # Place boss in furthest room for dungeon-type areas (prefer lowest z-level)
        if entry_category in BOSS_CATEGORIES:
            boss_room_name = _find_furthest_room(placed_locations, prefer_lowest_z=True)
            if boss_room_name:
                boss_room = sub_grid.get_by_name(boss_room_name)
                if boss_room:
                    boss_room.boss_enemy = entry_category  # Category-based boss

        # Place treasures in non-entry, non-boss rooms
        _place_treasures(placed_locations, entry_category or "dungeon")

        # Place keys for locked door puzzles in earlier rooms (Issue #23)
        if all_keys_to_place:
            _place_keys_in_earlier_rooms(placed_locations, all_keys_to_place)

        # Attach sub_grid to entry
        entry_loc.sub_grid = sub_grid
        entry_loc.is_exit_point = True  # Can exit from entry back to overworld

        # Only add entry to world
        world[entry_name] = entry_loc
    else:
        # Single location or no entry - add all to world (legacy behavior)
        for name, data in placed_locations.items():
            world[name] = data["location"]

    # Note: No explicit connections needed - navigation is coordinate-based
    # The entry location at target_coords connects to source via coordinate adjacency

    logger.info(
        f"Added area with {len(placed_locations)} locations, "
        f"entry: '{entry_name}'"
    )
    return world


def create_world_with_fallback(
    ai_service: Optional[AIService] = None,
    theme: str = "fantasy"
) -> tuple[dict[str, Location], str]:
    """Create world with AI or raise exception.

    Note: This function is deprecated. Use create_ai_world directly
    and handle fallback in the caller.

    Args:
        ai_service: Optional AIService instance
        theme: World theme

    Returns:
        Tuple of (world, starting_location)

    Raises:
        ValueError: If ai_service is None
        AIServiceError: If generation fails
    """
    if ai_service is None:
        raise ValueError("AI service is required")

    logger.info("Attempting to create AI-generated world")
    return create_ai_world(ai_service, theme=theme)
