"""Tests for Flooded Level Boss (Drowned Overseer) encounter in Abandoned Mines.

Tests boss encounter triggering, Drowned Overseer boss, bleed and freeze abilities,
defeat tracking, and persistence of boss_defeated state.

Spec: Flooded Level in Abandoned Mines has drowned_overseer boss with bleed and freeze abilities.
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.combat import spawn_boss, get_boss_ascii_art
from cli_rpg.game_state import GameState
from cli_rpg.world import create_default_world


class TestFloodedLevelConfiguration:
    """Tests for Flooded Level configuration with boss_enemy."""

    # Spec: Flooded Level has boss_enemy = "drowned_overseer"
    def test_flooded_level_has_boss_enemy(self):
        """Flooded Level has boss_enemy = 'drowned_overseer'."""
        world, _ = create_default_world()
        flooded_level = world["Flooded Level"]
        assert flooded_level.boss_enemy == "drowned_overseer"

    # Spec: Flooded Level uses dungeon category
    def test_flooded_level_has_dungeon_category(self):
        """Flooded Level has dungeon category."""
        world, _ = create_default_world()
        flooded_level = world["Flooded Level"]
        assert flooded_level.category == "dungeon"

    # Spec: Boss location starts as not safe
    def test_flooded_level_is_not_safe_zone(self):
        """Flooded Level is not a safe zone (boss makes it dangerous)."""
        world, _ = create_default_world()
        flooded_level = world["Flooded Level"]
        assert flooded_level.is_safe_zone is False


class TestFloodedLevelTriggersEncounter:
    """Tests that Flooded Level triggers boss encounter on first entry."""

    # Spec: Entering Flooded Level triggers boss combat
    def test_flooded_level_triggers_boss_on_first_entry(self):
        """Enter Flooded Level triggers combat with a boss enemy."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Flooded Level
        success, message = game_state.enter("Flooded Level")

        # Should trigger boss combat
        assert success
        assert game_state.is_in_combat()
        assert game_state.current_combat is not None
        assert len(game_state.current_combat.enemies) == 1
        assert game_state.current_combat.enemies[0].is_boss is True

    # Spec: Boss is Drowned Overseer with is_boss=True
    def test_flooded_level_boss_is_drowned_overseer(self):
        """Verify boss is Drowned Overseer with is_boss=True."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Flooded Level
        success, message = game_state.enter("Flooded Level")

        # Boss should be Drowned Overseer
        assert game_state.current_combat is not None
        boss = game_state.current_combat.enemies[0]
        assert boss.name == "The Drowned Overseer"
        assert boss.is_boss is True


class TestDrownedOverseerBoss:
    """Tests for Drowned Overseer boss template."""

    # Spec: spawn_boss with drowned_overseer returns correct enemy
    def test_spawn_boss_drowned_overseer(self):
        """spawn_boss with drowned_overseer type creates Drowned Overseer."""
        boss = spawn_boss("Flooded Level", level=5, location_category="dungeon", boss_type="drowned_overseer")
        assert boss.name == "The Drowned Overseer"
        assert boss.is_boss is True

    # Spec: Boss has bleed ability (rusted pickaxe theme)
    def test_drowned_overseer_has_bleed_ability(self):
        """Drowned Overseer has bleed chance (rusted mining tools)."""
        boss = spawn_boss("Flooded Level", level=5, location_category="dungeon", boss_type="drowned_overseer")
        assert boss.bleed_chance > 0  # Rusted pickaxe can cause bleeding
        assert boss.bleed_damage > 0
        assert boss.bleed_duration >= 1

    # Spec: Boss has freeze ability (icy water touch)
    def test_drowned_overseer_has_freeze_ability(self):
        """Drowned Overseer has freeze chance (icy water)."""
        boss = spawn_boss("Flooded Level", level=5, location_category="dungeon", boss_type="drowned_overseer")
        assert boss.freeze_chance > 0  # Icy water touch can freeze
        assert boss.freeze_duration >= 1

    # Spec: Boss has 2x base stats
    def test_drowned_overseer_has_boss_stats(self):
        """Drowned Overseer has 2x base stats (boss scaling)."""
        boss = spawn_boss("Flooded Level", level=5, location_category="dungeon", boss_type="drowned_overseer")

        # Stats should be 2x base (as per spawn_boss formula)
        # base_health = (40 + level * 25) * 2 = (40 + 125) * 2 = 330
        expected_health = (40 + 5 * 25) * 2
        assert boss.max_health == expected_health

    # Spec: Boss has ASCII art
    def test_drowned_overseer_has_ascii_art(self):
        """Drowned Overseer has appropriate ASCII art."""
        boss = spawn_boss("Flooded Level", level=5, location_category="dungeon", boss_type="drowned_overseer")
        assert boss.ascii_art is not None
        assert len(boss.ascii_art) > 0


class TestBossAsciiArtForDrownedOverseer:
    """Tests for get_boss_ascii_art with drowned/overseer/flooded keywords."""

    # Spec: get_boss_ascii_art recognizes drowned/overseer/flooded keywords
    def test_get_boss_ascii_art_drowned(self):
        """get_boss_ascii_art returns art for 'drowned' keyword."""
        art = get_boss_ascii_art("Drowned Overseer")
        assert art is not None
        assert len(art) > 0

    def test_get_boss_ascii_art_overseer(self):
        """get_boss_ascii_art returns art for 'overseer' keyword."""
        art = get_boss_ascii_art("The Overseer")
        assert art is not None
        assert len(art) > 0

    def test_get_boss_ascii_art_flooded(self):
        """get_boss_ascii_art returns art for 'flooded' keyword."""
        art = get_boss_ascii_art("Flooded Guardian")
        assert art is not None
        assert len(art) > 0


class TestFloodedLevelNoRespawn:
    """Tests that boss doesn't respawn after defeat."""

    # Spec: No respawn after defeat
    def test_flooded_level_no_respawn_after_defeat(self):
        """After defeating boss, entering doesn't trigger combat."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Flooded Level - triggers boss
        success, _ = game_state.enter("Flooded Level")
        assert game_state.is_in_combat()

        # Defeat the boss
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)  # Kill the boss
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Exit and re-enter
        game_state.exit_location()  # Back to Abandoned Mines
        success, _ = game_state.enter("Flooded Level")

        # Should NOT trigger combat again
        assert success
        assert not game_state.is_in_combat()

    # Spec: Location becomes safe zone after defeat
    def test_flooded_level_safe_after_defeat(self):
        """Location becomes safe zone after boss defeated."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Initially not a safe zone
        flooded_level = game_state.world["Flooded Level"]
        assert flooded_level.is_safe_zone is False

        # Enter Flooded Level and defeat boss
        success, _ = game_state.enter("Flooded Level")
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Should now be a safe zone
        assert flooded_level.is_safe_zone is True


class TestFloodedLevelPersistence:
    """Tests for boss_defeated state persistence."""

    # Spec: boss_defeated persists in save/load
    def test_flooded_level_boss_defeat_persists_in_save(self):
        """boss_defeated flag serializes correctly."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Abandoned Mines")

        # Enter Flooded Level and defeat boss
        success, _ = game_state.enter("Flooded Level")
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Serialize and deserialize
        data = game_state.to_dict()
        restored_state = GameState.from_dict(data)

        # boss_defeated should be preserved
        flooded_level = restored_state.world["Flooded Level"]
        assert flooded_level.boss_defeated is True
