# Plan: Refactor Agent to HumanLikeAgent (Phase 2.6)

## Spec

Integrate the completed personality, memory, and class behavior systems into the main Agent class to create a HumanLikeAgent that exhibits observable behavioral differences based on personality traits and character class.

**Behavioral Changes:**
- Personality traits (risk_tolerance, exploration_drive, social_engagement, combat_aggression, resource_conservation) modify decision thresholds
- Class behaviors provide class-specific combat commands (bash, cast, sneak, etc.)
- Memory system influences decisions based on past failures and location danger
- Environmental awareness (time_of_day, tiredness, weather) affects behavior

## Tests (in `tests/test_human_like_agent.py`)

1. **Agent creation with personality/class/memory**
   - `test_create_with_personality_type`: HumanLikeAgent accepts PersonalityType, stores traits
   - `test_create_with_character_class`: Accepts CharacterClassName, gets behavior
   - `test_create_with_memory`: AgentMemory is initialized and accessible
   - `test_default_is_cautious_warrior`: Default personality is CAUTIOUS_EXPLORER, default class is WARRIOR

2. **Personality affects decision thresholds**
   - `test_aggressive_fighter_flees_later`: AGGRESSIVE_FIGHTER (risk_tolerance=0.9) flees at lower HP than CAUTIOUS_EXPLORER (0.2)
   - `test_completionist_talks_more`: COMPLETIONIST (social_engagement=1.0) prioritizes NPC interaction
   - `test_speedrunner_skips_npcs`: SPEEDRUNNER (social_engagement=0.1) skips optional NPC talks
   - `test_exploration_drive_affects_dungeon_depth`: Higher exploration_drive = more moves in sub-locations

3. **Class behavior integration**
   - `test_warrior_uses_bash`: Warrior class uses bash command in combat when available
   - `test_mage_casts_spells`: Mage casts fireball/ice_bolt when mana sufficient
   - `test_rogue_uses_sneak`: Rogue hides then sneak attacks
   - `test_ranger_summons_companion`: Ranger summons companion in exploration
   - `test_cleric_smites_undead`: Cleric uses smite against undead enemies

4. **Memory influences decisions**
   - `test_avoids_dangerous_enemies`: Agent flees from enemies that killed it before
   - `test_location_danger_affects_entry`: High-danger locations entered more cautiously
   - `test_npc_memory_persists`: NPC interactions are remembered across locations

5. **Environmental awareness**
   - `test_night_affects_combat`: Night time (is_night=True) increases caution
   - `test_tiredness_triggers_rest`: High tiredness triggers rest decision
   - `test_weather_affects_exploration`: Bad weather reduces exploration priority

6. **Serialization**
   - `test_to_checkpoint_dict_includes_new_fields`: Checkpoint includes personality, class, memory
   - `test_restore_from_checkpoint_restores_all`: All state restored from checkpoint

## Implementation Steps

### Step 1: Create `scripts/human_like_agent.py`

```python
class HumanLikeAgent(Agent):
    """Agent with personality, class behaviors, and memory for human-like play."""

    def __init__(
        self,
        personality: PersonalityType = PersonalityType.CAUTIOUS_EXPLORER,
        character_class: CharacterClassName = CharacterClassName.WARRIOR,
        verbose: bool = False,
    ):
        super().__init__(verbose=verbose)
        self.personality_type = personality
        self.traits = get_personality_traits(personality)
        self.character_class = character_class
        self.class_behavior = get_class_behavior(character_class)
        self.memory = AgentMemory()
```

### Step 2: Override `_combat_decision()` to use class behaviors

- Call `self.class_behavior.get_combat_command(state, self.memory)`
- If returns command, use it; otherwise fall back to base attack
- Use `self.class_behavior.should_flee()` for flee decision
- Modify flee threshold by `traits.risk_tolerance`

### Step 3: Override `_explore_decision()` to use personality + class

- Scale NPC talk probability by `traits.social_engagement`
- Scale dungeon entry by `traits.exploration_drive` and `traits.risk_tolerance`
- Call `self.class_behavior.get_exploration_command()` for class-specific actions
- Use memory's `is_enemy_dangerous()` and `get_location_danger()`

### Step 4: Add environmental awareness to decisions

- Check `state.is_night()` for undead caution (combat_aggression modifier)
- Check `state.should_rest()` for tiredness-based rest
- Check `state.is_bad_weather()` for exploration reduction

### Step 5: Update serialization

- `to_checkpoint_dict()`: Add personality_type, character_class, memory.to_dict()
- `restore_from_checkpoint()`: Restore personality, class, memory from dict

### Step 6: Update `GameSession` in `ai_agent.py`

- Add `personality` and `character_class` parameters
- Pass to HumanLikeAgent constructor instead of Agent

### Step 7: Update `run_simulation.py` CLI

- Add `--personality=<type>` flag (default: cautious)
- Add `--class=<name>` flag (default: warrior)

## Files to Create/Modify

1. **Create**: `scripts/human_like_agent.py` - HumanLikeAgent class
2. **Create**: `tests/test_human_like_agent.py` - Tests for new agent
3. **Modify**: `scripts/ai_agent.py` - Update GameSession to use HumanLikeAgent
4. **Modify**: `scripts/run_simulation.py` - Add CLI flags
5. **Modify**: `scripts/agent/__init__.py` - Export HumanLikeAgent
