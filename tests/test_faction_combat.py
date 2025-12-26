"""Tests for faction reputation consequences in combat.

Spec: Wire faction reputation changes into combat outcomes. When the player defeats
enemies affiliated with a faction, their reputation with that faction decreases,
while reputation with opposing factions increases.
"""

import pytest

from cli_rpg.models.enemy import Enemy
from cli_rpg.models.faction import Faction
from cli_rpg.models.character import Character
from cli_rpg.faction_combat import (
    get_enemy_faction,
    apply_combat_reputation,
    FACTION_REPUTATION_LOSS,
    FACTION_REPUTATION_GAIN,
)


class TestEnemyFactionAffiliation:
    """Tests for Enemy.faction_affiliation field."""

    def test_enemy_faction_affiliation_default_none(self):
        """Enemy has no faction by default."""
        # Spec: faction_affiliation defaults to None
        enemy = Enemy(
            name="Goblin",
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10,
        )
        assert enemy.faction_affiliation is None

    def test_enemy_faction_affiliation_set(self):
        """Can set faction_affiliation on Enemy."""
        # Spec: faction_affiliation can be set to a faction name
        enemy = Enemy(
            name="Bandit",
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10,
            faction_affiliation="Thieves Guild",
        )
        assert enemy.faction_affiliation == "Thieves Guild"

    def test_enemy_faction_affiliation_serialization(self):
        """Faction affiliation persists through to_dict/from_dict."""
        # Spec: faction_affiliation must be serialized/deserialized
        enemy = Enemy(
            name="Guard",
            health=30,
            max_health=30,
            attack_power=8,
            defense=5,
            xp_reward=15,
            faction_affiliation="Town Guard",
        )
        data = enemy.to_dict()
        restored = Enemy.from_dict(data)
        assert restored.faction_affiliation == "Town Guard"

    def test_enemy_faction_affiliation_serialization_none(self):
        """None faction affiliation serializes correctly."""
        enemy = Enemy(
            name="Goblin",
            health=20,
            max_health=20,
            attack_power=5,
            defense=2,
            xp_reward=10,
        )
        data = enemy.to_dict()
        restored = Enemy.from_dict(data)
        assert restored.faction_affiliation is None


class TestFactionEnemyMapping:
    """Tests for get_enemy_faction() mapping function."""

    def test_get_enemy_faction_bandit(self):
        """Returns 'Thieves Guild' for bandit-type enemies."""
        # Spec: Bandit, Thief, Ruffian, Outlaw -> Thieves Guild
        assert get_enemy_faction("Bandit") == "Thieves Guild"
        assert get_enemy_faction("Thief") == "Thieves Guild"
        assert get_enemy_faction("Ruffian") == "Thieves Guild"
        assert get_enemy_faction("Outlaw") == "Thieves Guild"
        # Case insensitive
        assert get_enemy_faction("bandit") == "Thieves Guild"
        assert get_enemy_faction("BANDIT") == "Thieves Guild"
        # Partial matches in name
        assert get_enemy_faction("Forest Bandit") == "Thieves Guild"
        assert get_enemy_faction("Bandit Leader") == "Thieves Guild"

    def test_get_enemy_faction_guard(self):
        """Returns 'Town Guard' for guard-type enemies."""
        # Spec: Guard, Soldier, Knight, Captain -> Town Guard
        assert get_enemy_faction("Guard") == "Town Guard"
        assert get_enemy_faction("Soldier") == "Town Guard"
        assert get_enemy_faction("Knight") == "Town Guard"
        assert get_enemy_faction("Captain") == "Town Guard"
        # Case insensitive
        assert get_enemy_faction("guard") == "Town Guard"
        assert get_enemy_faction("GUARD") == "Town Guard"
        # Partial matches in name
        assert get_enemy_faction("Palace Guard") == "Town Guard"
        assert get_enemy_faction("Elite Knight") == "Town Guard"

    def test_get_enemy_faction_none(self):
        """Returns None for unaffiliated enemies."""
        # Spec: Unaffiliated enemies like "Goblin" return None
        assert get_enemy_faction("Goblin") is None
        assert get_enemy_faction("Spider") is None
        assert get_enemy_faction("Skeleton") is None
        assert get_enemy_faction("Dragon") is None


class TestCombatReputationChanges:
    """Tests for apply_combat_reputation() function."""

    def _create_test_character(self) -> Character:
        """Create a test character for combat tests."""
        return Character(
            name="TestHero",
            health=100,
            max_health=100,
            strength=10,
            defense=10,
            intelligence=10,
            agility=10,
            luck=10,
            perception=10,
            charisma=10,
            level=1,
            xp=0,
            xp_to_next_level=100,
            gold=0,
        )

    def _create_test_factions(self) -> list[Faction]:
        """Create test factions with default reputation (50)."""
        return [
            Faction(name="Thieves Guild", description="A guild of thieves"),
            Faction(name="Town Guard", description="The town's guard"),
        ]

    def test_combat_victory_reduces_faction_rep(self):
        """Killing bandit reduces Thieves Guild rep by 5."""
        # Spec: Kill affiliated enemy: -5 reputation with that faction
        factions = self._create_test_factions()
        thieves_guild = factions[0]
        initial_rep = thieves_guild.reputation

        enemies = [
            Enemy(
                name="Bandit",
                health=0,  # Dead enemy
                max_health=20,
                attack_power=5,
                defense=2,
                xp_reward=10,
                faction_affiliation="Thieves Guild",
            )
        ]

        messages = apply_combat_reputation(factions, enemies)

        assert thieves_guild.reputation == initial_rep - FACTION_REPUTATION_LOSS
        assert any("Thieves Guild" in msg for msg in messages)

    def test_combat_victory_increases_rival_rep(self):
        """Killing bandit increases Town Guard rep by 3."""
        # Spec: Kill affiliated enemy: +3 reputation with opposing faction
        factions = self._create_test_factions()
        town_guard = factions[1]
        initial_rep = town_guard.reputation

        enemies = [
            Enemy(
                name="Bandit",
                health=0,
                max_health=20,
                attack_power=5,
                defense=2,
                xp_reward=10,
                faction_affiliation="Thieves Guild",
            )
        ]

        messages = apply_combat_reputation(factions, enemies)

        assert town_guard.reputation == initial_rep + FACTION_REPUTATION_GAIN
        assert any("Town Guard" in msg for msg in messages)

    def test_combat_victory_no_faction_no_rep_change(self):
        """Killing unaffiliated enemy has no effect on faction rep."""
        # Spec: Unaffiliated enemies don't affect reputation
        factions = self._create_test_factions()
        initial_thieves_rep = factions[0].reputation
        initial_guard_rep = factions[1].reputation

        enemies = [
            Enemy(
                name="Goblin",
                health=0,
                max_health=20,
                attack_power=5,
                defense=2,
                xp_reward=10,
            )
        ]

        messages = apply_combat_reputation(factions, enemies)

        assert factions[0].reputation == initial_thieves_rep
        assert factions[1].reputation == initial_guard_rep
        assert len(messages) == 0

    def test_combat_victory_displays_rep_messages(self):
        """Victory message includes rep change info."""
        # Spec: Display reputation change messages to player
        factions = self._create_test_factions()

        enemies = [
            Enemy(
                name="Guard",
                health=0,
                max_health=30,
                attack_power=8,
                defense=5,
                xp_reward=15,
                faction_affiliation="Town Guard",
            )
        ]

        messages = apply_combat_reputation(factions, enemies)

        # Should have messages about both factions
        assert len(messages) >= 1
        # Check message content indicates reputation changes
        assert any("-" in msg or "decreased" in msg.lower() for msg in messages)

    def test_combat_victory_multiple_enemies(self):
        """Each affiliated enemy contributes rep changes."""
        # Spec: Multiple enemies each affect reputation
        factions = self._create_test_factions()
        thieves_guild = factions[0]
        town_guard = factions[1]
        initial_thieves_rep = thieves_guild.reputation
        initial_guard_rep = town_guard.reputation

        enemies = [
            Enemy(
                name="Bandit",
                health=0,
                max_health=20,
                attack_power=5,
                defense=2,
                xp_reward=10,
                faction_affiliation="Thieves Guild",
            ),
            Enemy(
                name="Thief",
                health=0,
                max_health=15,
                attack_power=4,
                defense=2,
                xp_reward=8,
                faction_affiliation="Thieves Guild",
            ),
        ]

        messages = apply_combat_reputation(factions, enemies)

        # Each bandit/thief should reduce Thieves Guild rep by 5
        assert thieves_guild.reputation == initial_thieves_rep - (2 * FACTION_REPUTATION_LOSS)
        # Each should increase Town Guard rep by 3
        assert town_guard.reputation == initial_guard_rep + (2 * FACTION_REPUTATION_GAIN)

    def test_combat_victory_mixed_enemies(self):
        """Mixed affiliated and unaffiliated enemies are handled correctly."""
        factions = self._create_test_factions()
        thieves_guild = factions[0]
        initial_rep = thieves_guild.reputation

        enemies = [
            Enemy(
                name="Bandit",
                health=0,
                max_health=20,
                attack_power=5,
                defense=2,
                xp_reward=10,
                faction_affiliation="Thieves Guild",
            ),
            Enemy(
                name="Goblin",
                health=0,
                max_health=15,
                attack_power=4,
                defense=2,
                xp_reward=8,
            ),
        ]

        apply_combat_reputation(factions, enemies)

        # Only the bandit should affect reputation
        assert thieves_guild.reputation == initial_rep - FACTION_REPUTATION_LOSS

    def test_combat_reputation_unknown_faction(self):
        """Enemies with unknown faction affiliations are handled gracefully."""
        factions = self._create_test_factions()
        initial_thieves_rep = factions[0].reputation
        initial_guard_rep = factions[1].reputation

        enemies = [
            Enemy(
                name="Mysterious Cultist",
                health=0,
                max_health=25,
                attack_power=6,
                defense=3,
                xp_reward=12,
                faction_affiliation="Dark Cult",  # Unknown faction
            )
        ]

        messages = apply_combat_reputation(factions, enemies)

        # No faction change for unknown factions
        assert factions[0].reputation == initial_thieves_rep
        assert factions[1].reputation == initial_guard_rep
        assert len(messages) == 0
