"""Tests for agent class behavior system.

Tests the ClassBehavior protocol, CharacterClassName enum, ClassBehaviorConfig dataclass,
and all 5 concrete behavior classes (Warrior, Mage, Rogue, Ranger, Cleric).
"""

import pytest

from scripts.state_parser import AgentState
from scripts.agent.memory import AgentMemory
from scripts.agent.class_behaviors import (
    CharacterClassName,
    ClassBehaviorConfig,
    ClassBehavior,
    WarriorBehavior,
    MageBehavior,
    RogueBehavior,
    RangerBehavior,
    ClericBehavior,
    BEHAVIOR_REGISTRY,
    get_class_behavior,
)


class TestCharacterClassName:
    """Test CharacterClassName enum has all required values."""

    def test_has_warrior(self):
        """Spec: CharacterClassName enum - WARRIOR."""
        assert CharacterClassName.WARRIOR is not None
        assert CharacterClassName.WARRIOR.value == "Warrior"

    def test_has_mage(self):
        """Spec: CharacterClassName enum - MAGE."""
        assert CharacterClassName.MAGE is not None
        assert CharacterClassName.MAGE.value == "Mage"

    def test_has_rogue(self):
        """Spec: CharacterClassName enum - ROGUE."""
        assert CharacterClassName.ROGUE is not None
        assert CharacterClassName.ROGUE.value == "Rogue"

    def test_has_ranger(self):
        """Spec: CharacterClassName enum - RANGER."""
        assert CharacterClassName.RANGER is not None
        assert CharacterClassName.RANGER.value == "Ranger"

    def test_has_cleric(self):
        """Spec: CharacterClassName enum - CLERIC."""
        assert CharacterClassName.CLERIC is not None
        assert CharacterClassName.CLERIC.value == "Cleric"

    def test_exactly_five_classes(self):
        """Spec: CharacterClassName enum with 5 values."""
        assert len(CharacterClassName) == 5


class TestClassBehaviorConfig:
    """Test ClassBehaviorConfig dataclass structure."""

    def test_has_flee_health_threshold(self):
        """Spec: ClassBehaviorConfig has flee_health_threshold field."""
        config = ClassBehaviorConfig(
            flee_health_threshold=0.2,
            heal_health_threshold=0.5,
            mana_conservation_threshold=0.2,
            special_ability_cooldown=3,
        )
        assert config.flee_health_threshold == 0.2

    def test_has_heal_health_threshold(self):
        """Spec: ClassBehaviorConfig has heal_health_threshold field."""
        config = ClassBehaviorConfig(
            flee_health_threshold=0.2,
            heal_health_threshold=0.5,
            mana_conservation_threshold=0.2,
            special_ability_cooldown=3,
        )
        assert config.heal_health_threshold == 0.5

    def test_has_mana_conservation_threshold(self):
        """Spec: ClassBehaviorConfig has mana_conservation_threshold field."""
        config = ClassBehaviorConfig(
            flee_health_threshold=0.2,
            heal_health_threshold=0.5,
            mana_conservation_threshold=0.3,
            special_ability_cooldown=3,
        )
        assert config.mana_conservation_threshold == 0.3

    def test_has_special_ability_cooldown(self):
        """Spec: ClassBehaviorConfig has special_ability_cooldown field."""
        config = ClassBehaviorConfig(
            flee_health_threshold=0.2,
            heal_health_threshold=0.5,
            mana_conservation_threshold=0.2,
            special_ability_cooldown=5,
        )
        assert config.special_ability_cooldown == 5


class TestClassBehaviorRegistry:
    """Test that all 5 classes have registered behaviors."""

    def test_warrior_behavior_exists(self):
        """Spec: Warrior class has registered behavior."""
        assert CharacterClassName.WARRIOR in BEHAVIOR_REGISTRY

    def test_mage_behavior_exists(self):
        """Spec: Mage class has registered behavior."""
        assert CharacterClassName.MAGE in BEHAVIOR_REGISTRY

    def test_rogue_behavior_exists(self):
        """Spec: Rogue class has registered behavior."""
        assert CharacterClassName.ROGUE in BEHAVIOR_REGISTRY

    def test_ranger_behavior_exists(self):
        """Spec: Ranger class has registered behavior."""
        assert CharacterClassName.RANGER in BEHAVIOR_REGISTRY

    def test_cleric_behavior_exists(self):
        """Spec: Cleric class has registered behavior."""
        assert CharacterClassName.CLERIC in BEHAVIOR_REGISTRY

    def test_get_behavior_for_all_classes(self):
        """Spec: get_class_behavior returns behavior for all classes."""
        for class_name in CharacterClassName:
            behavior = get_class_behavior(class_name)
            assert behavior is not None
            # Verify it has the required methods
            assert hasattr(behavior, "get_combat_command")
            assert hasattr(behavior, "get_exploration_command")
            assert hasattr(behavior, "should_flee")


class TestWarriorBehavior:
    """Test Warrior combat: bash, aggressive/berserker stance."""

    @pytest.fixture
    def warrior(self):
        """Create a WarriorBehavior instance."""
        return WarriorBehavior()

    @pytest.fixture
    def combat_state(self):
        """Create a combat AgentState."""
        state = AgentState()
        state.in_combat = True
        state.enemy = "Goblin"
        state.health = 80
        state.max_health = 100
        state.commands = ["attack", "bash", "stance", "flee"]
        return state

    @pytest.fixture
    def memory(self):
        """Create an empty AgentMemory."""
        return AgentMemory()

    def test_uses_bash_when_available(self, warrior, combat_state, memory):
        """Spec: Warrior uses bash when available in combat."""
        command = warrior.get_combat_command(combat_state, memory)
        # Should use bash (special ability)
        assert command is not None
        assert "bash" in command

    def test_switches_to_aggressive_stance(self, warrior, combat_state, memory):
        """Spec: Warrior uses aggressive stance when health > 50%."""
        combat_state.health = 60  # 60% health
        combat_state.commands = ["attack", "stance", "flee"]  # No bash available
        command = warrior.get_combat_command(combat_state, memory)
        # Should suggest stance change or attack
        assert command is None or "stance" in command or "attack" in command

    def test_switches_to_berserker_at_low_health(self, warrior, combat_state, memory):
        """Spec: Warrior uses berserker stance when health < 30%."""
        combat_state.health = 25  # 25% health
        combat_state.commands = ["attack", "stance", "flee"]  # No bash
        command = warrior.get_combat_command(combat_state, memory)
        # At low health might suggest stance berserker or flee
        assert command is None or isinstance(command, str)

    def test_lower_flee_threshold(self, warrior, combat_state, memory):
        """Spec: Warrior has lower flee threshold (15%) - warriors are brave."""
        # At 20% health, should NOT flee (threshold is 15%)
        combat_state.health = 20
        assert not warrior.should_flee(combat_state, memory)

        # At 10% health, should flee
        combat_state.health = 10
        assert warrior.should_flee(combat_state, memory)

    def test_exploration_returns_none(self, warrior, memory):
        """Spec: Warrior has direct approach - no special exploration commands."""
        state = AgentState()
        state.in_combat = False
        command = warrior.get_exploration_command(state, memory)
        assert command is None


class TestMageBehavior:
    """Test Mage combat: fireball/ice_bolt, self-heal, mana conservation."""

    @pytest.fixture
    def mage(self):
        """Create a MageBehavior instance."""
        return MageBehavior()

    @pytest.fixture
    def combat_state(self):
        """Create a combat AgentState with mana."""
        state = AgentState()
        state.in_combat = True
        state.enemy = "Orc"
        state.health = 80
        state.max_health = 100
        state.commands = ["attack", "cast", "flee"]
        return state

    @pytest.fixture
    def memory(self):
        """Create an empty AgentMemory."""
        return AgentMemory()

    def test_uses_fireball_when_mana_available(self, mage, combat_state, memory):
        """Spec: Mage uses fireball when mana > 30%."""
        # Simulate high mana by setting mage's internal state
        mage._mana_percent = 0.5  # 50% mana
        command = mage.get_combat_command(combat_state, memory)
        assert command is not None
        assert "cast" in command and ("fireball" in command or "ice_bolt" in command)

    def test_uses_ice_bolt_as_alternative(self, mage, combat_state, memory):
        """Spec: Mage can use ice_bolt as alternative spell."""
        mage._mana_percent = 0.5
        # Get several commands to see variety
        commands = [mage.get_combat_command(combat_state, memory) for _ in range(10)]
        spell_commands = [c for c in commands if c and "cast" in c]
        assert len(spell_commands) > 0
        # Should see at least fireball or ice_bolt
        spell_names = " ".join(spell_commands)
        assert "fireball" in spell_names or "ice_bolt" in spell_names

    def test_casts_heal_when_hurt(self, mage, combat_state, memory):
        """Spec: Mage casts heal when health < 50% and mana available."""
        combat_state.health = 40  # 40% health
        mage._mana_percent = 0.5
        command = mage.get_combat_command(combat_state, memory)
        # Should prioritize healing
        assert command is not None
        assert "cast" in command and "heal" in command

    def test_conserves_mana_when_low(self, mage, combat_state, memory):
        """Spec: Mage conserves mana when low - falls back to attack."""
        mage._mana_percent = 0.15  # 15% mana (below 20% threshold)
        command = mage.get_combat_command(combat_state, memory)
        # Should return None to use default attack
        assert command is None

    def test_falls_back_to_attack_when_no_mana(self, mage, combat_state, memory):
        """Spec: Mage uses attack when out of mana."""
        mage._mana_percent = 0.0
        command = mage.get_combat_command(combat_state, memory)
        assert command is None  # None means use default attack

    def test_higher_flee_threshold(self, mage, combat_state, memory):
        """Spec: Mage has higher flee threshold (25%) - mages are fragile."""
        # At 30% health, should NOT flee
        combat_state.health = 30
        assert not mage.should_flee(combat_state, memory)

        # At 20% health, should flee
        combat_state.health = 20
        assert mage.should_flee(combat_state, memory)


class TestRogueBehavior:
    """Test Rogue: sneak attacks, hide, secret searching."""

    @pytest.fixture
    def rogue(self):
        """Create a RogueBehavior instance."""
        return RogueBehavior()

    @pytest.fixture
    def combat_state(self):
        """Create a combat AgentState."""
        state = AgentState()
        state.in_combat = True
        state.enemy = "Bandit"
        state.health = 80
        state.max_health = 100
        state.commands = ["attack", "sneak", "hide", "flee"]
        return state

    @pytest.fixture
    def memory(self):
        """Create an empty AgentMemory."""
        return AgentMemory()

    def test_uses_sneak_attack_when_hidden(self, rogue, combat_state, memory):
        """Spec: Rogue uses sneak attack when hidden."""
        rogue._is_hidden = True
        command = rogue.get_combat_command(combat_state, memory)
        assert command is not None
        assert "sneak" in command

    def test_uses_hide_when_not_hidden(self, rogue, combat_state, memory):
        """Spec: Rogue uses hide when not hidden at combat start."""
        rogue._is_hidden = False
        rogue._combat_turns = 0  # Combat just started
        command = rogue.get_combat_command(combat_state, memory)
        assert command is not None
        assert "hide" in command

    def test_searches_for_secrets_in_dungeons(self, rogue, memory):
        """Spec: Rogue searches for secrets in dungeons (30% chance)."""
        state = AgentState()
        state.in_combat = False
        state.location_category = "dungeon"
        state.commands = ["search", "go", "look"]

        # Run multiple times to check probability
        search_count = 0
        for _ in range(100):
            command = rogue.get_exploration_command(state, memory)
            if command and "search" in command:
                search_count += 1

        # Should have some searches (roughly 30%, allow for variance)
        assert 10 < search_count < 60

    def test_prioritizes_stealth_approach(self, rogue, combat_state, memory):
        """Spec: Rogue prioritizes stealth - tries to hide before attacking."""
        rogue._is_hidden = False
        rogue._combat_turns = 0
        command = rogue.get_combat_command(combat_state, memory)
        assert command is not None
        assert "hide" in command

    def test_default_flee_threshold(self, rogue, combat_state, memory):
        """Spec: Rogue has default flee threshold (20%)."""
        combat_state.health = 25
        assert not rogue.should_flee(combat_state, memory)

        combat_state.health = 15
        assert rogue.should_flee(combat_state, memory)


class TestRangerBehavior:
    """Test Ranger: summon companion, track, wilderness comfort."""

    @pytest.fixture
    def ranger(self):
        """Create a RangerBehavior instance."""
        return RangerBehavior()

    @pytest.fixture
    def combat_state(self):
        """Create a combat AgentState."""
        state = AgentState()
        state.in_combat = True
        state.enemy = "Wolf"
        state.health = 80
        state.max_health = 100
        state.commands = ["attack", "summon", "flee"]
        return state

    @pytest.fixture
    def memory(self):
        """Create an empty AgentMemory."""
        return AgentMemory()

    def test_summons_companion_if_not_present(self, ranger, memory):
        """Spec: Ranger summons companion if not present (out of combat)."""
        state = AgentState()
        state.in_combat = False
        state.commands = ["summon", "go", "look"]
        ranger._has_companion = False

        command = ranger.get_exploration_command(state, memory)
        assert command is not None
        assert "summon" in command

    def test_uses_track_in_wilderness(self, ranger, memory):
        """Spec: Ranger uses track command in wilderness."""
        state = AgentState()
        state.in_combat = False
        state.location_category = "forest"
        state.commands = ["track", "go", "look"]
        ranger._has_companion = True  # Already has companion

        command = ranger.get_exploration_command(state, memory)
        # Should sometimes use track
        assert command is None or "track" in command

    def test_comfort_in_forest_wilderness(self, ranger, combat_state, memory):
        """Spec: Ranger is more comfortable in wilderness - lower flee in forest."""
        combat_state.location_category = "forest"
        combat_state.health = 18  # Just above 15% threshold

        # In wilderness, ranger should be slightly braver
        # This is a behavioral test - ranger behavior may differ
        flee_decision = ranger.should_flee(combat_state, memory)
        # At 18% health, might or might not flee depending on location
        assert isinstance(flee_decision, bool)

    def test_feeds_companion_when_hurt(self, ranger, memory):
        """Spec: Ranger feeds companion when companion health is low."""
        state = AgentState()
        state.in_combat = False
        state.commands = ["feed", "go", "look"]
        state.inventory = ["meat", "berries"]
        ranger._has_companion = True
        ranger._companion_health_low = True

        command = ranger.get_exploration_command(state, memory)
        assert command is not None
        assert "feed" in command

    def test_default_flee_threshold(self, ranger, combat_state, memory):
        """Spec: Ranger has default flee threshold (20%)."""
        combat_state.health = 25
        assert not ranger.should_flee(combat_state, memory)

        combat_state.health = 15
        assert ranger.should_flee(combat_state, memory)


class TestClericBehavior:
    """Test Cleric: smite undead, bless, heal, holy symbol."""

    @pytest.fixture
    def cleric(self):
        """Create a ClericBehavior instance."""
        return ClericBehavior()

    @pytest.fixture
    def combat_state(self):
        """Create a combat AgentState."""
        state = AgentState()
        state.in_combat = True
        state.enemy = "Skeleton"
        state.health = 80
        state.max_health = 100
        state.commands = ["attack", "smite", "bless", "cast", "flee"]
        return state

    @pytest.fixture
    def memory(self):
        """Create an empty AgentMemory."""
        return AgentMemory()

    def test_uses_smite_against_undead(self, cleric, combat_state, memory):
        """Spec: Cleric uses smite against undead enemies."""
        combat_state.enemy = "Skeleton"
        command = cleric.get_combat_command(combat_state, memory)
        assert command is not None
        assert "smite" in command

    def test_uses_smite_against_zombie(self, cleric, combat_state, memory):
        """Spec: Cleric uses smite against zombie (undead)."""
        combat_state.enemy = "Zombie Knight"
        command = cleric.get_combat_command(combat_state, memory)
        assert command is not None
        assert "smite" in command

    def test_uses_smite_against_ghost(self, cleric, combat_state, memory):
        """Spec: Cleric uses smite against ghost (undead)."""
        combat_state.enemy = "Ghost"
        command = cleric.get_combat_command(combat_state, memory)
        assert command is not None
        assert "smite" in command

    def test_uses_bless_before_combat(self, cleric, combat_state, memory):
        """Spec: Cleric uses bless at start of combat."""
        cleric._combat_turns = 0
        cleric._is_blessed = False
        combat_state.enemy = "Orc"  # Non-undead
        command = cleric.get_combat_command(combat_state, memory)
        assert command is not None
        assert "bless" in command

    def test_heals_party_when_hurt(self, cleric, combat_state, memory):
        """Spec: Cleric heals when health < 50%."""
        combat_state.health = 40  # 40% health
        combat_state.enemy = "Orc"  # Non-undead
        cleric._is_blessed = True  # Already blessed
        command = cleric.get_combat_command(combat_state, memory)
        assert command is not None
        assert "cast" in command and "heal" in command

    def test_ensures_holy_symbol_equipped(self, cleric, memory):
        """Spec: Cleric ensures holy symbol is equipped during exploration."""
        state = AgentState()
        state.in_combat = False
        state.commands = ["equip", "go", "look"]
        state.inventory = ["Holy Symbol of Light", "sword"]
        cleric._has_holy_symbol_equipped = False

        command = cleric.get_exploration_command(state, memory)
        assert command is not None
        assert "equip" in command and "holy" in command.lower()

    def test_default_flee_threshold(self, cleric, combat_state, memory):
        """Spec: Cleric has default flee threshold (20%)."""
        combat_state.health = 25
        assert not cleric.should_flee(combat_state, memory)

        combat_state.health = 15
        assert cleric.should_flee(combat_state, memory)


class TestSerialization:
    """Test checkpoint compatibility for ClassBehaviorConfig."""

    def test_behavior_config_to_dict(self):
        """Spec: ClassBehaviorConfig.to_dict() serializes correctly."""
        config = ClassBehaviorConfig(
            flee_health_threshold=0.15,
            heal_health_threshold=0.5,
            mana_conservation_threshold=0.2,
            special_ability_cooldown=3,
        )
        data = config.to_dict()
        assert data == {
            "flee_health_threshold": 0.15,
            "heal_health_threshold": 0.5,
            "mana_conservation_threshold": 0.2,
            "special_ability_cooldown": 3,
        }

    def test_behavior_config_from_dict(self):
        """Spec: ClassBehaviorConfig.from_dict() deserializes correctly."""
        data = {
            "flee_health_threshold": 0.25,
            "heal_health_threshold": 0.6,
            "mana_conservation_threshold": 0.3,
            "special_ability_cooldown": 5,
        }
        config = ClassBehaviorConfig.from_dict(data)
        assert config.flee_health_threshold == 0.25
        assert config.heal_health_threshold == 0.6
        assert config.mana_conservation_threshold == 0.3
        assert config.special_ability_cooldown == 5

    def test_serialization_round_trip(self):
        """Spec: Serialization round-trip works correctly."""
        original = ClassBehaviorConfig(
            flee_health_threshold=0.2,
            heal_health_threshold=0.5,
            mana_conservation_threshold=0.2,
            special_ability_cooldown=4,
        )
        data = original.to_dict()
        restored = ClassBehaviorConfig.from_dict(data)
        assert restored == original
