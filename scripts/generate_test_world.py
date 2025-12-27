#!/usr/bin/env python3
"""Generate pre-built test world fixture for demo mode and testing.

This script creates a comprehensive test world JSON containing:
- A level 3 Warrior character with balanced stats
- 5 named overworld locations forming a simple map
- NPCs with shops and quests
- A cave SubGrid with exit point and boss
- Default factions

Usage:
    python scripts/generate_test_world.py

The output is written to tests/fixtures/test_world.json
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from cli_rpg.models.character import Character, CharacterClass, FightingStance
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType, QuestDifficulty
from cli_rpg.models.faction import Faction
from cli_rpg.models.inventory import Inventory
from cli_rpg.models.game_time import GameTime
from cli_rpg.models.weather import Weather
from cli_rpg.world_grid import SubGrid
from cli_rpg.game_state import GameState


def create_test_items() -> dict[str, Item]:
    """Create items for the test world."""
    return {
        "health_potion": Item(
            name="Health Potion",
            description="Restores 30 health points",
            item_type=ItemType.CONSUMABLE,
            heal_amount=30,
        ),
        "mana_potion": Item(
            name="Mana Potion",
            description="Restores 25 mana points",
            item_type=ItemType.CONSUMABLE,
            mana_restore=25,
        ),
        "iron_sword": Item(
            name="Iron Sword",
            description="A sturdy iron blade",
            item_type=ItemType.WEAPON,
            damage_bonus=8,
        ),
        "steel_sword": Item(
            name="Steel Sword",
            description="A well-forged steel blade",
            item_type=ItemType.WEAPON,
            damage_bonus=12,
        ),
        "leather_armor": Item(
            name="Leather Armor",
            description="Basic leather protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3,
        ),
        "chainmail": Item(
            name="Chainmail",
            description="Interlocking metal rings",
            item_type=ItemType.ARMOR,
            defense_bonus=6,
        ),
        "torch": Item(
            name="Torch",
            description="A simple torch that illuminates dark places",
            item_type=ItemType.MISC,
            light_duration=10,
        ),
        "ancient_key": Item(
            name="Ancient Key",
            description="A mysterious key from the old kingdom",
            item_type=ItemType.MISC,
        ),
    }


def create_test_character() -> Character:
    """Create a level 3 Warrior character for testing."""
    char = Character(
        name="Demo Hero",
        strength=14,
        dexterity=12,
        intelligence=10,
        charisma=10,
        perception=10,
        luck=10,
        character_class=CharacterClass.WARRIOR,
    )
    # Level up to 3
    char.level = 3
    char.xp = 250
    char.max_health = 130  # Higher from leveling
    char.health = 130
    char.gold = 100

    # Add some items to inventory
    items = create_test_items()
    char.inventory.add_item(items["health_potion"])
    char.inventory.add_item(items["health_potion"])
    char.inventory.add_item(items["iron_sword"])
    char.inventory.add_item(items["leather_armor"])
    char.inventory.add_item(items["torch"])

    # Equip weapon and armor
    char.inventory.equip(items["iron_sword"])
    char.inventory.equip(items["leather_armor"])

    return char


def create_test_quest() -> Quest:
    """Create a sample quest for testing."""
    return Quest(
        name="Clear the Cave",
        description="A merchant needs help clearing dangerous creatures from a nearby cave.",
        objective_type=ObjectiveType.KILL,
        target="Cave Spider",
        target_count=3,
        current_count=1,  # Partially completed
        xp_reward=150,
        gold_reward=50,
        status=QuestStatus.ACTIVE,
        difficulty=QuestDifficulty.NORMAL,
        quest_giver="Merchant Marcus",
    )


def create_merchant_shop() -> Shop:
    """Create a merchant shop with common items."""
    items = create_test_items()
    return Shop(
        name="Marcus's Goods",
        inventory=[
            ShopItem(item=items["health_potion"], buy_price=25),
            ShopItem(item=items["mana_potion"], buy_price=30),
            ShopItem(item=items["steel_sword"], buy_price=150),
            ShopItem(item=items["chainmail"], buy_price=200),
            ShopItem(item=items["torch"], buy_price=5),
        ],
    )


def create_merchant_npc() -> NPC:
    """Create the merchant NPC with shop."""
    return NPC(
        name="Merchant Marcus",
        description="A portly merchant with a friendly smile.",
        dialogue="Welcome to my shop! I have the finest goods in town.",
        is_merchant=True,
        shop=create_merchant_shop(),
        is_quest_giver=True,
        offered_quests=[create_test_quest()],
        greetings=[
            "Ah, a customer! Looking for supplies?",
            "Welcome back! What can I get you today?",
        ],
    )


def create_quest_giver_npc() -> NPC:
    """Create a quest-giver NPC (village elder)."""
    exploration_quest = Quest(
        name="Scout the Ruins",
        description="The elder needs someone to scout the abandoned ruins to the east.",
        objective_type=ObjectiveType.EXPLORE,
        target="Abandoned Ruins",
        target_count=1,
        xp_reward=100,
        gold_reward=30,
        status=QuestStatus.AVAILABLE,
        difficulty=QuestDifficulty.EASY,
        quest_giver="Elder Theron",
    )

    return NPC(
        name="Elder Theron",
        description="A wise old man who leads the village.",
        dialogue="Greetings, traveler. Our village could use your help.",
        is_quest_giver=True,
        offered_quests=[exploration_quest],
        greetings=[
            "Ah, you've come. I sensed you would.",
            "The village is grateful for heroes like you.",
        ],
    )


def create_cave_subgrid(parent_name: str) -> SubGrid:
    """Create a 3x3 cave SubGrid with boss and exit point."""
    from cli_rpg.world_grid import get_subgrid_bounds

    bounds = get_subgrid_bounds("cave")
    sub_grid = SubGrid(bounds=bounds, parent_name=parent_name)

    # Create cave entrance (exit point at 0,0,0)
    entrance = Location(
        name="Cave Entrance",
        description="The entrance to a dark cave. Daylight filters in from behind you.",
        category="cave",
        is_exit_point=True,
    )
    sub_grid.add_location(entrance, 0, 0, 0)

    # Create dark passage (0,1,0)
    passage = Location(
        name="Dark Passage",
        description="A narrow tunnel leading deeper into the cave. Spider webs cover the walls.",
        category="cave",
    )
    sub_grid.add_location(passage, 0, 1, 0)

    # Create spider den with boss (-1,1,0)
    den = Location(
        name="Spider Den",
        description="A large cavern filled with thick webbing. Something large lurks in the shadows.",
        category="cave",
        boss_enemy="Giant Spider",
        treasures=[
            {"item": "Ancient Key", "locked": False, "opened": False}
        ],
    )
    sub_grid.add_location(den, -1, 1, 0)

    # Create treasure room (1,1,0)
    treasure = Location(
        name="Hidden Alcove",
        description="A small alcove with glittering treasures.",
        category="cave",
        treasures=[
            {"item": "Health Potion", "locked": True, "opened": False}
        ],
    )
    sub_grid.add_location(treasure, 1, 1, 0)

    return sub_grid


def create_test_world() -> dict[str, Location]:
    """Create the test world with 5 locations."""
    world = {}

    # 1. Starting Village at (0,0) - safe zone with NPCs
    village = Location(
        name="Peaceful Village",
        description="A small village nestled in a verdant valley. Smoke rises from cozy cottages.",
        coordinates=(0, 0),
        category="town",
        terrain="plains",
        is_named=True,
        is_overworld=True,
        is_safe_zone=True,
        npcs=[create_merchant_npc(), create_quest_giver_npc()],
    )
    world[village.name] = village

    # 2. Forest Path at (0,1) - wilderness area north
    forest = Location(
        name="Whispering Forest",
        description="Tall trees form a dense canopy overhead. The path winds through ancient oaks.",
        coordinates=(0, 1),
        category="forest",
        terrain="forest",
        is_named=True,
        is_overworld=True,
        details="The forest floor is carpeted with fallen leaves. Bird calls echo through the trees.",
    )
    world[forest.name] = forest

    # 3. Cave Entrance at (1,0) - enterable location east
    cave = Location(
        name="Dark Cave",
        description="A gaping cave mouth opens in the hillside. Cold air flows from within.",
        coordinates=(1, 0),
        category="cave",
        terrain="hills",
        is_named=True,
        is_overworld=True,
        entry_point="Cave Entrance",
    )
    # Add SubGrid
    cave.sub_grid = create_cave_subgrid(cave.name)
    world[cave.name] = cave

    # 4. Abandoned Ruins at (-1,0) - exploration target west
    ruins = Location(
        name="Abandoned Ruins",
        description="Crumbling stone walls mark what was once a grand structure.",
        coordinates=(-1, 0),
        category="ruins",
        terrain="plains",
        is_named=True,
        is_overworld=True,
        details="Moss covers the ancient stones. Fragments of carved inscriptions remain.",
        secrets="Hidden beneath a loose flagstone, you find an old chest.",
        hidden_secrets=[
            {"description": "A hidden chest beneath a flagstone", "threshold": 12, "discovered": False}
        ],
    )
    world[ruins.name] = ruins

    # 5. Crossroads at (0,-1) - junction point south
    crossroads = Location(
        name="Southern Crossroads",
        description="A weathered signpost marks the intersection of several roads.",
        coordinates=(0, -1),
        category="wilderness",
        terrain="plains",
        is_named=True,
        is_overworld=True,
    )
    world[crossroads.name] = crossroads

    return world


def create_default_factions() -> list[Faction]:
    """Create default factions matching world.get_default_factions()."""
    return [
        Faction(
            name="Town Guard",
            description="The local militia protecting settlements",
        ),
        Faction(
            name="Merchant Guild",
            description="Traders and shopkeepers",
        ),
        Faction(
            name="Thieves Guild",
            description="A shadowy network of rogues",
        ),
    ]


def create_test_game_state() -> GameState:
    """Create a complete GameState for testing."""
    character = create_test_character()
    world = create_test_world()

    # Add the quest to the character
    character.quests.append(create_test_quest())

    game_state = GameState(
        character=character,
        world=world,
        starting_location="Peaceful Village",
        theme="fantasy",
    )

    # Set up game time (8 AM on day 1)
    game_state.game_time = GameTime(hour=8, total_hours=8)

    # Set up weather (clear)
    game_state.weather = Weather(condition="clear")

    # Set up factions
    game_state.factions = create_default_factions()

    # Initialize visibility (mark starting area as seen)
    game_state.seen_tiles.add((0, 0))
    game_state.seen_tiles.add((0, 1))
    game_state.seen_tiles.add((1, 0))
    game_state.seen_tiles.add((-1, 0))
    game_state.seen_tiles.add((0, -1))

    return game_state


def main():
    """Generate and save the test world fixture."""
    output_path = project_root / "tests" / "fixtures" / "test_world.json"

    print("Generating test world...")
    game_state = create_test_game_state()

    print("Serializing to JSON...")
    data = game_state.to_dict()

    print(f"Writing to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    # Calculate size
    size_kb = output_path.stat().st_size / 1024
    print(f"Done! Generated {size_kb:.1f}KB fixture.")

    # Summary
    print("\nTest World Summary:")
    print(f"  Character: {data['character']['name']} (Level {data['character']['level']})")
    print(f"  Locations: {len(data['world'])}")
    print(f"  Factions: {len(data['factions'])}")
    print(f"  Starting Location: {data['current_location']}")


if __name__ == "__main__":
    main()
