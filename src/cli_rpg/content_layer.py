"""ContentLayer mediator for procedural layout + AI content generation.

This module bridges procedural layout generators (RoomTemplate from
procedural_interiors.py) with AI content generation (ai_service.py) to
produce fully populated SubGrid instances with deterministic spatial
structure and AI-generated thematic content.

Architecture:
- ContentLayer.populate_subgrid(): Main entry point
- Transforms RoomTemplate → Location for each room
- Applies room-type-specific content (boss, treasure, puzzle, hazards)
- Supports AI content generation with graceful fallback
- Ensures determinism via seed parameter
"""

import logging
import random
from typing import Optional, TYPE_CHECKING

from cli_rpg.procedural_interiors import RoomTemplate, RoomType
from cli_rpg.models.location import Location
from cli_rpg.world_grid import SubGrid, get_subgrid_bounds

if TYPE_CHECKING:
    from cli_rpg.ai_service import AIService
    from cli_rpg.models.generation_context import GenerationContext


# Set up logging
logger = logging.getLogger(__name__)


# Fallback names by room type
FALLBACK_NAMES: dict[RoomType, list[str]] = {
    RoomType.ENTRY: ["Entrance Chamber", "Entry Hall", "Threshold", "Vestibule"],
    RoomType.CORRIDOR: ["Dark Corridor", "Narrow Passage", "Stone Hallway", "Winding Path"],
    RoomType.CHAMBER: ["Ancient Chamber", "Dusty Room", "Stone Chamber", "Silent Hall"],
    RoomType.BOSS_ROOM: ["Boss Lair", "Inner Sanctum", "Throne Room", "Final Chamber"],
    RoomType.TREASURE: ["Treasure Vault", "Hidden Cache", "Gilded Chamber", "Hoard Room"],
    RoomType.PUZZLE: ["Puzzle Room", "Trial Chamber", "Enigma Hall", "Test of Wits"],
}


# Fallback descriptions by room type and category
FALLBACK_DESCRIPTIONS: dict[RoomType, dict[str, str]] = {
    RoomType.ENTRY: {
        "dungeon": "The entrance to the dungeon. Dark passages stretch ahead.",
        "cave": "The cave mouth opens into darkness. Strange echoes surround you.",
        "ruins": "Crumbling stones mark the entrance to these ancient ruins.",
        "temple": "Sacred symbols adorn the threshold of this holy place.",
        "default": "The entrance to this place. Adventure awaits within.",
    },
    RoomType.CORRIDOR: {
        "dungeon": "A narrow passage with damp walls. Shadows dance at the edges of your vision.",
        "cave": "A rocky tunnel twists through the darkness. Water drips somewhere nearby.",
        "ruins": "A partially collapsed hallway. Rubble crunches underfoot.",
        "temple": "A processional corridor lined with faded murals.",
        "default": "A connecting passage leading deeper into the structure.",
    },
    RoomType.CHAMBER: {
        "dungeon": "A larger room with crumbling pillars. Something valuable might be hidden here.",
        "cave": "A cavern opens up around you. Stalactites hang from the ceiling.",
        "ruins": "An ancient chamber, its original purpose lost to time.",
        "temple": "A meditation chamber with worn prayer cushions.",
        "default": "A spacious room with signs of ancient habitation.",
    },
    RoomType.BOSS_ROOM: {
        "dungeon": "A massive chamber where something powerful lurks.",
        "cave": "A vast underground dome. The beast's lair awaits.",
        "ruins": "The heart of the ruins. An ancient guardian protects this place.",
        "temple": "The inner sanctum. A sacred guardian challenges all who enter.",
        "default": "A final chamber where danger awaits.",
    },
    RoomType.TREASURE: {
        "dungeon": "A hidden vault filled with the spoils of past adventurers.",
        "cave": "A glittering grotto where precious things have accumulated.",
        "ruins": "A treasure room protected by ancient wards.",
        "temple": "An offering chamber filled with sacred relics.",
        "default": "A chamber where valuable items have been stored.",
    },
    RoomType.PUZZLE: {
        "dungeon": "A room with strange mechanisms. A test of wit awaits.",
        "cave": "A chamber with peculiar rock formations. Something seems off.",
        "ruins": "An ancient trial chamber. The builders left puzzles for intruders.",
        "temple": "A room of trials. Only the worthy may pass.",
        "default": "A puzzle room designed to test intruders.",
    },
}


# Treasure loot tables per category (simplified from ai_world.py)
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
}


# Treasure chest names per category
TREASURE_CHEST_NAMES: dict[str, list[str]] = {
    "dungeon": ["Iron Chest", "Dusty Strongbox", "Forgotten Coffer"],
    "cave": ["Stone Chest", "Crystal Box", "Hidden Cache"],
    "ruins": ["Ancient Chest", "Ruined Coffer", "Gilded Box"],
    "temple": ["Sacred Chest", "Offering Box", "Blessed Container"],
}


class ContentLayer:
    """Mediator that bridges procedural layouts with AI content generation.

    Transforms RoomTemplate lists from procedural generators into fully
    populated SubGrid instances with thematic content.
    """

    def populate_subgrid(
        self,
        room_templates: list[RoomTemplate],
        parent_location: Location,
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
        seed: int,
    ) -> SubGrid:
        """Transform RoomTemplate list into populated SubGrid.

        Args:
            room_templates: List of RoomTemplate blueprints from procedural generator
            parent_location: The parent location (dungeon, cave, etc.)
            ai_service: Optional AI service for content generation
            generation_context: Optional context for AI generation
            seed: Random seed for deterministic generation

        Returns:
            SubGrid populated with Location instances
        """
        # Initialize RNG for deterministic generation
        rng = random.Random(seed)

        # Get bounds from parent category
        bounds = get_subgrid_bounds(parent_location.category)
        sub_grid = SubGrid(bounds=bounds, parent_name=parent_location.name)

        # Track placed locations for multi-pass processing
        placed_locations: dict[str, dict] = {}

        # First pass: Create locations from templates
        for template in room_templates:
            location = self._create_location_from_template(
                template=template,
                parent_location=parent_location,
                ai_service=ai_service,
                generation_context=generation_context,
                rng=rng,
            )

            x, y, z = template.coords

            # Skip if outside bounds
            if not sub_grid.is_within_bounds(x, y, z):
                logger.debug(f"Skipping {location.name}: outside bounds")
                continue

            sub_grid.add_location(location, x, y, z)
            placed_locations[location.name] = {
                "location": location,
                "template": template,
                "coords": template.coords,
            }

        return sub_grid

    def _create_location_from_template(
        self,
        template: RoomTemplate,
        parent_location: Location,
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
        rng: random.Random,
    ) -> Location:
        """Create a Location from a RoomTemplate.

        Args:
            template: The room template to transform
            parent_location: Parent location for context
            ai_service: Optional AI service for content
            generation_context: Optional context for AI
            rng: Random number generator for determinism

        Returns:
            Fully populated Location instance
        """
        category = parent_location.category or "dungeon"

        # Generate content (AI or fallback)
        name, description = self._generate_content(
            template=template,
            category=category,
            ai_service=ai_service,
            generation_context=generation_context,
            rng=rng,
        )

        # Create base location
        location = Location(
            name=name,
            description=description,
            category=category,
            is_exit_point=template.is_entry,
            is_overworld=False,  # Interior locations are not overworld
        )

        # Apply room-type-specific content
        self._apply_room_type_content(
            location=location,
            template=template,
            category=category,
            rng=rng,
        )

        # Transfer suggested hazards
        if template.suggested_hazards:
            location.hazards.extend(template.suggested_hazards)

        return location

    def _generate_content(
        self,
        template: RoomTemplate,
        category: str,
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
        rng: random.Random,
    ) -> tuple[str, str]:
        """Generate name and description for a room.

        Args:
            template: Room template for context
            category: Location category (dungeon, cave, etc.)
            ai_service: Optional AI service
            generation_context: Optional generation context
            rng: Random number generator

        Returns:
            Tuple of (name, description)
        """
        # Try AI generation if available
        if ai_service is not None:
            try:
                content = ai_service.generate_room_content(
                    room_type=template.room_type.value,
                    category=category,
                    connections=template.connections,
                    is_entry=template.is_entry,
                    context=generation_context,
                )
                if content and "name" in content and "description" in content:
                    return content["name"], content["description"]
            except Exception as e:
                logger.debug(f"AI room content generation failed: {e}")

        # Fallback to procedural names
        return self._generate_fallback_content(template, category, rng)

    def _generate_fallback_content(
        self,
        template: RoomTemplate,
        category: str,
        rng: random.Random,
    ) -> tuple[str, str]:
        """Generate fallback name and description.

        Args:
            template: Room template
            category: Location category
            rng: Random number generator

        Returns:
            Tuple of (name, description)
        """
        # Get name from room type
        names = FALLBACK_NAMES.get(template.room_type, ["Unknown Chamber"])
        name = rng.choice(names)

        # Get description from room type + category
        desc_by_category = FALLBACK_DESCRIPTIONS.get(
            template.room_type, {"default": "A mysterious room."}
        )
        description = desc_by_category.get(category, desc_by_category.get("default", ""))

        return name, description

    def _apply_room_type_content(
        self,
        location: Location,
        template: RoomTemplate,
        category: str,
        rng: random.Random,
    ) -> None:
        """Apply room-type-specific content to location.

        Args:
            location: Location to modify
            template: Room template
            category: Location category
            rng: Random number generator
        """
        if template.room_type == RoomType.BOSS_ROOM:
            # Set boss enemy based on category
            location.boss_enemy = category

        elif template.room_type == RoomType.TREASURE:
            # Create treasure chest
            treasure = self._create_treasure_chest(category, rng)
            location.treasures.append(treasure)

        elif template.room_type == RoomType.PUZZLE:
            # Puzzles are handled separately via existing puzzle generation
            # Just ensure the room is marked appropriately
            pass

    def _create_treasure_chest(
        self,
        category: str,
        rng: random.Random,
    ) -> dict:
        """Create a treasure chest with thematic items.

        Args:
            category: Location category for theme
            rng: Random number generator

        Returns:
            Treasure dict matching Location.treasures schema
        """
        # Get thematic chest name
        chest_names = TREASURE_CHEST_NAMES.get(category, ["Treasure Chest"])
        chest_name = rng.choice(chest_names)

        # Get thematic loot
        loot_table = TREASURE_LOOT_TABLES.get(category, TREASURE_LOOT_TABLES.get("dungeon", []))
        num_items = rng.randint(1, min(2, len(loot_table)))
        items = rng.sample(loot_table, num_items)

        # Generate description
        descriptions = {
            "dungeon": "An old chest left behind by previous adventurers.",
            "cave": "A chest hidden among the rocks.",
            "ruins": "An ancient container from a forgotten era.",
            "temple": "A sacred chest placed as an offering.",
        }
        description = descriptions.get(category, "A mysterious treasure chest.")

        return {
            "name": chest_name,
            "description": description,
            "locked": True,
            "difficulty": rng.randint(1, 3),
            "opened": False,
            "items": [item.copy() for item in items],
            "requires_key": None,
        }
