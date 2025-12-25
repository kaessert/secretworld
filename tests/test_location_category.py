"""Tests for the Location category field - Location Categories feature.

These tests verify the spec requirement:
Add a `category` field to locations enabling type-aware gameplay
(enemy spawning, shop inventory, ambient text).

Categories include: town, dungeon, wilderness, settlement, ruins, etc.
"""

import pytest
from cli_rpg.models.location import Location
from cli_rpg.combat import spawn_enemy


class TestLocationCategory:
    """Test Location category field functionality."""

    def test_location_category_field_exists(self):
        """Test that Location has a category field - spec: add category field."""
        location = Location(
            name="Dark Forest",
            description="A shadowy forest.",
            category="wilderness"
        )
        assert location.category == "wilderness"

    def test_location_category_defaults_to_none(self):
        """Test category defaults to None for backward compatibility - spec: Optional[str] = None."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        assert location.category is None

    def test_location_category_accepts_various_types(self):
        """Test category accepts expected values - spec: town, dungeon, wilderness, settlement, ruins."""
        categories = ["town", "dungeon", "wilderness", "settlement", "ruins"]
        for cat in categories:
            location = Location(
                name=f"Test {cat}",
                description="A test location.",
                category=cat
            )
            assert location.category == cat

    def test_location_category_in_to_dict(self):
        """Test category is included in to_dict when present - spec: serialization."""
        location = Location(
            name="Dark Cave",
            description="A deep cave.",
            category="dungeon"
        )
        data = location.to_dict()
        assert data["category"] == "dungeon"

    def test_location_category_not_in_to_dict_when_none(self):
        """Test category is excluded from to_dict when None - spec: backward compat."""
        location = Location(
            name="Town Square",
            description="A bustling square."
        )
        data = location.to_dict()
        assert "category" not in data

    def test_location_category_from_dict(self):
        """Test category restored from dict - spec: deserialization."""
        data = {
            "name": "Dark Cave",
            "description": "A deep cave.",
            "connections": {},
            "category": "dungeon"
        }
        location = Location.from_dict(data)
        assert location.category == "dungeon"

    def test_location_category_from_dict_missing(self):
        """Test from_dict with missing category defaults to None - spec: backward compat."""
        data = {
            "name": "Town Square",
            "description": "A bustling square.",
            "connections": {}
        }
        location = Location.from_dict(data)
        assert location.category is None

    def test_location_category_roundtrip(self):
        """Test category preserved through serialization roundtrip."""
        original = Location(
            name="Dark Forest",
            description="A shadowy forest.",
            connections={"north": "Cave Entrance"},
            coordinates=(5, 10),
            category="wilderness"
        )
        data = original.to_dict()
        restored = Location.from_dict(data)
        assert restored.category == original.category

    def test_location_category_with_all_fields(self):
        """Test Location with all fields including category works correctly."""
        from cli_rpg.models.npc import NPC

        npc = NPC(
            name="Forest Guardian",
            description="A mystical guardian.",
            dialogue="Welcome to the grove, traveler."
        )

        location = Location(
            name="Enchanted Grove",
            description="A magical grove.",
            connections={"south": "Dark Path"},
            npcs=[npc],
            coordinates=(3, 4),
            category="wilderness"
        )

        # Verify all fields
        assert location.name == "Enchanted Grove"
        assert location.description == "A magical grove."
        assert location.connections == {"south": "Dark Path"}
        assert len(location.npcs) == 1
        assert location.coordinates == (3, 4)
        assert location.category == "wilderness"

        # Verify serialization includes all
        data = location.to_dict()
        assert data["category"] == "wilderness"
        assert data["coordinates"] == [3, 4]
        assert len(data["npcs"]) == 1


class TestCombatWithLocationCategory:
    """Test combat.spawn_enemy() uses location.category when available."""

    def test_spawn_enemy_with_location_category(self):
        """Spec: spawn_enemy uses location.category if provided - primary method."""
        enemy = spawn_enemy(
            location_name="Random Place",  # Name doesn't match any pattern
            level=3,
            location_category="dungeon"  # Explicit category
        )
        # Dungeon enemies: Skeleton, Zombie, Ghost, Dark Knight
        dungeon_enemies = ["Skeleton", "Zombie", "Ghost", "Dark Knight"]
        assert enemy.name in dungeon_enemies

    def test_spawn_enemy_fallback_to_name_matching(self):
        """Spec: spawn_enemy falls back to location name when no category."""
        enemy = spawn_enemy(
            location_name="Dark Forest",  # Name contains 'forest'
            level=3,
            location_category=None
        )
        # Forest enemies: Wolf, Bear, Wild Boar, Giant Spider
        forest_enemies = ["Wolf", "Bear", "Wild Boar", "Giant Spider"]
        assert enemy.name in forest_enemies

    def test_spawn_enemy_category_takes_precedence(self):
        """Spec: category takes precedence over location name matching."""
        # Location name contains 'forest' but category is 'cave'
        enemy = spawn_enemy(
            location_name="Forest Cave",  # Name would match 'forest' first
            level=3,
            location_category="cave"  # But category is cave
        )
        # Cave enemies: Bat, Goblin, Troll, Cave Dweller
        cave_enemies = ["Bat", "Goblin", "Troll", "Cave Dweller"]
        assert enemy.name in cave_enemies

    def test_spawn_enemy_default_when_no_match(self):
        """Spec: uses default enemies when neither category nor name match."""
        enemy = spawn_enemy(
            location_name="Mysterious Place",  # No match
            level=3,
            location_category=None
        )
        # Default enemies: Monster, Creature, Beast, Fiend
        default_enemies = ["Monster", "Creature", "Beast", "Fiend"]
        assert enemy.name in default_enemies

    def test_spawn_enemy_town_category(self):
        """Spec: town category maps to village enemies (bandits, thieves)."""
        enemy = spawn_enemy(
            location_name="Some Place",
            level=3,
            location_category="town"
        )
        # Town/Village enemies: Bandit, Thief, Ruffian, Outlaw
        town_enemies = ["Bandit", "Thief", "Ruffian", "Outlaw"]
        assert enemy.name in town_enemies

    def test_spawn_enemy_settlement_category(self):
        """Spec: settlement category maps to village enemies like town."""
        enemy = spawn_enemy(
            location_name="Some Place",
            level=3,
            location_category="settlement"
        )
        # Settlement/Village enemies: Bandit, Thief, Ruffian, Outlaw
        settlement_enemies = ["Bandit", "Thief", "Ruffian", "Outlaw"]
        assert enemy.name in settlement_enemies

    def test_spawn_enemy_wilderness_category(self):
        """Spec: wilderness category maps to forest enemies."""
        enemy = spawn_enemy(
            location_name="Some Place",
            level=3,
            location_category="wilderness"
        )
        # Wilderness maps to forest enemies: Wolf, Bear, Wild Boar, Giant Spider
        wilderness_enemies = ["Wolf", "Bear", "Wild Boar", "Giant Spider"]
        assert enemy.name in wilderness_enemies

    def test_spawn_enemy_ruins_category(self):
        """Spec: ruins category maps to dungeon enemies."""
        enemy = spawn_enemy(
            location_name="Some Place",
            level=3,
            location_category="ruins"
        )
        # Ruins maps to dungeon enemies: Skeleton, Zombie, Ghost, Dark Knight
        ruins_enemies = ["Skeleton", "Zombie", "Ghost", "Dark Knight"]
        assert enemy.name in ruins_enemies
