"""Tests for secret discovery rewards system.

Tests the tangible rewards players receive when discovering secrets via the search command.
"""
import pytest
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.secrets import perform_active_search, apply_secret_rewards


class TestHiddenTreasureRewards:
    """Test hidden_treasure secret type rewards."""

    def test_hidden_treasure_grants_gold(self):
        """Discovering hidden_treasure adds gold to character."""
        # Spec: hidden_treasure adds 10-50 gold
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(name="Cave", description="A dark cave.")
        secret = {
            "type": "hidden_treasure",
            "description": "A hidden chest",
            "threshold": 12,
            "reward_gold": 25,
        }

        initial_gold = char.gold
        success, message = apply_secret_rewards(char, location, secret)

        assert success
        assert char.gold == initial_gold + 25
        assert "25 gold" in message.lower()

    def test_hidden_treasure_grants_item(self):
        """Discovering hidden_treasure adds item to inventory."""
        # Spec: hidden_treasure grants 1 random item
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(name="Cave", description="A dark cave.")
        secret = {
            "type": "hidden_treasure",
            "description": "A hidden chest",
            "threshold": 12,
            "reward_item": "Health Potion",
        }

        initial_count = len(char.inventory.items)
        success, message = apply_secret_rewards(char, location, secret)

        assert success
        assert len(char.inventory.items) == initial_count + 1
        assert any(item.name == "Health Potion" for item in char.inventory.items)
        assert "Health Potion" in message

    def test_hidden_treasure_grants_both_gold_and_item(self):
        """Hidden treasure can grant both gold and item."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(name="Cave", description="A dark cave.")
        secret = {
            "type": "hidden_treasure",
            "description": "A hidden chest",
            "threshold": 12,
            "reward_gold": 30,
            "reward_item": "Dagger",
        }

        initial_gold = char.gold
        initial_count = len(char.inventory.items)
        success, message = apply_secret_rewards(char, location, secret)

        assert success
        assert char.gold == initial_gold + 30
        assert len(char.inventory.items) == initial_count + 1
        assert "30 gold" in message.lower()
        assert "Dagger" in message


class TestTrapSecretRewards:
    """Test trap secret type rewards."""

    def test_trap_triggers_damage_on_low_dex(self):
        """Trap deals damage when DEX < 12."""
        # Spec: Trap deals 5-15 damage if triggered (DEX < 12)
        char = Character(name="Hero", strength=10, dexterity=8, intelligence=10, perception=15)
        location = Location(name="Hall", description="A long hall.")
        secret = {
            "type": "trap",
            "description": "Pressure plate",
            "threshold": 12,
            "trap_damage": 10,
        }

        initial_health = char.health
        success, message = apply_secret_rewards(char, location, secret)

        assert success  # Success here means "reward applied" (even if it's damage)
        assert char.health == initial_health - 10
        assert "damage" in message.lower() or "triggered" in message.lower()

    def test_trap_disarmed_on_high_dex(self):
        """Trap is disarmed and grants XP when DEX >= 12."""
        # Spec: Trap grants 10 XP if disarmed (DEX >= 12)
        char = Character(name="Hero", strength=10, dexterity=12, intelligence=10, perception=15)
        location = Location(name="Hall", description="A long hall.")
        secret = {
            "type": "trap",
            "description": "Pressure plate",
            "threshold": 12,
            "trap_damage": 10,
        }

        initial_health = char.health
        initial_xp = char.xp
        success, message = apply_secret_rewards(char, location, secret)

        assert success
        assert char.health == initial_health  # No damage taken
        assert char.xp == initial_xp + 10  # XP reward
        assert "disarm" in message.lower()


class TestLoreHintRewards:
    """Test lore_hint secret type rewards."""

    def test_lore_hint_grants_xp(self):
        """Discovering lore_hint grants small XP reward."""
        # Spec: lore_hint grants 5 XP
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(name="Library", description="Ancient texts.")
        secret = {
            "type": "lore_hint",
            "description": "Ancient inscription about the Shadow Lord",
            "threshold": 12,
        }

        initial_xp = char.xp
        success, message = apply_secret_rewards(char, location, secret)

        assert success
        assert char.xp == initial_xp + 5
        assert "xp" in message.lower() or "discover" in message.lower()


class TestHiddenDoorRewards:
    """Test hidden_door secret type rewards."""

    def test_hidden_door_reveals_exit(self):
        """Discovering hidden_door adds new exit direction."""
        # Spec: hidden_door reveals new exit at current location
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(name="Room", description="A small room.")
        secret = {
            "type": "hidden_door",
            "description": "A concealed passage",
            "threshold": 12,
            "exit_direction": "north",
        }

        initial_exits = list(location.temporary_exits)
        success, message = apply_secret_rewards(char, location, secret)

        assert success
        assert "north" in location.temporary_exits
        assert len(location.temporary_exits) == len(initial_exits) + 1
        assert "passage" in message.lower() or "north" in message.lower()


class TestRewardOnlyAppliedOnce:
    """Test that rewards aren't re-applied."""

    def test_reward_only_applied_once(self):
        """Re-searching doesn't re-grant rewards."""
        # Spec: Rewards only apply once per secret
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(
            name="Cave",
            description="A dark cave.",
            hidden_secrets=[{
                "type": "hidden_treasure",
                "description": "Chest",
                "threshold": 12,
                "reward_gold": 50,
            }]
        )

        # First search - finds treasure and gets gold
        found1, msg1 = perform_active_search(char, location)
        gold_after_first = char.gold
        assert found1
        assert gold_after_first > 0

        # Second search - should not find anything (already discovered)
        found2, msg2 = perform_active_search(char, location)
        assert not found2
        assert char.gold == gold_after_first  # No additional gold


class TestSearchMessageIncludesRewards:
    """Test that search command output includes reward descriptions."""

    def test_search_message_includes_rewards(self):
        """Search output message includes what was gained."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        location = Location(
            name="Cave",
            description="A dark cave.",
            hidden_secrets=[{
                "type": "hidden_treasure",
                "description": "A dusty chest",
                "threshold": 12,
                "reward_gold": 25,
                "reward_item": "Health Potion",
            }]
        )

        found, message = perform_active_search(char, location)

        assert found
        # Message should include both the discovery and what was gained
        assert "dusty chest" in message.lower() or "discover" in message.lower()
        assert "25 gold" in message.lower() or "gold" in message.lower()


class TestTemporaryExitsField:
    """Test Location.temporary_exits field and integration."""

    def test_location_has_temporary_exits_field(self):
        """Location has temporary_exits list that defaults to empty."""
        location = Location(name="Room", description="A room.")
        assert hasattr(location, "temporary_exits")
        assert location.temporary_exits == []

    def test_temporary_exits_serialization(self):
        """temporary_exits are saved and loaded correctly."""
        location = Location(
            name="Room",
            description="A room.",
            temporary_exits=["north", "secret passage"]
        )
        data = location.to_dict()
        loaded = Location.from_dict(data)
        assert loaded.temporary_exits == ["north", "secret passage"]
