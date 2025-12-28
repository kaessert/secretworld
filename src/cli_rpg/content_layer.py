"""ContentLayer mediator for procedural layout + AI content generation.

This module bridges procedural layout generators (RoomTemplate from
procedural_interiors.py) with AI content generation (ai_service.py) to
produce fully populated SubGrid instances with deterministic spatial
structure and AI-generated thematic content.

Architecture:
- ContentLayer.populate_subgrid(): Main entry point
- ContentLayer.generate_quest_from_template(): Quest generation from templates
- Transforms RoomTemplate → Location for each room
- Applies room-type-specific content (boss, treasure, puzzle, hazards)
- Supports AI content generation with graceful fallback via FallbackContentProvider
- Ensures determinism via seed parameter
"""

import logging
import random
from typing import Optional, TYPE_CHECKING

from cli_rpg.procedural_interiors import RoomTemplate, RoomType
from cli_rpg.models.location import Location
from cli_rpg.models.quest import Quest, QuestStatus
from cli_rpg.world_grid import SubGrid, get_subgrid_bounds
from cli_rpg.fallback_content import FallbackContentProvider
from cli_rpg.procedural_quests import (
    QuestTemplate,
    QuestTemplateType,
    scale_quest_difficulty,
    _generate_fallback_quest_content,
    generate_branches_for_template,
)

if TYPE_CHECKING:
    from cli_rpg.ai_service import AIService
    from cli_rpg.models.generation_context import GenerationContext


# Set up logging
logger = logging.getLogger(__name__)


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

        # Track used names to avoid duplicates
        used_names: set[str] = set()

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

            # Disambiguate duplicate names by appending coordinates
            original_name = location.name
            if original_name in used_names:
                # Append coordinates to make name unique
                location.name = f"{original_name} ({x},{y},{z})"
            used_names.add(location.name)

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

        # Create base location with explicit exits from procedural generation
        location = Location(
            name=name,
            description=description,
            category=category,
            is_exit_point=template.is_entry,
            is_overworld=False,  # Interior locations are not overworld
            allowed_exits=template.connections.copy(),  # Transfer procedural connections
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
        """Generate fallback name and description using FallbackContentProvider.

        Args:
            template: Room template
            category: Location category
            rng: Random number generator (used to generate seed for provider)

        Returns:
            Tuple of (name, description)
        """
        # Create a FallbackContentProvider with a seed derived from the RNG
        # This ensures determinism while delegating to the centralized provider
        provider = FallbackContentProvider(seed=rng.randint(0, 2**31))
        content = provider.get_room_content(template.room_type, category)
        return content["name"], content["description"]

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

    def generate_npc_content(
        self,
        role: str,
        category: str,
        coords: tuple[int, int, int],
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
        rng: random.Random,
    ) -> dict:
        """Generate NPC name, description, and dialogue.

        Tries AI generation first, falls back to FallbackContentProvider on failure.

        Args:
            role: NPC role (merchant, guard, quest_giver, villager, etc.)
            category: Location category for context
            coords: 3D coordinates for deterministic seeding
            ai_service: Optional AI service for content generation
            generation_context: Optional context for AI generation
            rng: Random number generator for determinism

        Returns:
            Dict with 'name', 'description', 'dialogue' keys
        """
        # Try AI generation if available
        if ai_service is not None:
            try:
                # Check if ai_service has generate_npc_content method
                if hasattr(ai_service, "generate_npc_content"):
                    content = ai_service.generate_npc_content(
                        role=role,
                        category=category,
                        context=generation_context,
                    )
                    if (
                        content
                        and "name" in content
                        and "description" in content
                        and "dialogue" in content
                    ):
                        return content
            except Exception as e:
                logger.debug(f"AI NPC content generation failed: {e}")

        # Fallback to FallbackContentProvider
        provider = FallbackContentProvider(seed=rng.randint(0, 2**31))
        return provider.get_npc_content(role, category)

    def generate_quest_content(
        self,
        category: str,
        coords: tuple[int, int, int],
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
        rng: random.Random,
        npc_name: str = "",
        valid_locations: Optional[set[str]] = None,
        valid_npcs: Optional[set[str]] = None,
    ) -> Optional[dict]:
        """Generate quest name, description, and objectives.

        Tries AI generation first, falls back to FallbackContentProvider on failure.

        Args:
            category: Location category for thematic quests
            coords: 3D coordinates for deterministic seeding
            ai_service: Optional AI service for content generation
            generation_context: Optional context for AI generation
            rng: Random number generator for determinism
            npc_name: Name of quest-giving NPC for context
            valid_locations: Optional set of valid location names for EXPLORE quests
            valid_npcs: Optional set of valid NPC names for TALK quests

        Returns:
            Dict with 'name', 'description', 'objective_type', 'target' keys,
            or None if generation fails
        """
        # Try AI generation if available
        if ai_service is not None and generation_context is not None:
            try:
                world_context = generation_context.world
                region_context = generation_context.region
                theme = world_context.theme if world_context else "fantasy"

                quest_data = ai_service.generate_quest(
                    theme=theme,
                    npc_name=npc_name,
                    player_level=1,
                    location_name="",
                    valid_locations=valid_locations,
                    valid_npcs=valid_npcs,
                    world_context=world_context,
                    region_context=region_context,
                )
                if quest_data:
                    return quest_data
            except Exception as e:
                logger.debug(f"AI quest generation failed: {e}")

        # Fallback to FallbackContentProvider
        provider = FallbackContentProvider(seed=rng.randint(0, 2**31))
        return provider.get_quest_content(category)

    def generate_quest_from_template(
        self,
        template: QuestTemplate,
        category: str,
        player_level: int,
        danger_level: int,
        npc_name: str,
        coords: tuple[int, int, int],
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
        seed: int,
    ) -> Optional[Quest]:
        """Generate a Quest from a QuestTemplate with AI or fallback content.

        Uses scale_quest_difficulty() to determine scaled values, then populates
        narrative content (name, description, target) via AI or fallback.

        Args:
            template: The QuestTemplate blueprint to populate.
            category: Location category for thematic content.
            player_level: Player's level for difficulty scaling.
            danger_level: Region danger level (1-3 typically).
            npc_name: Name of quest-giving NPC for context.
            coords: 3D coordinates for cache keying.
            ai_service: Optional AI service for content generation.
            generation_context: Optional context for AI generation.
            seed: Random seed for deterministic generation.

        Returns:
            Fully populated Quest object, or None if generation fails.
        """
        rng = random.Random(seed)

        # Calculate scaled difficulty values
        scaled = scale_quest_difficulty(template, player_level, danger_level)

        # Try AI content generation first
        content = self._generate_quest_template_content_ai(
            template=template,
            category=category,
            player_level=player_level,
            npc_name=npc_name,
            ai_service=ai_service,
            generation_context=generation_context,
        )

        # Fall back to template-based content if AI unavailable
        if content is None:
            content = _generate_fallback_quest_content(
                template.template_type,
                category,
                rng.randint(0, 2**31),
            )

        if content is None:
            logger.debug("Failed to generate quest content from template")
            return None

        # Generate alternative branches for this quest type
        branches = generate_branches_for_template(
            template_type=template.template_type,
            target=content["target"],
            category=category,
            seed=rng.randint(0, 2**31),
        )

        try:
            quest = Quest(
                name=content["name"],
                description=content["description"],
                objective_type=template.objective_type,
                target=content["target"],
                target_count=scaled["target_count"],
                gold_reward=scaled["gold_reward"],
                xp_reward=scaled["xp_reward"],
                difficulty=scaled["difficulty"],
                recommended_level=scaled["recommended_level"],
                quest_giver=npc_name if npc_name else None,
                chain_position=template.chain_position,
                status=QuestStatus.AVAILABLE,
                alternative_branches=branches,
            )
            return quest
        except (ValueError, KeyError) as e:
            logger.debug(f"Failed to create Quest from template content: {e}")
            return None

    def _generate_quest_template_content_ai(
        self,
        template: QuestTemplate,
        category: str,
        player_level: int,
        npc_name: str,
        ai_service: Optional["AIService"],
        generation_context: Optional["GenerationContext"],
    ) -> Optional[dict]:
        """Try to generate quest content via AI service.

        Args:
            template: The QuestTemplate blueprint.
            category: Location category.
            player_level: Player's level.
            npc_name: Quest-giving NPC name.
            ai_service: AI service for content generation.
            generation_context: Context for AI generation.

        Returns:
            Dict with 'name', 'description', 'target' if successful, None otherwise.
        """
        if ai_service is None:
            return None

        try:
            # Check if ai_service has generate_quest_from_template method
            if hasattr(ai_service, "generate_quest_from_template"):
                content = ai_service.generate_quest_from_template(
                    template_type=template.template_type.value,
                    category=category,
                    player_level=player_level,
                    npc_name=npc_name,
                    context=generation_context,
                )
                if content and all(k in content for k in ["name", "description", "target"]):
                    return content

            # Fallback to generate_quest if available
            if hasattr(ai_service, "generate_quest") and generation_context:
                world_context = generation_context.world if generation_context else None
                region_context = generation_context.region if generation_context else None
                theme = world_context.theme if world_context else "fantasy"

                quest_data = ai_service.generate_quest(
                    theme=theme,
                    npc_name=npc_name,
                    player_level=player_level,
                    location_name=category,
                    world_context=world_context,
                    region_context=region_context,
                )
                if quest_data and "name" in quest_data:
                    # Map AI response to our expected format
                    return {
                        "name": quest_data.get("name", "A Quest"),
                        "description": quest_data.get("description", "Complete this task."),
                        "target": quest_data.get("target", "Target"),
                    }
        except Exception as e:
            logger.debug(f"AI quest template content generation failed: {e}")

        return None
