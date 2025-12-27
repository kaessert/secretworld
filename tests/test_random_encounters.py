"""Tests for random encounter system.

Tests the RandomEncounter model and random_encounters module functionality.
"""
import pytest
from unittest.mock import patch, MagicMock

from cli_rpg.models.random_encounter import RandomEncounter
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.npc import NPC
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.models.shop import Shop, ShopItem
from cli_rpg.models.item import Item, ItemType
from cli_rpg.game_state import GameState
from cli_rpg.random_encounters import (
    RANDOM_ENCOUNTER_CHANCE,
    ENCOUNTER_WEIGHTS,
    check_for_random_encounter,
    spawn_wandering_merchant,
    spawn_wanderer,
    format_encounter_message,
    _select_encounter_type,
)


class TestRandomEncounterModel:
    """Tests for RandomEncounter dataclass.

    Spec: RandomEncounter model should have encounter_type, entity, and description fields
    """

    def test_random_encounter_model_creation(self):
        """Test RandomEncounter dataclass with required fields.

        Spec: Should create with encounter_type, entity, and description
        """
        enemy = Enemy(
            name="Goblin", health=30, max_health=30,
            attack_power=5, defense=2, xp_reward=20
        )
        encounter = RandomEncounter(
            encounter_type="hostile",
            entity=enemy,
            description="A goblin jumps out!"
        )

        assert encounter.encounter_type == "hostile"
        assert encounter.entity == enemy
        assert encounter.description == "A goblin jumps out!"

    def test_random_encounter_merchant_type(self):
        """Test RandomEncounter with merchant type.

        Spec: Merchant encounters should accept NPC entities
        """
        npc = NPC(
            name="Traveling Merchant",
            description="A merchant with wares",
            dialogue="Want to trade?"
        )
        encounter = RandomEncounter(
            encounter_type="merchant",
            entity=npc,
            description="A merchant appears!"
        )

        assert encounter.encounter_type == "merchant"
        assert isinstance(encounter.entity, NPC)

    def test_random_encounter_wanderer_type(self):
        """Test RandomEncounter with wanderer type.

        Spec: Wanderer encounters should accept NPC entities
        """
        npc = NPC(
            name="Weary Traveler",
            description="A tired wanderer",
            dialogue="Dark times ahead..."
        )
        encounter = RandomEncounter(
            encounter_type="wanderer",
            entity=npc,
            description="You meet a wanderer."
        )

        assert encounter.encounter_type == "wanderer"
        assert isinstance(encounter.entity, NPC)

    def test_random_encounter_invalid_type(self):
        """Test that invalid encounter types raise ValueError.

        Spec: Only "hostile", "merchant", "wanderer" are valid types
        """
        enemy = Enemy(
            name="Goblin", health=30, max_health=30,
            attack_power=5, defense=2, xp_reward=20
        )
        with pytest.raises(ValueError, match="encounter_type must be one of"):
            RandomEncounter(
                encounter_type="invalid",
                entity=enemy,
                description="Test"
            )

    def test_random_encounter_hostile_requires_enemy(self):
        """Test that hostile encounters require Enemy entity.

        Spec: Hostile encounters must have Enemy, not NPC
        """
        npc = NPC(name="Merchant", description="A merchant", dialogue="Hello")
        with pytest.raises(ValueError, match="hostile encounters must have an Enemy"):
            RandomEncounter(
                encounter_type="hostile",
                entity=npc,
                description="Test"
            )

    def test_random_encounter_merchant_requires_npc(self):
        """Test that merchant encounters require NPC entity.

        Spec: Merchant encounters must have NPC, not Enemy
        """
        enemy = Enemy(
            name="Goblin", health=30, max_health=30,
            attack_power=5, defense=2, xp_reward=20
        )
        with pytest.raises(ValueError, match="merchant encounters must have an NPC"):
            RandomEncounter(
                encounter_type="merchant",
                entity=enemy,
                description="Test"
            )

    def test_random_encounter_serialization(self):
        """Test to_dict/from_dict roundtrip.

        Spec: Should preserve all fields through serialization
        """
        enemy = Enemy(
            name="Wolf", health=25, max_health=25,
            attack_power=6, defense=1, xp_reward=15
        )
        original = RandomEncounter(
            encounter_type="hostile",
            entity=enemy,
            description="A wolf attacks!"
        )

        # Serialize
        data = original.to_dict()
        assert data["encounter_type"] == "hostile"
        assert data["entity_type"] == "enemy"
        assert data["description"] == "A wolf attacks!"
        assert data["entity"]["name"] == "Wolf"

        # Deserialize
        restored = RandomEncounter.from_dict(data)
        assert restored.encounter_type == original.encounter_type
        assert restored.description == original.description
        assert restored.entity.name == enemy.name

    def test_random_encounter_serialization_npc(self):
        """Test serialization with NPC entity.

        Spec: Should serialize and deserialize NPC entities correctly
        """
        npc = NPC(
            name="Trader",
            description="A traveling trader",
            dialogue="Looking for goods?"
        )
        original = RandomEncounter(
            encounter_type="merchant",
            entity=npc,
            description="A trader approaches."
        )

        data = original.to_dict()
        assert data["entity_type"] == "npc"

        restored = RandomEncounter.from_dict(data)
        assert isinstance(restored.entity, NPC)
        assert restored.entity.name == "Trader"


class TestRandomEncounterChance:
    """Tests for encounter chance configuration.

    Spec: Random encounter chance should be 15% (configurable constant)
    """

    def test_random_encounter_chance_configurable(self):
        """Verify 15% chance constant exists.

        Spec: RANDOM_ENCOUNTER_CHANCE = 0.15
        """
        assert RANDOM_ENCOUNTER_CHANCE == 0.15

    def test_encounter_weights_sum_to_one(self):
        """Verify encounter weights sum to 1.0.

        Spec: ENCOUNTER_WEIGHTS values should sum to 1.0
        """
        total = sum(ENCOUNTER_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001  # Allow for float precision

    def test_encounter_weights_correct(self):
        """Verify encounter type weights.

        Spec: hostile=60%, merchant=25%, wanderer=15%
        """
        assert ENCOUNTER_WEIGHTS["hostile"] == 0.60
        assert ENCOUNTER_WEIGHTS["merchant"] == 0.25
        assert ENCOUNTER_WEIGHTS["wanderer"] == 0.15


class TestMoveRandomEncounter:
    """Tests for random encounter integration with GameState.move()."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create a basic game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Start": Location("Start", "Start location", coordinates=(0, 0)),
            "End": Location("End", "End location", coordinates=(0, 1)),
        }
        return GameState(character, world, "Start")

    def test_move_can_trigger_random_encounter(self, game_state, monkeypatch):
        """Test that move with seeded RNG triggers encounter.

        Spec: Move should check for random encounter after successful movement
        """
        # Disable whisper service to avoid random interference
        game_state.whisper_service.get_whisper = lambda **kwargs: None

        # Disable weather transitions to avoid random interference
        game_state.weather.transition = lambda: None

        # Mock random.random in random_encounters module to trigger encounter
        # Value must be <= 0.15 to trigger, then <= 0.60 for hostile
        call_count = [0]
        def mock_random():
            call_count[0] += 1
            if call_count[0] == 1:
                return 0.10  # Trigger encounter (< 0.15)
            elif call_count[0] == 2:
                return 0.30  # Select hostile (< 0.60)
            return 0.50  # Default for any other calls

        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)
        # Also mock the combat module's random calls
        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])
        monkeypatch.setattr("cli_rpg.combat.random.randint", lambda a, b: a)

        success, message = game_state.move("north")

        assert success is True
        assert "[Random Encounter!]" in message
        # Should have started combat
        assert game_state.is_in_combat()

    def test_no_encounter_when_roll_fails(self, game_state, monkeypatch):
        """Test that no encounter happens when roll exceeds threshold.

        Spec: No encounter when random() > RANDOM_ENCOUNTER_CHANCE
        """
        # Mock random to fail encounter check (above 0.15 threshold)
        mock_random = MagicMock(return_value=0.50)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        success, message = game_state.move("north")

        assert success is True
        assert "[Random Encounter!]" not in message
        assert not game_state.is_in_combat()

    def test_no_encounter_when_already_in_combat(self, game_state, monkeypatch):
        """Skip random encounters if combat active.

        Spec: Should not trigger random encounter when already in combat
        """
        from cli_rpg.combat import CombatEncounter
        from cli_rpg.models.enemy import Enemy

        # Start combat before move
        enemy = Enemy(
            name="Goblin", health=30, max_health=30,
            attack_power=5, defense=2, xp_reward=20
        )
        game_state.current_combat = CombatEncounter(game_state.current_character, enemies=[enemy])
        game_state.current_combat.is_active = True

        # Mock random to always trigger
        mock_random = MagicMock(return_value=0.05)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        # Call the check directly (since move won't trigger during combat normally)
        result = check_for_random_encounter(game_state)

        # Should not trigger because already in combat
        assert result is None


class TestHostileEncounter:
    """Tests for hostile random encounters."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create a basic game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Forest": Location(
                "Dark Forest", "A dark forest",
                coordinates=(0, 0), category="forest"
            ),
            "Clearing": Location(
                "Clearing", "A forest clearing",
                coordinates=(0, 1)
            ),
        }
        return GameState(character, world, "Forest")

    def test_hostile_encounter_starts_combat(self, game_state, monkeypatch):
        """Hostile encounter type creates CombatEncounter.

        Spec: Hostile encounters should start combat using existing trigger_encounter pattern
        """
        # Mock to trigger hostile encounter
        random_values = [0.05, 0.30]  # trigger=True, type=hostile (< 0.60)
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        # Need to also mock the spawn_enemy random calls
        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])
        monkeypatch.setattr("cli_rpg.combat.random.randint", lambda a, b: a)

        result = check_for_random_encounter(game_state)

        assert result is not None
        assert "[Random Encounter!]" in result
        assert game_state.is_in_combat()
        assert game_state.current_combat is not None

    def test_encounter_respects_location_category(self, game_state, monkeypatch):
        """Hostile encounters use location category for enemy type.

        Spec: Enemy spawned should respect the location's category
        """
        # Mock to trigger hostile encounter
        random_values = [0.05, 0.30]  # trigger=True, type=hostile
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        # Mock spawn_enemy to capture arguments
        original_spawn = None
        captured_args = {}

        def mock_spawn_enemy(location_name, level, location_category=None, terrain_type=None, distance=0):
            captured_args["location_name"] = location_name
            captured_args["location_category"] = location_category
            captured_args["terrain_type"] = terrain_type
            # Return a valid enemy
            return Enemy(
                name="Wolf", health=30, max_health=30,
                attack_power=5, defense=2, xp_reward=20
            )

        monkeypatch.setattr("cli_rpg.random_encounters.spawn_enemy", mock_spawn_enemy)

        check_for_random_encounter(game_state)

        # Should have passed the location category
        assert captured_args.get("location_category") == "forest"


class TestMerchantEncounter:
    """Tests for merchant random encounters."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create a basic game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Road": Location("Road", "A dusty road", coordinates=(0, 0)),
            "Town": Location("Town", "A small town", coordinates=(0, 1)),
        }
        return GameState(character, world, "Road")

    def test_merchant_encounter_creates_npc(self, game_state, monkeypatch):
        """Merchant encounter creates talkable NPC at location.

        Spec: Should create NPC with is_merchant=True and shop
        """
        # Mock to trigger merchant encounter
        random_values = [0.05, 0.70]  # trigger=True, type=merchant (0.60-0.85)
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        # Mock random.choice and randint for merchant generation
        monkeypatch.setattr("cli_rpg.random_encounters.random.choice", lambda x: x[0])
        monkeypatch.setattr("cli_rpg.random_encounters.random.randint", lambda a, b: a)

        initial_npc_count = len(game_state.get_current_location().npcs)

        result = check_for_random_encounter(game_state)

        assert result is not None
        assert "[Random Encounter!]" in result
        # Should have added NPC to location
        location = game_state.get_current_location()
        assert len(location.npcs) == initial_npc_count + 1
        # NPC should be a merchant
        new_npc = location.npcs[-1]
        assert new_npc.is_merchant is True
        assert new_npc.shop is not None

    def test_spawn_wandering_merchant(self):
        """Test spawn_wandering_merchant creates valid merchant.

        Spec: Should create NPC with shop containing 2-3 items
        """
        merchant = spawn_wandering_merchant(level=5)

        assert isinstance(merchant, NPC)
        assert merchant.is_merchant is True
        assert merchant.shop is not None
        assert 2 <= len(merchant.shop.inventory) <= 3

        # All shop items should have prices
        for shop_item in merchant.shop.inventory:
            assert shop_item.buy_price > 0


class TestWandererEncounter:
    """Tests for wanderer random encounters."""

    @pytest.fixture
    def game_state(self, monkeypatch):
        """Create a basic game state for testing."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Road": Location("Road", "A dusty road", coordinates=(0, 0)),
            "Town": Location("Town", "A small town", coordinates=(0, 1)),
        }
        return GameState(character, world, "Road", theme="fantasy")

    def test_wanderer_encounter_creates_npc(self, game_state, monkeypatch):
        """Wanderer encounter creates NPC at location.

        Spec: Should create NPC with atmospheric dialogue at location
        """
        # Mock to trigger wanderer encounter
        random_values = [0.05, 0.90]  # trigger=True, type=wanderer (> 0.85)
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        # Mock random.choice for wanderer generation
        monkeypatch.setattr("cli_rpg.random_encounters.random.choice", lambda x: x[0])

        initial_npc_count = len(game_state.get_current_location().npcs)

        result = check_for_random_encounter(game_state)

        assert result is not None
        assert "[Random Encounter!]" in result
        # Should have added NPC to location
        location = game_state.get_current_location()
        assert len(location.npcs) == initial_npc_count + 1
        # NPC should NOT be a merchant
        new_npc = location.npcs[-1]
        assert new_npc.is_merchant is False

    def test_spawn_wanderer(self):
        """Test spawn_wanderer creates valid wanderer NPC.

        Spec: Should create NPC with lore/atmospheric dialogue
        """
        wanderer = spawn_wanderer(theme="fantasy")

        assert isinstance(wanderer, NPC)
        assert wanderer.is_merchant is False
        assert len(wanderer.dialogue) > 0
        assert len(wanderer.description) > 0


class TestEncounterMessageFormat:
    """Tests for encounter message formatting."""

    def test_encounter_message_format(self):
        """Verify output includes [Random Encounter!] marker.

        Spec: All encounter messages should have the marker
        """
        enemy = Enemy(
            name="Wolf", health=30, max_health=30,
            attack_power=5, defense=2, xp_reward=20
        )
        encounter = RandomEncounter(
            encounter_type="hostile",
            entity=enemy,
            description="A wolf attacks!"
        )

        message = format_encounter_message(encounter)

        assert "[Random Encounter!]" in message
        assert "A wolf attacks!" in message

    def test_merchant_message_includes_talk_hint(self):
        """Merchant messages should include talk hint.

        Spec: Should show (Use 'talk <name>' to interact)
        """
        npc = NPC(
            name="Traveling Merchant",
            description="A merchant with wares",
            dialogue="Want to trade?"
        )
        encounter = RandomEncounter(
            encounter_type="merchant",
            entity=npc,
            description="A merchant appears!"
        )

        message = format_encounter_message(encounter)

        assert "talk" in message.lower()
        assert npc.name in message

    def test_wanderer_message_includes_talk_hint(self):
        """Wanderer messages should include talk hint.

        Spec: Should show (Use 'talk <name>' to interact)
        """
        npc = NPC(
            name="Weary Traveler",
            description="A tired wanderer",
            dialogue="Dark times..."
        )
        encounter = RandomEncounter(
            encounter_type="wanderer",
            entity=npc,
            description="You meet a wanderer."
        )

        message = format_encounter_message(encounter)

        assert "talk" in message.lower()
        assert npc.name in message


class TestSelectEncounterType:
    """Tests for encounter type selection."""

    def test_select_encounter_type_hostile(self):
        """Test hostile selection when roll < 0.60.

        Spec: 60% chance for hostile
        """
        with patch("cli_rpg.random_encounters.random.random", return_value=0.30):
            result = _select_encounter_type()
            assert result == "hostile"

    def test_select_encounter_type_merchant(self):
        """Test merchant selection when 0.60 <= roll < 0.85.

        Spec: 25% chance for merchant
        """
        with patch("cli_rpg.random_encounters.random.random", return_value=0.70):
            result = _select_encounter_type()
            assert result == "merchant"

    def test_select_encounter_type_wanderer(self):
        """Test wanderer selection when roll >= 0.85.

        Spec: 15% chance for wanderer
        """
        with patch("cli_rpg.random_encounters.random.random", return_value=0.90):
            result = _select_encounter_type()
            assert result == "wanderer"


class TestSafeZoneEncounters:
    """Tests for safe zone encounter behavior."""

    @pytest.fixture
    def game_state_with_safe_zone(self, monkeypatch):
        """Create game state with a safe zone location."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location(
                "Town Square", "A safe town square",
                coordinates=(0, 0), is_safe_zone=True
            ),
            "Road": Location(
                "Road", "A dangerous road",
                coordinates=(0, 1), is_safe_zone=False
            ),
        }
        return GameState(character, world, "Town")

    def test_no_encounter_in_safe_zone(self, game_state_with_safe_zone, monkeypatch):
        """No random encounters in safe zones.

        Spec: is_safe_zone=True prevents all random encounters
        """
        # Mock random to always trigger encounter (if not blocked)
        mock_random = MagicMock(return_value=0.05)  # Would trigger encounter
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        result = check_for_random_encounter(game_state_with_safe_zone)

        # Should be None because we're in a safe zone
        assert result is None
        assert not game_state_with_safe_zone.is_in_combat()

    def test_encounter_allowed_in_non_safe_zone(self, game_state_with_safe_zone, monkeypatch):
        """Random encounters work in non-safe zones.

        Spec: is_safe_zone=False allows normal encounter behavior
        """
        # Move to the dangerous road first
        game_state_with_safe_zone.current_location = "Road"

        # Mock to trigger hostile encounter
        random_values = [0.05, 0.30]  # trigger=True, type=hostile
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)
        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])
        monkeypatch.setattr("cli_rpg.combat.random.randint", lambda a, b: a)

        result = check_for_random_encounter(game_state_with_safe_zone)

        # Should trigger encounter in non-safe zone
        assert result is not None
        assert "[Random Encounter!]" in result


class TestTerrainAwareEncounters:
    """Tests for terrain-aware random encounters.

    Spec: Hostile encounters should spawn enemies appropriate to the terrain
    Priority: location.terrain (WFC-generated) > location.category (semantic) > location name matching
    """

    @pytest.fixture
    def game_state_with_terrain(self, monkeypatch):
        """Create game state with terrain-typed location."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Desert": Location(
                "Sandy Wastes", "Hot desert",
                coordinates=(0, 0), terrain="desert"
            ),
        }
        return GameState(character, world, "Desert")

    def test_hostile_encounter_uses_terrain_for_enemy(self, game_state_with_terrain, monkeypatch):
        """Hostile encounters spawn terrain-appropriate enemies.

        Spec: When location.terrain is set, spawn_enemy should receive it as terrain_type
        """
        # Mock to trigger hostile encounter
        random_values = [0.05, 0.30]  # trigger=True, type=hostile
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        captured_args = {}

        def mock_spawn_enemy(location_name, level, location_category=None, terrain_type=None, distance=0):
            captured_args["terrain_type"] = terrain_type
            captured_args["location_category"] = location_category
            return Enemy(
                name="Scorpion", health=30, max_health=30,
                attack_power=5, defense=2, xp_reward=20
            )

        monkeypatch.setattr("cli_rpg.random_encounters.spawn_enemy", mock_spawn_enemy)
        check_for_random_encounter(game_state_with_terrain)

        assert captured_args.get("terrain_type") == "desert"

    def test_terrain_takes_priority_over_category(self, monkeypatch):
        """Terrain type should override location category.

        Spec: terrain_type > location_category in spawn_enemy
        """
        from cli_rpg.combat import spawn_enemy, ENEMY_TEMPLATES

        # Spawn with both terrain and category (terrain wins)
        # Mock random.choice to return first item in the list
        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])

        enemy = spawn_enemy(
            location_name="Test",
            level=1,
            location_category="forest",
            terrain_type="desert",
        )
        # Desert enemies include Scorpion, Sand Serpent, etc. (not forest enemies)
        assert enemy.name in ENEMY_TEMPLATES["desert"]

    def test_category_used_when_no_terrain(self, monkeypatch):
        """Location category should be used when terrain is not set.

        Spec: Falls back to category when terrain_type is None
        """
        from cli_rpg.combat import spawn_enemy, ENEMY_TEMPLATES

        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])

        enemy = spawn_enemy(
            location_name="Test",
            level=1,
            location_category="forest",
            terrain_type=None,
        )
        assert enemy.name in ENEMY_TEMPLATES["forest"]

    def test_new_terrain_types_have_templates(self):
        """New terrain types should have enemy templates.

        Spec: plains, desert, swamp, hills, beach, foothills all have templates
        """
        from cli_rpg.combat import ENEMY_TEMPLATES

        expected_terrains = ["plains", "desert", "swamp", "hills", "beach", "foothills"]
        for terrain in expected_terrains:
            assert terrain in ENEMY_TEMPLATES, f"Missing template for {terrain}"
            assert len(ENEMY_TEMPLATES[terrain]) >= 4, f"{terrain} should have at least 4 enemies"


class TestCategorySpecificEncounters:
    """Tests for Issue 21: Location-specific random encounters.

    Spec: Encounter rates and hostile spawns vary by location category
    """

    @pytest.fixture
    def dungeon_game_state(self, monkeypatch):
        """Create game state in a dungeon location."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Dungeon": Location(
                "Dark Dungeon", "A dangerous dungeon",
                coordinates=(0, 0), category="dungeon"
            ),
            "Dungeon2": Location(
                "Dungeon Deeper", "Deeper into the dungeon",
                coordinates=(0, 1), category="dungeon"
            ),
        }
        return GameState(character, world, "Dungeon")

    @pytest.fixture
    def forest_game_state(self, monkeypatch):
        """Create game state in a forest location."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Forest": Location(
                "Dark Forest", "A shadowy forest",
                coordinates=(0, 0), category="forest"
            ),
            "Forest2": Location(
                "Forest Clearing", "A forest clearing",
                coordinates=(0, 1), category="forest"
            ),
        }
        return GameState(character, world, "Forest")

    def test_encounter_rate_uses_category(self, dungeon_game_state, monkeypatch):
        """Encounter rate varies by location category.

        Spec: Dungeons should use higher encounter rate (0.25) vs forest (0.15)
        """
        from cli_rpg.encounter_tables import CATEGORY_ENCOUNTER_RATES, DEFAULT_ENCOUNTER_RATE

        # Verify dungeon has higher rate
        dungeon_rate = CATEGORY_ENCOUNTER_RATES.get("dungeon", DEFAULT_ENCOUNTER_RATE)
        forest_rate = CATEGORY_ENCOUNTER_RATES.get("forest", DEFAULT_ENCOUNTER_RATE)
        assert dungeon_rate > forest_rate

    def test_dungeon_triggers_more_encounters(self, dungeon_game_state, forest_game_state, monkeypatch):
        """Dungeon locations trigger more encounters than forest.

        Spec: Higher rate categories should have more encounters statistically
        """
        from cli_rpg.encounter_tables import get_encounter_rate

        # Check the rates are different
        dungeon_rate = get_encounter_rate("dungeon")
        forest_rate = get_encounter_rate("forest")

        assert dungeon_rate > forest_rate
        assert dungeon_rate == 0.25  # Dungeon rate from spec
        assert forest_rate == 0.15  # Default/forest rate

    def test_check_for_random_encounter_uses_category_rate(self, dungeon_game_state, monkeypatch):
        """check_for_random_encounter uses category-specific encounter rate.

        Spec: Roll should be against category rate, not global RANDOM_ENCOUNTER_CHANCE
        """
        # With rate=0.25 for dungeon, a roll of 0.20 should trigger (0.20 <= 0.25)
        # But with default rate=0.15, it would NOT trigger (0.20 > 0.15)
        random_values = [0.20, 0.30]  # First triggers encounter check, second selects hostile
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)
        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])
        monkeypatch.setattr("cli_rpg.combat.random.randint", lambda a, b: a)

        result = check_for_random_encounter(dungeon_game_state)

        # Should trigger because 0.20 <= 0.25 (dungeon rate)
        assert result is not None
        assert "[Random Encounter!]" in result

    def test_no_encounter_when_roll_exceeds_category_rate(self, forest_game_state, monkeypatch):
        """No encounter when roll exceeds category rate.

        Spec: Roll of 0.20 should NOT trigger in forest (rate=0.15)
        """
        # With rate=0.15 for forest, a roll of 0.20 should NOT trigger
        mock_random = MagicMock(return_value=0.20)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        result = check_for_random_encounter(forest_game_state)

        # Should NOT trigger because 0.20 > 0.15 (forest rate)
        assert result is None
