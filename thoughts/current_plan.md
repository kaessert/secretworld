# Implementation Plan: class_behaviors.py for AI Agent

## Summary
Create `scripts/agent/class_behaviors.py` with class-specific combat and exploration strategies for all 5 character classes (Warrior, Mage, Rogue, Ranger, Cleric) to make the AI agent behave differently based on character class.

## Spec

### ClassBehavior Protocol
```python
class ClassBehavior(Protocol):
    """Protocol defining class-specific agent behaviors."""

    def get_combat_command(self, state: AgentState, memory: AgentMemory) -> Optional[str]:
        """Return class-specific combat command, or None to use default attack."""
        ...

    def get_exploration_command(self, state: AgentState, memory: AgentMemory) -> Optional[str]:
        """Return class-specific exploration command, or None for default behavior."""
        ...

    def should_flee(self, state: AgentState, memory: AgentMemory) -> bool:
        """Return True if class strategy suggests fleeing."""
        ...
```

### Class-Specific Behaviors (from ISSUES.md)

| Class   | Combat                              | Exploration              |
|---------|-------------------------------------|--------------------------|
| Warrior | bash, aggressive/berserker stance   | Direct approach          |
| Mage    | fireball/ice_bolt, self-heal        | Conserve mana            |
| Rogue   | sneak attacks, hide                 | Search for secrets       |
| Ranger  | summon companion, track             | Wilderness comfort       |
| Cleric  | smite undead, bless, heal           | Holy symbol equipped     |

### Data Structures

```python
from enum import Enum

class CharacterClassName(Enum):
    """Mirror of CharacterClass from game for agent use."""
    WARRIOR = "Warrior"
    MAGE = "Mage"
    ROGUE = "Rogue"
    RANGER = "Ranger"
    CLERIC = "Cleric"

@dataclass
class ClassBehaviorConfig:
    """Configuration for class-specific behavior thresholds."""
    flee_health_threshold: float  # HP% to consider fleeing
    heal_health_threshold: float  # HP% to heal self
    mana_conservation_threshold: float  # Mana% to conserve
    special_ability_cooldown: int  # Moves between special abilities
```

## Tests First (TDD)

### File: `tests/test_agent_class_behaviors.py`

```python
# Test structure mirrors test_agent_personality.py and test_agent_memory.py

class TestClassBehaviorRegistry:
    """Test that all 5 classes have registered behaviors."""
    def test_warrior_behavior_exists(self): ...
    def test_mage_behavior_exists(self): ...
    def test_rogue_behavior_exists(self): ...
    def test_ranger_behavior_exists(self): ...
    def test_cleric_behavior_exists(self): ...
    def test_get_behavior_for_all_classes(self): ...

class TestWarriorBehavior:
    """Test Warrior combat: bash, aggressive/berserker stance."""
    def test_uses_bash_when_available(self): ...
    def test_switches_to_aggressive_stance(self): ...
    def test_switches_to_berserker_at_low_health(self): ...
    def test_higher_flee_threshold_than_default(self): ...

class TestMageBehavior:
    """Test Mage combat: fireball/ice_bolt, self-heal, mana conservation."""
    def test_uses_fireball_when_mana_available(self): ...
    def test_uses_ice_bolt_as_alternative(self): ...
    def test_casts_heal_when_hurt(self): ...
    def test_conserves_mana_when_low(self): ...
    def test_falls_back_to_attack_when_no_mana(self): ...

class TestRogueBehavior:
    """Test Rogue: sneak attacks, hide, secret searching."""
    def test_uses_sneak_attack_when_hidden(self): ...
    def test_uses_hide_when_not_hidden(self): ...
    def test_searches_for_secrets_in_dungeons(self): ...
    def test_prioritizes_stealth_approach(self): ...

class TestRangerBehavior:
    """Test Ranger: summon companion, track, wilderness comfort."""
    def test_summons_companion_if_not_present(self): ...
    def test_uses_track_in_wilderness(self): ...
    def test_comfort_in_forest_wilderness(self): ...
    def test_feeds_companion_when_hurt(self): ...

class TestClericBehavior:
    """Test Cleric: smite undead, bless, heal, holy symbol."""
    def test_uses_smite_against_undead(self): ...
    def test_uses_bless_before_combat(self): ...
    def test_heals_party_when_hurt(self): ...
    def test_ensures_holy_symbol_equipped(self): ...

class TestSerialization:
    """Test checkpoint compatibility."""
    def test_behavior_config_to_dict(self): ...
    def test_behavior_config_from_dict(self): ...
```

## Implementation

### File: `scripts/agent/class_behaviors.py`

1. **CharacterClassName enum** - Mirror game's CharacterClass
2. **ClassBehaviorConfig dataclass** - Thresholds and cooldowns with to_dict/from_dict
3. **ClassBehavior Protocol** - Interface for class behaviors
4. **5 Concrete behavior classes**:
   - `WarriorBehavior` - bash, stance switching
   - `MageBehavior` - spells, mana management
   - `RogueBehavior` - stealth, secrets
   - `RangerBehavior` - companion, tracking
   - `ClericBehavior` - smite, bless, heal
5. **BEHAVIOR_REGISTRY dict** - Maps CharacterClassName to behavior instance
6. **get_class_behavior(class_name)** - Helper to get behavior for a class

### Dependencies
- Import from `scripts.state_parser.AgentState` for state access
- Import from `scripts.agent.memory.AgentMemory` for memory access
- Use game commands: bash, stance, fireball, ice_bolt, heal, hide, sneak, track, summon, smite, bless

### Update `scripts/agent/__init__.py`
Export new classes:
- `ClassBehavior`
- `ClassBehaviorConfig`
- `CharacterClassName`
- `WarriorBehavior`, `MageBehavior`, `RogueBehavior`, `RangerBehavior`, `ClericBehavior`
- `BEHAVIOR_REGISTRY`
- `get_class_behavior`

## Implementation Steps

1. Create `tests/test_agent_class_behaviors.py` with all test cases
2. Create `scripts/agent/class_behaviors.py` with:
   - CharacterClassName enum
   - ClassBehaviorConfig dataclass with to_dict/from_dict
   - ClassBehavior Protocol
   - All 5 behavior classes with get_combat_command, get_exploration_command, should_flee
   - BEHAVIOR_REGISTRY and get_class_behavior helper
3. Update `scripts/agent/__init__.py` to export new classes
4. Run tests: `pytest tests/test_agent_class_behaviors.py -v`

## Detailed Class Behaviors

### WarriorBehavior
- **Combat**: Use `bash` if available. Switch to `stance aggressive` if health > 50%, `stance berserker` if health < 30%
- **Flee threshold**: 15% (lower than default - warriors are brave)
- **Exploration**: Direct approach, no special commands

### MageBehavior
- **Combat**: Use `cast fireball` or `cast ice_bolt` if mana > 30%. Use `cast heal` on self if health < 50% and mana > 20%. Fall back to `attack` when mana < 20%
- **Flee threshold**: 25% (higher - mages are fragile)
- **Exploration**: Rest more often to conserve mana for combat

### RogueBehavior
- **Combat**: Use `sneak` attack if character is hidden. Use `hide` if not hidden and combat just started
- **Flee threshold**: 20% (default)
- **Exploration**: Use `search` command frequently (30% chance per room in dungeons)

### RangerBehavior
- **Combat**: Use `summon` if companion not present and out of combat. Normal attacks otherwise
- **Flee threshold**: 20%
- **Exploration**: Use `track` in wilderness. `feed <item>` companion if companion health low

### ClericBehavior
- **Combat**: Use `smite` against undead (enemy name contains skeleton, zombie, ghost, etc.). Use `bless` at start of combat. Use `cast heal` when health < 50%
- **Flee threshold**: 20%
- **Exploration**: Ensure holy symbol is equipped

## Files to Create/Modify
- `tests/test_agent_class_behaviors.py` (new)
- `scripts/agent/class_behaviors.py` (new)
- `scripts/agent/__init__.py` (update exports)
