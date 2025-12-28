# Implementation Plan: Human-Like Agent Core (Phase 2 - Personality System)

## Goal
Implement `scripts/agent/personality.py` with 5 personality presets that will influence agent decision-making, establishing the foundation for human-like behavior.

## Specification

### PersonalityType Enum
Five presets with distinct play styles:
- `CAUTIOUS_EXPLORER` - Prioritizes safety and thorough exploration
- `AGGRESSIVE_FIGHTER` - Seeks combat, takes risks
- `COMPLETIONIST` - Does everything, talks to everyone
- `SPEEDRUNNER` - Minimal interaction, efficient pathing
- `ROLEPLAYER` - Balanced with focus on NPC interaction

### PersonalityTraits Dataclass
Float traits (0.0-1.0) that influence decisions:
- `risk_tolerance` - Willingness to fight at low HP, enter dangerous areas
- `exploration_drive` - Priority on visiting new locations vs returning to known
- `social_engagement` - Likelihood of talking to NPCs, accepting quests
- `combat_aggression` - Preference for fighting vs fleeing
- `resource_conservation` - Tendency to use potions sparingly, rest often

### Preset Values (from ISSUES.md)
| Type | Risk | Exploration | Social | Combat | Conservation |
|------|------|-------------|--------|--------|--------------|
| CAUTIOUS_EXPLORER | 0.2 | 0.9 | 0.7 | 0.3 | 0.7 |
| AGGRESSIVE_FIGHTER | 0.9 | 0.4 | 0.3 | 0.9 | 0.2 |
| COMPLETIONIST | 0.5 | 1.0 | 1.0 | 0.5 | 0.4 |
| SPEEDRUNNER | 0.7 | 0.1 | 0.1 | 0.4 | 0.3 |
| ROLEPLAYER | 0.5 | 0.7 | 0.9 | 0.5 | 0.5 |

## Implementation Steps

### 1. Create package structure
- Create `scripts/agent/__init__.py`
- Create `scripts/agent/personality.py`

### 2. Implement personality.py
```python
# Contents:
# - PersonalityType(Enum) with 5 presets
# - PersonalityTraits dataclass with 5 float fields
# - PERSONALITY_PRESETS dict mapping type -> traits
# - get_personality_traits(preset: PersonalityType) -> PersonalityTraits
# - Serialization methods (to_dict/from_dict) for checkpoint compatibility
```

### 3. Write tests
- `tests/test_agent_personality.py`
- Test enum values exist
- Test all presets have valid trait ranges (0.0-1.0)
- Test serialization round-trip
- Test get_personality_traits returns correct values

## Files to Create
1. `scripts/agent/__init__.py` - Package init exposing PersonalityType, PersonalityTraits
2. `scripts/agent/personality.py` - Core personality implementation
3. `tests/test_agent_personality.py` - Unit tests

## Integration Points (future)
- `Agent.__init__()` will accept `personality: PersonalityType` parameter
- `Agent._combat_decision()` will use `combat_aggression` and `risk_tolerance`
- `Agent._healing_decision()` will use `resource_conservation`
- `Agent._overworld_exploration_decision()` will use `exploration_drive` and `social_engagement`
- CLI `--personality` flag in `run_simulation.py`

## Acceptance Criteria
- [ ] PersonalityType enum with 5 values
- [ ] PersonalityTraits dataclass with 5 float fields
- [ ] All preset values match ISSUES.md spec
- [ ] Traits validated to 0.0-1.0 range
- [ ] Serialization works for checkpoint compatibility
- [ ] All tests pass
