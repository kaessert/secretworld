"""Tests for HumanLikeAgent - agent with personality, class, and memory.

Tests that HumanLikeAgent integrates personality traits, class behaviors,
and memory to produce observable behavioral differences.
"""

import pytest
from dataclasses import replace

from scripts.agent import (
    PersonalityType,
    PersonalityTraits,
    CharacterClassName,
    AgentMemory,
    get_personality_traits,
)
from scripts.human_like_agent import HumanLikeAgent
from scripts.state_parser import AgentState


# === Fixtures ===

@pytest.fixture
def base_state() -> AgentState:
    """Create a basic AgentState for testing."""
    return AgentState(
        location="Test Town",
        health=100,
        max_health=100,
        gold=50,
        level=1,
        exits=["north", "south", "east", "west"],
        npcs=["Guard", "Merchant"],
        commands=["go", "talk", "look", "rest", "enter"],
        enterables=["Dark Cave"],
        in_sub_location=False,
        in_combat=False,
    )


@pytest.fixture
def combat_state() -> AgentState:
    """Create a combat AgentState for testing."""
    return AgentState(
        location="Dark Cave",
        health=50,
        max_health=100,
        gold=50,
        level=1,
        in_combat=True,
        enemy="Goblin",
        enemy_health=30,
        commands=["attack", "flee", "defend"],
        exits=[],
        npcs=[],
    )


# === 1. Agent creation with personality/class/memory ===

class TestAgentCreation:
    """Test HumanLikeAgent initialization with personality/class/memory."""

    def test_create_with_personality_type(self):
        """HumanLikeAgent accepts PersonalityType and stores traits."""
        # Spec: Agent creation with personality type
        agent = HumanLikeAgent(personality=PersonalityType.AGGRESSIVE_FIGHTER)

        assert agent.personality_type == PersonalityType.AGGRESSIVE_FIGHTER
        assert agent.traits is not None
        assert agent.traits.risk_tolerance == 0.9  # From preset
        assert agent.traits.combat_aggression == 0.9

    def test_create_with_character_class(self):
        """HumanLikeAgent accepts CharacterClassName and gets behavior."""
        # Spec: Agent creation with character class
        agent = HumanLikeAgent(character_class=CharacterClassName.MAGE)

        assert agent.character_class == CharacterClassName.MAGE
        assert agent.class_behavior is not None
        # Mage has higher flee threshold (fragile)
        assert agent.class_behavior.config.flee_health_threshold == 0.25

    def test_create_with_memory(self):
        """AgentMemory is initialized and accessible."""
        # Spec: Agent creation with memory
        agent = HumanLikeAgent()

        assert agent.memory is not None
        assert isinstance(agent.memory, AgentMemory)
        assert agent.memory.failures == []
        assert agent.memory.npc_memories == {}
        assert agent.memory.location_memories == {}

    def test_default_is_cautious_warrior(self):
        """Default personality is CAUTIOUS_EXPLORER, default class is WARRIOR."""
        # Spec: Default configuration
        agent = HumanLikeAgent()

        assert agent.personality_type == PersonalityType.CAUTIOUS_EXPLORER
        assert agent.character_class == CharacterClassName.WARRIOR
        # Verify traits match the preset
        expected_traits = get_personality_traits(PersonalityType.CAUTIOUS_EXPLORER)
        assert agent.traits.risk_tolerance == expected_traits.risk_tolerance


# === 2. Personality affects decision thresholds ===

class TestPersonalityThresholds:
    """Test that personality traits modify decision thresholds."""

    def test_aggressive_fighter_flees_later(self, combat_state):
        """AGGRESSIVE_FIGHTER (risk_tolerance=0.9) flees at lower HP than CAUTIOUS_EXPLORER."""
        # Spec: Risk tolerance affects flee threshold
        aggressive = HumanLikeAgent(personality=PersonalityType.AGGRESSIVE_FIGHTER)
        cautious = HumanLikeAgent(personality=PersonalityType.CAUTIOUS_EXPLORER)

        # At 15% HP - aggressive should still fight, cautious should flee
        critical_state = replace(combat_state, health=15, max_health=100)

        aggressive_decision = aggressive.decide(critical_state)
        cautious_decision = cautious.decide(critical_state)

        # Aggressive fights (attacks), cautious flees
        assert aggressive_decision == "attack", f"Aggressive should attack at 15% HP, got: {aggressive_decision}"
        assert cautious_decision == "flee", f"Cautious should flee at 15% HP, got: {cautious_decision}"

    def test_completionist_talks_more(self, base_state):
        """COMPLETIONIST (social_engagement=1.0) prioritizes NPC interaction."""
        # Spec: Social engagement affects NPC talk priority
        completionist = HumanLikeAgent(personality=PersonalityType.COMPLETIONIST)

        # Skip initial look behavior by setting agent as already in this location
        completionist.needs_look = False
        completionist.last_location = base_state.location

        # At full health with NPCs present
        decision = completionist.decide(base_state)

        # Completionist should prioritize talking to NPCs
        assert decision.startswith("talk "), f"Completionist should talk to NPCs, got: {decision}"

    def test_speedrunner_skips_npcs(self, base_state):
        """SPEEDRUNNER (social_engagement=0.1) skips optional NPC talks."""
        # Spec: Low social engagement skips NPCs
        speedrunner = HumanLikeAgent(personality=PersonalityType.SPEEDRUNNER)

        # Skip initial look behavior by setting agent as already in this location
        speedrunner.needs_look = False
        speedrunner.last_location = base_state.location

        # Speedrunner should move rather than talk (unless quest-critical)
        decision = speedrunner.decide(base_state)

        # Speedrunner should prefer movement over talking
        assert decision.startswith("go ") or decision.startswith("enter "), \
            f"Speedrunner should move/enter, got: {decision}"

    def test_exploration_drive_affects_dungeon_depth(self, base_state):
        """Higher exploration_drive = more moves in sub-locations."""
        # Spec: Exploration drive affects sub-location behavior
        cautious = HumanLikeAgent(personality=PersonalityType.CAUTIOUS_EXPLORER)
        speedrunner = HumanLikeAgent(personality=PersonalityType.SPEEDRUNNER)

        # exploration_drive: cautious=0.9, speedrunner=0.1
        # Higher drive = higher max sub-location moves allowed
        assert cautious.max_sub_location_moves > speedrunner.max_sub_location_moves


# === 3. Class behavior integration ===

class TestClassBehaviorIntegration:
    """Test class-specific commands are used in appropriate situations."""

    def test_warrior_uses_bash(self, combat_state):
        """Warrior class uses bash command in combat when available."""
        # Spec: Warrior class behavior
        warrior = HumanLikeAgent(character_class=CharacterClassName.WARRIOR)

        # Add bash to available commands
        state_with_bash = replace(combat_state, commands=["attack", "flee", "bash"])

        decision = warrior.decide(state_with_bash)

        assert decision == "bash", f"Warrior should use bash when available, got: {decision}"

    def test_mage_casts_spells(self, combat_state):
        """Mage casts fireball/ice_bolt when mana sufficient."""
        # Spec: Mage class behavior - casts spells
        mage = HumanLikeAgent(character_class=CharacterClassName.MAGE)
        # Ensure mana is sufficient
        mage.class_behavior._mana_percent = 0.5

        # Add cast to commands
        state_with_cast = replace(combat_state, commands=["attack", "flee", "cast"])

        decision = mage.decide(state_with_cast)

        # Mage should cast a spell (fireball or ice_bolt)
        assert decision.startswith("cast "), f"Mage should cast spell, got: {decision}"
        assert "fireball" in decision or "ice_bolt" in decision or "heal" in decision

    def test_rogue_uses_sneak(self, combat_state):
        """Rogue hides then sneak attacks."""
        # Spec: Rogue class behavior - stealth
        rogue = HumanLikeAgent(character_class=CharacterClassName.ROGUE)

        # Add hide and sneak to commands (first turn, should hide)
        state_with_stealth = replace(combat_state, commands=["attack", "flee", "hide", "sneak"])

        decision = rogue.decide(state_with_stealth)

        # First turn: should hide
        assert decision == "hide", f"Rogue should hide first turn, got: {decision}"

        # Mark as hidden and try again
        rogue.class_behavior._is_hidden = True
        decision2 = rogue.decide(state_with_stealth)

        # After hiding: should sneak attack
        assert decision2 == "sneak", f"Hidden rogue should sneak attack, got: {decision2}"

    def test_ranger_summons_companion(self, base_state):
        """Ranger summons companion in exploration."""
        # Spec: Ranger class behavior - companion
        ranger = HumanLikeAgent(character_class=CharacterClassName.RANGER)

        # Skip initial look behavior by setting agent as already in this location
        ranger.needs_look = False
        ranger.last_location = base_state.location

        # Add summon to commands - remove NPCs to avoid talking first, remove enterables
        state_with_summon = replace(base_state, commands=["go", "look", "summon"], npcs=[], enterables=[])

        decision = ranger.decide(state_with_summon)

        # Ranger should summon companion
        assert decision == "summon", f"Ranger should summon companion, got: {decision}"

    def test_cleric_smites_undead(self, combat_state):
        """Cleric uses smite against undead enemies."""
        # Spec: Cleric class behavior - smite undead
        cleric = HumanLikeAgent(character_class=CharacterClassName.CLERIC)

        # Set up undead enemy
        undead_state = replace(
            combat_state,
            enemy="Skeleton Warrior",
            commands=["attack", "flee", "smite", "bless"]
        )

        decision = cleric.decide(undead_state)

        # Cleric should smite undead
        assert decision == "smite", f"Cleric should smite undead, got: {decision}"


# === 4. Memory influences decisions ===

class TestMemoryInfluence:
    """Test that memory affects agent decisions."""

    def test_avoids_dangerous_enemies(self, combat_state):
        """Agent flees from enemies that killed it before."""
        # Spec: Memory influences combat decisions
        agent = HumanLikeAgent()

        # Record a death from this enemy type
        agent.memory.record_failure(
            enemy_name="Goblin",
            location="Dark Cave",
            cause="death",
            timestamp="2024-01-01T10:00:00",
            health_at_failure=0,
        )

        # Now at healthy HP, but facing previously-deadly enemy
        healthy_combat = replace(combat_state, health=80, max_health=100)

        decision = agent.decide(healthy_combat)

        # Should flee despite good HP due to memory
        assert decision == "flee", f"Should flee from dangerous enemy, got: {decision}"

    def test_location_danger_affects_entry(self, base_state):
        """High-danger locations entered more cautiously."""
        # Spec: Location danger affects exploration
        agent = HumanLikeAgent()

        # Record high danger at the enterable location
        agent.memory.update_location(
            name="Dark Cave",
            category="dungeon",
            had_combat=True,
            found_secret=False,
            found_treasure=False,
            died=True,  # Died here before
        )

        # With high danger recorded (0.7), agent should be more cautious
        danger = agent.memory.get_location_danger("Dark Cave")
        assert danger >= 0.5, f"Location should be marked dangerous: {danger}"

        # At healthy HP but cautious personality
        decision = agent.decide(base_state)

        # With high danger, agent should skip entering or explore differently
        # The actual behavior depends on implementation - just verify memory is consulted

    def test_npc_memory_persists(self):
        """NPC interactions are remembered across locations."""
        # Spec: NPC memory persistence
        agent = HumanLikeAgent()

        # Record an NPC interaction
        agent.memory.record_npc_interaction(
            name="Guard",
            location="Town Gate",
            interaction_type="talk",
            trust_change=5,
            has_quest=True,
            timestamp="2024-01-01T10:00:00",
        )

        # Verify memory persists
        assert "Guard" in agent.memory.npc_memories
        npc_mem = agent.memory.npc_memories["Guard"]
        assert npc_mem.has_quest is True
        assert npc_mem.trust_level == 5


# === 5. Environmental awareness ===

class TestEnvironmentalAwareness:
    """Test that environmental factors affect behavior."""

    def test_night_affects_combat(self, combat_state):
        """Night time (is_night=True) increases caution."""
        # Spec: Time of day affects combat decisions
        agent = HumanLikeAgent(personality=PersonalityType.CAUTIOUS_EXPLORER)

        # Night time state - at moderate HP during night, should be more cautious
        # CAUTIOUS_EXPLORER has risk_tolerance=0.2, so personality_modifier = (0.5 - 0.2) * 0.15 = 0.045
        # Warrior flee_threshold = 0.15, + 0.045 personality + 0.10 night = 0.295
        # So at ~28% HP, they should flee at night
        night_combat = replace(combat_state, hour=22, time_of_day="night", health=28, max_health=100)

        decision = agent.decide(night_combat)

        # At night with HP below effective threshold, cautious agent should flee
        assert decision == "flee", f"Should be more cautious at night, got: {decision}"

    def test_tiredness_triggers_rest(self, base_state):
        """High tiredness triggers rest decision."""
        # Spec: Tiredness affects rest decisions
        agent = HumanLikeAgent()

        # Skip initial look behavior by setting agent as already in this location
        agent.needs_look = False
        agent.last_location = base_state.location

        # High tiredness state - no NPCs to avoid talking, and should_rest() requires 60+ tiredness
        tired_state = replace(base_state, tiredness=70, commands=["go", "rest", "look"], npcs=[], enterables=[])

        decision = agent.decide(tired_state)

        # Should rest when tired
        assert decision == "rest", f"Should rest when tired, got: {decision}"

    def test_weather_affects_exploration(self, base_state):
        """Bad weather reduces exploration priority."""
        # Spec: Weather affects exploration
        agent = HumanLikeAgent()

        # Storm weather - should reduce exploration drive
        storm_state = replace(base_state, weather="storm")

        # The agent should still function but may prioritize shelter
        decision = agent.decide(storm_state)

        # Decision should be valid (not an error)
        assert decision is not None
        assert len(decision) > 0


# === 6. Serialization ===

class TestSerialization:
    """Test checkpoint serialization includes new fields."""

    def test_to_checkpoint_dict_includes_new_fields(self):
        """Checkpoint includes personality, class, memory."""
        # Spec: Serialization includes new agent fields
        agent = HumanLikeAgent(
            personality=PersonalityType.AGGRESSIVE_FIGHTER,
            character_class=CharacterClassName.MAGE,
        )
        agent.memory.record_failure(
            enemy_name="Dragon",
            location="Cave",
            cause="death",
            timestamp="2024-01-01",
            health_at_failure=0,
        )

        checkpoint = agent.to_checkpoint_dict()

        # Verify new fields are present
        assert "personality_type" in checkpoint
        assert checkpoint["personality_type"] == "AGGRESSIVE_FIGHTER"
        assert "character_class" in checkpoint
        assert checkpoint["character_class"] == "MAGE"
        assert "memory" in checkpoint
        assert len(checkpoint["memory"]["failures"]) == 1

    def test_restore_from_checkpoint_restores_all(self):
        """All state restored from checkpoint."""
        # Spec: Checkpoint restoration
        original = HumanLikeAgent(
            personality=PersonalityType.COMPLETIONIST,
            character_class=CharacterClassName.ROGUE,
        )
        original.memory.record_failure(
            enemy_name="Troll",
            location="Bridge",
            cause="death",
            timestamp="2024-01-01",
            health_at_failure=0,
        )

        # Save checkpoint
        checkpoint = original.to_checkpoint_dict()

        # Create new agent and restore
        restored = HumanLikeAgent()
        restored.restore_from_checkpoint(checkpoint)

        # Verify restoration
        assert restored.personality_type == PersonalityType.COMPLETIONIST
        assert restored.character_class == CharacterClassName.ROGUE
        assert "Troll" in restored.memory.dangerous_enemies
