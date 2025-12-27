"""Tests for Forest Boss (Elder Treant) encounter in Ancient Grove.

Tests boss encounter triggering, Elder Treant boss, poison ability,
defeat tracking, and persistence of boss_defeated state.

Spec: Ancient Grove in Forest has elder_treant boss with poison ability.
"""

import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.combat import spawn_boss, get_boss_ascii_art
from cli_rpg.game_state import GameState
from cli_rpg.world import create_default_world


def navigate_to_ancient_grove(game_state: GameState) -> bool:
    """Navigate through the forest from entry point to Ancient Grove.

    Path: Forest -> Forest Edge (entry) -> east to Ancient Grove

    Returns True if successfully reached Ancient Grove.
    """
    # Enter at Forest Edge (entry point)
    success, _ = game_state.enter("Forest Edge")
    if not success:
        return False

    # Navigate to Ancient Grove (east from Forest Edge)
    success, _ = game_state.move("east")
    return success


class TestAncientGroveConfiguration:
    """Tests for Ancient Grove configuration with boss_enemy."""

    # Spec: Ancient Grove has boss_enemy = "elder_treant"
    def test_ancient_grove_has_boss_enemy(self):
        """Ancient Grove has boss_enemy = 'elder_treant'."""
        world, _ = create_default_world()
        forest = world["Forest"]
        ancient_grove = forest.sub_grid.get_by_name("Ancient Grove")
        assert ancient_grove.boss_enemy == "elder_treant"

    # Spec: Ancient Grove uses forest category
    def test_ancient_grove_has_forest_category(self):
        """Ancient Grove has forest category."""
        world, _ = create_default_world()
        forest = world["Forest"]
        ancient_grove = forest.sub_grid.get_by_name("Ancient Grove")
        assert ancient_grove.category == "forest"

    # Spec: Boss location starts as not safe
    def test_ancient_grove_is_not_safe_zone(self):
        """Ancient Grove is not a safe zone (boss makes it dangerous)."""
        world, _ = create_default_world()
        forest = world["Forest"]
        ancient_grove = forest.sub_grid.get_by_name("Ancient Grove")
        assert ancient_grove.is_safe_zone is False


class TestAncientGroveTriggersEncounter:
    """Tests that Ancient Grove triggers boss encounter on first entry."""

    # Spec: Entering Ancient Grove triggers boss combat
    def test_ancient_grove_triggers_boss_on_first_entry(self):
        """Enter Ancient Grove triggers combat with a boss enemy."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Forest")

        # Navigate to Ancient Grove through entry point
        success = navigate_to_ancient_grove(game_state)

        # Should trigger boss combat
        assert success
        assert game_state.is_in_combat()
        assert game_state.current_combat is not None
        assert len(game_state.current_combat.enemies) == 1
        assert game_state.current_combat.enemies[0].is_boss is True

    # Spec: Boss is Elder Treant with is_boss=True
    def test_ancient_grove_boss_is_elder_treant(self):
        """Verify boss is Elder Treant with is_boss=True."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Forest")

        # Navigate to Ancient Grove through entry point
        success = navigate_to_ancient_grove(game_state)

        # Boss should be Elder Treant
        assert success
        assert game_state.current_combat is not None
        boss = game_state.current_combat.enemies[0]
        assert boss.name == "The Elder Treant"
        assert boss.is_boss is True


class TestElderTreantBoss:
    """Tests for Elder Treant boss template."""

    # Spec: spawn_boss with elder_treant returns correct enemy
    def test_spawn_boss_elder_treant(self):
        """spawn_boss with elder_treant type creates Elder Treant."""
        boss = spawn_boss("Ancient Grove", level=5, location_category="forest", boss_type="elder_treant")
        assert boss.name == "The Elder Treant"
        assert boss.is_boss is True

    # Spec: Boss has poison ability (nature's corruption theme)
    def test_elder_treant_has_poison_ability(self):
        """Elder Treant has poison chance (nature's corruption)."""
        boss = spawn_boss("Ancient Grove", level=5, location_category="forest", boss_type="elder_treant")
        assert boss.poison_chance > 0  # Nature's corruption can poison
        assert boss.poison_damage > 0
        assert boss.poison_duration >= 1

    # Spec: Boss has 2x base stats
    def test_elder_treant_has_boss_stats(self):
        """Elder Treant has 2x base stats (boss scaling)."""
        boss = spawn_boss("Ancient Grove", level=5, location_category="forest", boss_type="elder_treant")

        # Stats should be 2x base (as per spawn_boss formula)
        # base_health = (40 + level * 25) * 2 = (40 + 125) * 2 = 330
        expected_health = (40 + 5 * 25) * 2
        assert boss.max_health == expected_health

    # Spec: Boss has ASCII art
    def test_elder_treant_has_ascii_art(self):
        """Elder Treant has appropriate ASCII art."""
        boss = spawn_boss("Ancient Grove", level=5, location_category="forest", boss_type="elder_treant")
        assert boss.ascii_art is not None
        assert len(boss.ascii_art) > 0


class TestBossAsciiArtForForest:
    """Tests for get_boss_ascii_art with treant/forest keywords."""

    # Spec: get_boss_ascii_art recognizes treant/forest keywords
    def test_get_boss_ascii_art_treant(self):
        """get_boss_ascii_art returns art for 'treant' keyword."""
        art = get_boss_ascii_art("Elder Treant")
        assert art is not None
        assert len(art) > 0

    def test_get_boss_ascii_art_tree(self):
        """get_boss_ascii_art returns art for 'tree' keyword."""
        art = get_boss_ascii_art("Ancient Tree Spirit")
        assert art is not None
        assert len(art) > 0

    def test_get_boss_ascii_art_grove(self):
        """get_boss_ascii_art returns art for 'grove' keyword."""
        art = get_boss_ascii_art("Grove Guardian")
        assert art is not None
        assert len(art) > 0

    def test_get_boss_ascii_art_dryad(self):
        """get_boss_ascii_art returns art for 'dryad' keyword."""
        art = get_boss_ascii_art("Ancient Dryad")
        assert art is not None
        assert len(art) > 0


class TestAncientGroveNoRespawn:
    """Tests that boss doesn't respawn after defeat."""

    # Spec: No respawn after defeat
    def test_ancient_grove_no_respawn_after_defeat(self):
        """After defeating boss, entering doesn't trigger combat."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Forest")

        # First enter Forest Edge (entry point for Forest)
        success, _ = game_state.enter("Forest Edge")
        assert success, "Failed to enter Forest Edge"

        # Navigate to Ancient Grove via the SubGrid
        # Forest Edge (0,0) -> Ancient Grove (1,0) is east
        success, _ = game_state.move("east")
        assert success, "Failed to move to Ancient Grove"
        assert game_state.is_in_combat(), "Should trigger boss combat"

        # Defeat the boss
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)  # Kill the boss
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Exit and re-enter
        game_state.move("west")  # Back to Forest Edge
        success, _ = game_state.move("east")  # Back to Ancient Grove

        # Should NOT trigger combat again
        assert success
        assert not game_state.is_in_combat()

    # Spec: Location becomes safe zone after defeat
    def test_ancient_grove_safe_after_defeat(self):
        """Location becomes safe zone after boss defeated."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Forest")

        # Get Ancient Grove via SubGrid
        forest = game_state.world["Forest"]
        ancient_grove = forest.sub_grid.get_by_name("Ancient Grove")
        assert ancient_grove.is_safe_zone is False

        # Enter Forest Edge, then move to Ancient Grove
        game_state.enter("Forest Edge")
        game_state.move("east")  # To Ancient Grove

        # Defeat boss
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Should now be a safe zone
        assert ancient_grove.is_safe_zone is True


class TestAncientGrovePersistence:
    """Tests for boss_defeated state persistence."""

    # Spec: boss_defeated persists in save/load
    def test_ancient_grove_boss_defeat_persists_in_save(self):
        """boss_defeated flag serializes correctly."""
        world, _ = create_default_world()
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(player, world, starting_location="Forest")

        # Enter Forest Edge, then move to Ancient Grove
        game_state.enter("Forest Edge")
        game_state.move("east")  # To Ancient Grove

        # Defeat boss
        boss = game_state.current_combat.enemies[0]
        boss.take_damage(boss.health)
        game_state.current_combat.end_combat(victory=True)
        game_state.mark_boss_defeated()  # Mark boss as defeated
        game_state.current_combat = None

        # Serialize and deserialize
        data = game_state.to_dict()
        restored_state = GameState.from_dict(data)

        # boss_defeated should be preserved - access via SubGrid
        forest = restored_state.world["Forest"]
        ancient_grove = forest.sub_grid.get_by_name("Ancient Grove")
        assert ancient_grove.boss_defeated is True


class TestForestBossCategory:
    """Tests for forest boss category in boss_templates."""

    # Spec: forest category exists in boss_templates
    def test_spawn_boss_forest_category(self):
        """spawn_boss with forest category creates a boss."""
        boss = spawn_boss("Some Forest Location", level=5, location_category="forest")
        assert boss.is_boss is True
        assert boss.max_health > 0
