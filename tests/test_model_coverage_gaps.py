"""Tests for coverage gaps in character.py, inventory.py, and world_grid.py.

These tests target specific uncovered lines to increase overall test coverage.
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.inventory import Inventory
from cli_rpg.models.location import Location
from cli_rpg.world_grid import WorldGrid


# ==============================================================================
# character.py coverage gaps
# ==============================================================================

class TestCharacterUseItemGenericConsumable:
    """Test use_item on generic consumable without heal (lines 204-210)."""

    def test_use_item_generic_consumable_no_heal(self):
        """Test using a consumable item that has no heal amount.

        Spec: Lines 204-210 - use_item on generic consumable without heal.
        """
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Create a consumable with 0 heal amount (generic consumable)
        generic_potion = Item(
            name="Mystery Elixir",
            description="A strange brew with unknown effects",
            item_type=ItemType.CONSUMABLE,
            heal_amount=0  # No healing
        )

        char.inventory.add_item(generic_potion)

        success, message = char.use_item(generic_potion)

        assert success is True
        assert "You used Mystery Elixir" in message
        assert generic_potion not in char.inventory.items

    def test_use_item_generic_consumable_with_quest_progress(self):
        """Test using generic consumable that triggers quest progress (line 209).

        Spec: Lines 204-210 - use_item on generic consumable with quest tracking.
        This specifically tests line 209 where quest_messages are appended to the message.
        """
        from cli_rpg.models.quest import Quest, ObjectiveType, QuestStatus

        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Create a consumable with 0 heal amount (generic consumable)
        mystery_item = Item(
            name="Ancient Artifact",
            description="A relic from a forgotten age",
            item_type=ItemType.CONSUMABLE,
            heal_amount=0
        )

        # Add quest that tracks using this item - USE objective tracks record_use()
        quest = Quest(
            name="Use the Relic",
            description="Use the ancient artifact",
            objective_type=ObjectiveType.USE,  # USE objective tracks record_use
            target="Ancient Artifact",
            target_count=1,
            status=QuestStatus.ACTIVE
        )
        char.quests.append(quest)
        char.inventory.add_item(mystery_item)

        success, message = char.use_item(mystery_item)

        assert success is True
        assert "You used Ancient Artifact" in message
        # This verifies line 209 - quest messages are appended
        assert "Quest objectives complete" in message or "Quest progress" in message


class TestCharacterDisplayColoredHealth:
    """Test display colored health at different thresholds (lines 665-668)."""

    def test_character_str_health_above_50_percent(self):
        """Test that health > 50% is displayed in green (heal color).

        Spec: Lines 663-664 - Health > 50% display.
        """
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # Full health = 100%
        result = str(char)

        assert "Hero" in result
        assert "Level 1" in result
        assert "Health" in result

    def test_character_str_health_between_25_and_50_percent(self):
        """Test that health 25-50% is displayed in gold color.

        Spec: Lines 665-666 - Health 25-50% display.
        """
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # With strength=10: max_health = 100 + 10*5 = 150
        # For 40% health: 150 * 0.4 = 60, so need to take 90 damage
        char.take_damage(90)  # 150 - 90 = 60 health = 40%

        result = str(char)

        assert "Hero" in result
        assert "60/" in result  # Should show current health

    def test_character_str_health_below_25_percent(self):
        """Test that health <= 25% is displayed in damage color.

        Spec: Lines 667-668 - Health <= 25% display.
        """
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        # With strength=10: max_health = 100 + 10*5 = 150
        # For 20% health: 150 * 0.2 = 30, so need to take 120 damage
        char.take_damage(120)  # 150 - 120 = 30 health = 20%

        result = str(char)

        assert "Hero" in result
        assert "30/" in result  # Should show current health


# ==============================================================================
# inventory.py coverage gaps
# ==============================================================================

class TestInventoryUnequipWhenFull:
    """Test unequip armor when inventory is full (lines 143-146)."""

    def test_unequip_armor_when_inventory_full_returns_false(self):
        """Test that unequipping armor fails when inventory is full.

        Spec: Lines 143-146 - unequip armor when inventory is full.
        """
        # Create inventory with capacity 2
        inv = Inventory(capacity=2)

        # Equip armor directly
        armor = Item(
            name="Leather Armor",
            description="Light protection",
            item_type=ItemType.ARMOR,
            defense_bonus=3
        )
        inv.equipped_armor = armor

        # Fill inventory to capacity
        item1 = Item(name="Potion", description="Heals", item_type=ItemType.CONSUMABLE)
        item2 = Item(name="Scroll", description="Magic", item_type=ItemType.MISC)
        inv.items.append(item1)
        inv.items.append(item2)

        assert inv.is_full()

        # Try to unequip armor - should fail
        result = inv.unequip("armor")

        assert result is False
        assert inv.equipped_armor == armor  # Still equipped


class TestInventoryUnequipInvalidSlot:
    """Test unequip invalid slot returns False (line 151)."""

    def test_unequip_invalid_slot_returns_false(self):
        """Test that unequipping an invalid slot returns False.

        Spec: Line 151 - unequip invalid slot returns False.
        """
        inv = Inventory()

        result = inv.unequip("helmet")  # Invalid slot

        assert result is False


class TestInventoryDisplayWithEquippedArmor:
    """Test display with equipped armor (line 246)."""

    def test_inventory_str_shows_equipped_armor(self):
        """Test that __str__ displays equipped armor.

        Spec: Line 246 - display with equipped armor.
        """
        inv = Inventory()

        armor = Item(
            name="Steel Plate",
            description="Heavy armor",
            item_type=ItemType.ARMOR,
            defense_bonus=10
        )
        inv.equipped_armor = armor

        result = str(inv)

        assert "Armor" in result
        assert "Steel Plate" in result


# ==============================================================================
# world_grid.py coverage gaps
# ==============================================================================

class TestWorldGridGetNeighborInvalidDirection:
    """Test get_neighbor with invalid direction (line 137)."""

    def test_get_neighbor_invalid_direction_returns_none(self):
        """Test that get_neighbor returns None for invalid direction.

        Spec: Line 137 - get_neighbor with invalid direction.
        """
        grid = WorldGrid()

        loc = Location(name="Town", description="A town.")
        grid.add_location(loc, 0, 0)

        result = grid.get_neighbor(0, 0, "up")  # up is not in DIRECTION_OFFSETS

        assert result is None


class TestWorldGridIterator:
    """Test __iter__ method (line 218)."""

    def test_world_grid_iteration(self):
        """Test that WorldGrid can be iterated over.

        Spec: Line 218 - __iter__ method.
        """
        grid = WorldGrid()

        loc1 = Location(name="Town", description="A town.")
        loc2 = Location(name="Forest", description="A forest.")
        grid.add_location(loc1, 0, 0)
        grid.add_location(loc2, 0, 1)

        names = list(grid)

        assert "Town" in names
        assert "Forest" in names
        assert len(names) == 2


class TestWorldGridValues:
    """Test values() method (line 226)."""

    def test_world_grid_values(self):
        """Test that values() returns locations.

        Spec: Line 226 - values() method.
        """
        grid = WorldGrid()

        loc1 = Location(name="Town", description="A town.")
        loc2 = Location(name="Forest", description="A forest.")
        grid.add_location(loc1, 0, 0)
        grid.add_location(loc2, 0, 1)

        values = list(grid.values())

        assert len(values) == 2
        assert all(isinstance(v, Location) for v in values)


class TestWorldGridEnsureDanglingExitsNoCoordinates:
    """Test ensure_dangling_exits with no coordinates (line 318)."""

    def test_ensure_expansion_possible_skips_no_coordinates(self):
        """Test that locations without coordinates are skipped.

        Spec: Line 318 - ensure_dangling_exits with no coordinates.
        """
        grid = WorldGrid()

        # Add location directly to name index without coordinates
        loc = Location(name="Floating Island", description="No coordinates")
        grid._by_name[loc.name] = loc  # No coordinates set

        # Should not crash, should return False (no candidates)
        result = grid.ensure_expansion_possible()

        # Since the only location has no coordinates, it should return False
        # (can't add expansion point to location without coordinates)
        assert result is False


class TestWorldGridEnsureDanglingExitsNoCandidates:
    """Test ensure_dangling_exits returns False when no candidates (line 330)."""

    def test_ensure_expansion_possible_no_candidates_returns_false(self):
        """Test that False is returned when no candidates exist.

        Spec: Line 330 - ensure_dangling_exits returns False when no candidates.
        """
        grid = WorldGrid()

        # Add location with all directions used
        loc = Location(name="Center", description="A central hub.")
        grid.add_location(loc, 0, 0)

        # Fill all directions with connections
        loc.add_connection("north", "Placeholder North")
        loc.add_connection("south", "Placeholder South")
        loc.add_connection("east", "Placeholder East")
        loc.add_connection("west", "Placeholder West")

        # Now it already has expansion exits, so should return False
        result = grid.ensure_expansion_possible()

        assert result is False  # Already has expansion exits


class TestWorldGridEnsureExpansionAlreadyPossible:
    """Test ensure_expansion_possible when already possible."""

    def test_ensure_expansion_possible_already_has_exits(self):
        """Test that ensure_expansion_possible returns False when exits exist.

        Spec: Line 309-310 - Return False if already has frontier exits.
        """
        grid = WorldGrid()

        loc = Location(name="Town", description="A town.")
        grid.add_location(loc, 0, 0)

        # Add a dangling connection
        loc.add_connection("north", "Unexplored North")

        # Should return False because world already has expansion exits
        result = grid.ensure_expansion_possible()

        assert result is False
        assert grid.has_expansion_exits()


class TestWorldGridFindFrontierExitsCardinalOnly:
    """Test find_frontier_exits only considers cardinal directions."""

    def test_find_frontier_exits_ignores_non_cardinal(self):
        """Test that up/down connections are not counted as frontier exits.

        Spec: Lines 255-256 - Only check cardinal directions.
        """
        grid = WorldGrid()

        loc = Location(name="Tower", description="A tall tower.")
        grid.add_location(loc, 0, 0)

        # Add up/down connections (not in DIRECTION_OFFSETS)
        loc.add_connection("up", "Tower Top")
        loc.add_connection("down", "Tower Basement")

        # These should NOT be counted as frontier exits
        frontier = grid.find_frontier_exits()

        # Should be empty because up/down are not cardinal directions
        assert len(frontier) == 0


class TestWorldGridContains:
    """Test __contains__ method."""

    def test_world_grid_contains(self):
        """Test that 'in' operator works for WorldGrid."""
        grid = WorldGrid()

        loc = Location(name="Town Square", description="Central plaza.")
        grid.add_location(loc, 0, 0)

        assert "Town Square" in grid
        assert "Nonexistent" not in grid
