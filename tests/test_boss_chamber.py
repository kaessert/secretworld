"""Tests for Boss Chamber encounter in Abandoned Mines.

Tests boss encounter triggering, Stone Sentinel boss, defeat tracking,
and persistence of boss_defeated state.
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.combat import spawn_boss
from cli_rpg.game_state import GameState
from cli_rpg.world import create_default_world


class TestBossChamberTriggersEncounter:
    """Tests that Boss Chamber triggers boss encounter on first entry."""

    def test_boss_chamber_triggers_boss_on_first_entry(self):
        """Enter Boss Chamber triggers combat with a boss enemy."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Boss Chamber
        success, message = game_state.enter("Boss Chamber")

        # Should trigger boss combat
        assert success
        assert game_state.is_in_combat()
        assert game_state.current_combat is not None
        assert len(game_state.current_combat.enemies) == 1
        assert game_state.current_combat.enemies[0].is_boss is True

    def test_boss_chamber_boss_is_stone_sentinel(self):
        """Verify boss is Stone Sentinel with is_boss=True."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Boss Chamber
        success, message = game_state.enter("Boss Chamber")

        # Boss should be Stone Sentinel
        assert game_state.current_combat is not None
        boss = game_state.current_combat.enemies[0]
        assert boss.name == "The Stone Sentinel"
        assert boss.is_boss is True

    def test_boss_chamber_boss_has_dungeon_stats(self):
        """Boss has 2x dungeon category stats."""
        # Test spawn_boss with stone_sentinel template
        boss = spawn_boss("Boss Chamber", level=5, location_category="dungeon", boss_type="stone_sentinel")

        # Stats should be 2x base (as per spawn_boss formula)
        # base_health = (40 + level * 25) * 2 = (40 + 125) * 2 = 330
        expected_health = (40 + 5 * 25) * 2
        assert boss.max_health == expected_health

        # Boss should have stun chance (stone golem trait)
        assert boss.stun_chance > 0


class TestBossChamberNoRespawn:
    """Tests that boss doesn't respawn after defeat."""

    def test_boss_chamber_no_respawn_after_defeat(self):
        """After defeating boss, entering doesn't trigger combat."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Boss Chamber - triggers boss
        success, _ = game_state.enter("Boss Chamber")
        assert game_state.is_in_combat()

        # Defeat the boss
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)  # Kill the boss
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Exit and re-enter
        game_state.exit_location()  # Back to Abandoned Mines
        success, _ = game_state.enter("Boss Chamber")

        # Should NOT trigger combat again
        assert success
        assert not game_state.is_in_combat()

    def test_boss_chamber_boss_defeat_persists_in_save(self):
        """boss_defeated flag serializes correctly."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Boss Chamber and defeat boss
        success, _ = game_state.enter("Boss Chamber")
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Serialize and deserialize
        data = game_state.to_dict()
        restored_state = GameState.from_dict(data)

        # boss_defeated should be preserved
        boss_chamber = restored_state.world["Boss Chamber"]
        assert boss_chamber.boss_defeated is True

    def test_boss_chamber_safe_after_defeat(self):
        """Location becomes safe zone after boss defeated."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Initially not a safe zone
        boss_chamber = game_state.world["Boss Chamber"]
        assert boss_chamber.is_safe_zone is False

        # Enter Boss Chamber and defeat boss
        success, _ = game_state.enter("Boss Chamber")
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Should now be a safe zone
        assert boss_chamber.is_safe_zone is True


class TestLocationBossFields:
    """Tests for Location model boss-related fields."""

    def test_location_boss_enemy_field(self):
        """Location has optional boss_enemy field."""
        location = Location(
            name="Boss Room",
            description="A dark chamber.",
            boss_enemy="stone_sentinel"
        )
        assert location.boss_enemy == "stone_sentinel"

    def test_location_boss_defeated_field(self):
        """Location has boss_defeated field defaulting to False."""
        location = Location(
            name="Boss Room",
            description="A dark chamber.",
            boss_enemy="stone_sentinel"
        )
        assert location.boss_defeated is False

    def test_location_boss_fields_serialization(self):
        """boss_enemy and boss_defeated serialize correctly."""
        location = Location(
            name="Boss Room",
            description="A dark chamber.",
            boss_enemy="stone_sentinel",
            boss_defeated=True
        )

        # Serialize
        data = location.to_dict()
        assert data["boss_enemy"] == "stone_sentinel"
        assert data["boss_defeated"] is True

        # Deserialize
        restored = Location.from_dict(data)
        assert restored.boss_enemy == "stone_sentinel"
        assert restored.boss_defeated is True

    def test_location_boss_fields_backward_compatibility(self):
        """from_dict handles missing boss fields for backward compat."""
        data = {
            "name": "Old Location",
            "description": "An old dungeon room.",
            "connections": {}
        }
        location = Location.from_dict(data)
        assert location.boss_enemy is None
        assert location.boss_defeated is False


class TestStoneSentinelBoss:
    """Tests for Stone Sentinel boss template."""

    def test_spawn_boss_stone_sentinel(self):
        """spawn_boss with stone_sentinel type creates Stone Sentinel."""
        boss = spawn_boss("Boss Chamber", level=5, location_category="dungeon", boss_type="stone_sentinel")
        assert boss.name == "The Stone Sentinel"
        assert boss.is_boss is True

    def test_stone_sentinel_has_stun_ability(self):
        """Stone Sentinel has stun chance (heavy stone fist)."""
        boss = spawn_boss("Boss Chamber", level=5, location_category="dungeon", boss_type="stone_sentinel")
        assert boss.stun_chance > 0  # Heavy stone fist can stun
        assert boss.stun_duration >= 1

    def test_stone_sentinel_has_ascii_art(self):
        """Stone Sentinel has appropriate ASCII art."""
        boss = spawn_boss("Boss Chamber", level=5, location_category="dungeon", boss_type="stone_sentinel")
        assert boss.ascii_art is not None
        assert len(boss.ascii_art) > 0


class TestBossChamberConfiguration:
    """Tests for Boss Chamber configuration in default world."""

    def test_boss_chamber_has_boss_enemy(self):
        """Boss Chamber has boss_enemy = 'stone_sentinel'."""
        world, _ = create_default_world()
        boss_chamber = world["Boss Chamber"]
        assert boss_chamber.boss_enemy == "stone_sentinel"

    def test_boss_chamber_is_not_safe_zone(self):
        """Boss Chamber is not a safe zone (boss makes it dangerous)."""
        world, _ = create_default_world()
        boss_chamber = world["Boss Chamber"]
        assert boss_chamber.is_safe_zone is False

    def test_boss_chamber_has_dungeon_category(self):
        """Boss Chamber has dungeon category."""
        world, _ = create_default_world()
        boss_chamber = world["Boss Chamber"]
        assert boss_chamber.category == "dungeon"
