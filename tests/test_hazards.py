"""Tests for environmental hazards system (Issue #26).

Tests verify:
- Hazard type definitions and validation
- Individual hazard effects (poison gas, darkness, unstable ground, temperature, flooded)
- Ranger class mitigation for wilderness hazards
- Light source negation of darkness penalty
- Antidote clearing poison effect
- Hazard assignment by location category
- Location serialization with hazards field
"""

import pytest
import random
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character, CharacterClass


class TestHazardTypes:
    """Test hazard type definitions and constants."""

    def test_hazard_types_are_defined(self):
        """Verify all required hazard types are defined."""
        from cli_rpg.hazards import HAZARD_TYPES

        assert "poison_gas" in HAZARD_TYPES
        assert "darkness" in HAZARD_TYPES
        assert "unstable_ground" in HAZARD_TYPES
        assert "extreme_cold" in HAZARD_TYPES
        assert "extreme_heat" in HAZARD_TYPES
        assert "flooded" in HAZARD_TYPES

    def test_category_hazards_mapping(self):
        """Verify hazard pools are defined per location category."""
        from cli_rpg.hazards import CATEGORY_HAZARDS

        # Dungeons get poison_gas, darkness, unstable_ground
        assert "dungeon" in CATEGORY_HAZARDS
        assert "poison_gas" in CATEGORY_HAZARDS["dungeon"]
        assert "darkness" in CATEGORY_HAZARDS["dungeon"]
        assert "unstable_ground" in CATEGORY_HAZARDS["dungeon"]

        # Caves get darkness, flooded, extreme_cold
        assert "cave" in CATEGORY_HAZARDS
        assert "darkness" in CATEGORY_HAZARDS["cave"]
        assert "flooded" in CATEGORY_HAZARDS["cave"]
        assert "extreme_cold" in CATEGORY_HAZARDS["cave"]

        # Ruins get unstable_ground, darkness
        assert "ruins" in CATEGORY_HAZARDS
        assert "unstable_ground" in CATEGORY_HAZARDS["ruins"]
        assert "darkness" in CATEGORY_HAZARDS["ruins"]

        # Temples get poison_gas, darkness
        assert "temple" in CATEGORY_HAZARDS
        assert "poison_gas" in CATEGORY_HAZARDS["temple"]
        assert "darkness" in CATEGORY_HAZARDS["temple"]


class TestPoisonGasHazard:
    """Test poison gas hazard effects."""

    def test_poison_gas_deals_damage(self):
        """Poison gas should deal DOT damage per move."""
        from cli_rpg.hazards import apply_poison_gas

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        initial_health = character.health

        message = apply_poison_gas(character)

        assert character.health < initial_health
        assert "poison" in message.lower() or "gas" in message.lower()

    def test_poison_gas_damage_amount(self):
        """Poison gas should deal 3-6 damage per exposure."""
        from cli_rpg.hazards import apply_poison_gas

        # Run multiple times to check range
        damages = []
        for _ in range(20):
            character = Character(
                name="TestHero",
                strength=10,
                dexterity=10,
                intelligence=10,
                charisma=10,
            )
            initial_health = character.health
            apply_poison_gas(character)
            damage_taken = initial_health - character.health
            damages.append(damage_taken)

        # Check damage is in expected range
        assert all(3 <= d <= 6 for d in damages)


class TestDarknessHazard:
    """Test darkness hazard effects."""

    def test_darkness_reduces_perception(self):
        """Darkness should reduce perception by 50%."""
        from cli_rpg.hazards import check_darkness_penalty

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        # No light source
        character.light_remaining = 0

        penalty = check_darkness_penalty(character)

        assert penalty == 0.5  # 50% reduction

    def test_light_source_negates_darkness(self):
        """Active light source should negate darkness penalty."""
        from cli_rpg.hazards import check_darkness_penalty

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        # Has active light source
        character.light_remaining = 5

        penalty = check_darkness_penalty(character)

        assert penalty == 1.0  # No penalty


class TestUnstableGroundHazard:
    """Test unstable ground hazard effects."""

    def test_unstable_ground_dex_check(self):
        """Unstable ground should use DEX check to avoid fall damage."""
        from cli_rpg.hazards import check_unstable_ground

        # High DEX character should rarely fall
        high_dex = Character(
            name="AgileHero",
            strength=10,
            dexterity=18,
            intelligence=10,
            charisma=10,
        )

        # Low DEX character should fall more often
        low_dex = Character(
            name="ClumsiHero",
            strength=10,
            dexterity=5,
            intelligence=10,
            charisma=10,
        )

        # Run multiple times to check statistical tendency
        high_dex_falls = 0
        low_dex_falls = 0
        random.seed(42)

        for _ in range(100):
            fell, _ = check_unstable_ground(high_dex)
            if fell:
                high_dex_falls += 1

            fell, _ = check_unstable_ground(low_dex)
            if fell:
                low_dex_falls += 1

        # Low DEX should fall more often than high DEX
        assert low_dex_falls > high_dex_falls

    def test_unstable_ground_fall_damage_range(self):
        """Fall damage should be 5-15 HP."""
        from cli_rpg.hazards import check_unstable_ground

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=5,  # Low DEX to ensure falls
            intelligence=10,
            charisma=10,
        )

        damages = []
        random.seed(42)
        for _ in range(50):
            fell, damage = check_unstable_ground(character)
            if fell:
                damages.append(damage)

        # Check damage range
        assert len(damages) > 0  # Should have some falls
        assert all(5 <= d <= 15 for d in damages)

    def test_ranger_ignores_unstable_ground(self):
        """Ranger class should ignore unstable ground hazard."""
        from cli_rpg.hazards import can_mitigate_hazard

        ranger = Character(
            name="RangerHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.RANGER,
        )

        assert can_mitigate_hazard(ranger, "unstable_ground") is True

        # Non-ranger should not mitigate
        warrior = Character(
            name="WarriorHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.WARRIOR,
        )
        assert can_mitigate_hazard(warrior, "unstable_ground") is False


class TestTemperatureHazards:
    """Test extreme cold/heat hazard effects."""

    def test_extreme_cold_adds_tiredness(self):
        """Extreme cold should add +5 tiredness per move."""
        from cli_rpg.hazards import apply_temperature_effect

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        initial_tiredness = character.tiredness.current

        message = apply_temperature_effect(character, "extreme_cold")

        assert character.tiredness.current == initial_tiredness + 5
        assert "cold" in message.lower()

    def test_extreme_heat_adds_tiredness(self):
        """Extreme heat should add +5 tiredness per move."""
        from cli_rpg.hazards import apply_temperature_effect

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        initial_tiredness = character.tiredness.current

        message = apply_temperature_effect(character, "extreme_heat")

        assert character.tiredness.current == initial_tiredness + 5
        assert "heat" in message.lower()

    def test_ranger_ignores_temperature_hazards(self):
        """Ranger class should ignore temperature hazards."""
        from cli_rpg.hazards import can_mitigate_hazard

        ranger = Character(
            name="RangerHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.RANGER,
        )

        assert can_mitigate_hazard(ranger, "extreme_cold") is True
        assert can_mitigate_hazard(ranger, "extreme_heat") is True


class TestFloodedHazard:
    """Test flooded room hazard effects."""

    def test_flooded_movement_failure_chance(self):
        """Flooded rooms should have 50% chance to fail movement."""
        from cli_rpg.hazards import check_flooded_movement

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )

        failures = 0
        random.seed(42)
        for _ in range(100):
            if check_flooded_movement(character):
                failures += 1

        # Should be roughly 50% (allow for variance)
        assert 35 <= failures <= 65

    def test_flooded_no_mitigation(self):
        """Flooded hazard should have no mitigation (even for Ranger)."""
        from cli_rpg.hazards import can_mitigate_hazard

        ranger = Character(
            name="RangerHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.RANGER,
        )

        # Flooded cannot be mitigated
        assert can_mitigate_hazard(ranger, "flooded") is False


class TestHazardMitigation:
    """Test hazard mitigation mechanics."""

    def test_ranger_mitigates_wilderness_hazards(self):
        """Ranger should mitigate unstable_ground and temperature hazards."""
        from cli_rpg.hazards import can_mitigate_hazard

        ranger = Character(
            name="RangerHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.RANGER,
        )

        assert can_mitigate_hazard(ranger, "unstable_ground") is True
        assert can_mitigate_hazard(ranger, "extreme_cold") is True
        assert can_mitigate_hazard(ranger, "extreme_heat") is True

    def test_light_mitigates_darkness(self):
        """Light source should mitigate darkness hazard."""
        from cli_rpg.hazards import can_mitigate_hazard

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )

        # No light - cannot mitigate
        character.light_remaining = 0
        assert can_mitigate_hazard(character, "darkness") is False

        # Has light - can mitigate
        character.light_remaining = 5
        assert can_mitigate_hazard(character, "darkness") is True

    def test_poison_gas_not_mitigatable_by_class(self):
        """Poison gas should not be mitigated by any class."""
        from cli_rpg.hazards import can_mitigate_hazard

        for char_class in CharacterClass:
            character = Character(
                name="TestHero",
                strength=10,
                dexterity=10,
                intelligence=10,
                charisma=10,
                character_class=char_class,
            )
            # Poison gas has no class-based mitigation (requires antidote item use)
            # So can_mitigate_hazard should return False
            assert can_mitigate_hazard(character, "poison_gas") is False


class TestLocationHazardField:
    """Test hazards field on Location model."""

    def test_location_has_hazards_field(self):
        """Location should have a hazards field (default empty list)."""
        location = Location(
            name="Test Location",
            description="A test location.",
        )

        assert hasattr(location, "hazards")
        assert location.hazards == []

    def test_location_with_hazards(self):
        """Location can be created with hazards."""
        location = Location(
            name="Toxic Chamber",
            description="A chamber filled with poisonous gas.",
            hazards=["poison_gas", "darkness"],
        )

        assert location.hazards == ["poison_gas", "darkness"]

    def test_location_hazards_serialization(self):
        """Hazards field should be included in to_dict/from_dict."""
        location = Location(
            name="Flooded Cave",
            description="A cave with rising water levels.",
            hazards=["flooded", "darkness"],
        )

        # Serialize
        data = location.to_dict()
        assert "hazards" in data
        assert data["hazards"] == ["flooded", "darkness"]

        # Deserialize
        restored = Location.from_dict(data)
        assert restored.hazards == ["flooded", "darkness"]

    def test_location_without_hazards_backward_compat(self):
        """Locations without hazards field should deserialize with empty list."""
        # Simulate old save data without hazards field
        data = {
            "name": "Old Location",
            "description": "From an old save file.",
            "npcs": [],
        }

        location = Location.from_dict(data)
        assert location.hazards == []


class TestHazardGeneration:
    """Test hazard generation during SubGrid creation."""

    def test_get_hazards_for_category(self):
        """get_hazards_for_category should return appropriate hazards."""
        from cli_rpg.hazards import get_hazards_for_category

        # Dungeons should get dungeon-appropriate hazards
        hazards = get_hazards_for_category("dungeon", distance=2)
        # Should be a list of 0-2 hazards from dungeon pool
        assert isinstance(hazards, list)
        # All returned hazards should be from dungeon pool
        from cli_rpg.hazards import CATEGORY_HAZARDS
        for h in hazards:
            assert h in CATEGORY_HAZARDS["dungeon"]

    def test_hazard_chance_increases_with_distance(self):
        """Deeper rooms should have higher hazard chance."""
        from cli_rpg.hazards import get_hazards_for_category

        # Run many times and check that deeper rooms get more hazards
        close_hazard_count = 0
        far_hazard_count = 0

        random.seed(42)
        for _ in range(100):
            close_hazards = get_hazards_for_category("dungeon", distance=1)
            far_hazards = get_hazards_for_category("dungeon", distance=5)
            close_hazard_count += len(close_hazards)
            far_hazard_count += len(far_hazards)

        # Far rooms should have more total hazards
        assert far_hazard_count > close_hazard_count

    def test_unknown_category_returns_empty(self):
        """Unknown categories should return empty hazard list."""
        from cli_rpg.hazards import get_hazards_for_category

        hazards = get_hazards_for_category("town", distance=5)
        assert hazards == []

        hazards = get_hazards_for_category("unknown_category", distance=5)
        assert hazards == []


class TestCheckHazardsOnEntry:
    """Test the main hazard processing function."""

    def test_check_hazards_returns_messages(self):
        """check_hazards_on_entry should return list of effect messages."""
        from cli_rpg.hazards import check_hazards_on_entry
        from cli_rpg.game_state import GameState
        from cli_rpg.world import create_default_world

        world, start = create_default_world()
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        game_state = GameState(character, world, start)

        # Create location with poison gas hazard
        location = Location(
            name="Toxic Room",
            description="A room filled with noxious fumes.",
            hazards=["poison_gas"],
        )

        initial_health = character.health
        messages = check_hazards_on_entry(game_state, location)

        assert isinstance(messages, list)
        assert len(messages) > 0
        assert character.health < initial_health  # Took poison damage

    def test_check_hazards_with_mitigation(self):
        """Mitigated hazards should not apply effects."""
        from cli_rpg.hazards import check_hazards_on_entry
        from cli_rpg.game_state import GameState
        from cli_rpg.world import create_default_world

        world, start = create_default_world()
        # Ranger character for unstable_ground mitigation
        character = Character(
            name="RangerHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.RANGER,
        )
        game_state = GameState(character, world, start)

        # Create location with unstable_ground hazard (Ranger ignores this)
        location = Location(
            name="Crumbling Floor",
            description="The floor here is unstable.",
            hazards=["unstable_ground"],
        )

        initial_health = character.health
        messages = check_hazards_on_entry(game_state, location)

        # Ranger should have mitigated - no damage taken
        assert character.health == initial_health
        # Should have a mitigation message
        assert any("ranger" in m.lower() or "ignore" in m.lower() or "avoid" in m.lower() for m in messages)

    def test_check_hazards_empty_list_for_no_hazards(self):
        """Locations without hazards should return empty message list."""
        from cli_rpg.hazards import check_hazards_on_entry
        from cli_rpg.game_state import GameState
        from cli_rpg.world import create_default_world

        world, start = create_default_world()
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        game_state = GameState(character, world, start)

        # Location without hazards
        location = Location(
            name="Safe Room",
            description="A safe, comfortable room.",
            hazards=[],
        )

        messages = check_hazards_on_entry(game_state, location)
        assert messages == []
