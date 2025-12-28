# Add Perception Stat to Enemy Model

## Spec
Add a `perception` stat to enemies that will be used for stealth detection. When a player attempts to sneak past enemies, the enemy's perception will be factored into the detection check (player stealth vs enemy perception).

**Behavior:**
- Default perception: 5 (baseline awareness)
- Perception scales with enemy level: `perception = 5 + (level // 2)`
- High perception enemies (scouts, sentries): +3 bonus
- Low perception enemies (mindless undead, beasts): -2 penalty
- Stealth check formula: `player_sneak_chance - (enemy_perception * 2)` (capped at 10-90%)

## Files to Modify

1. **`src/cli_rpg/models/enemy.py`**
   - Add `perception: int = 5` field to Enemy dataclass
   - Add to `to_dict()` serialization
   - Add to `from_dict()` deserialization with default fallback

2. **`tests/test_enemy.py`**
   - Add test for default perception value
   - Update `test_to_dict_serializes_enemy` to include perception
   - Update `test_from_dict_deserializes_enemy` to include perception
   - Update `test_serialization_roundtrip` to verify perception

3. **`src/cli_rpg/combat.py`** - `spawn_enemy()` function
   - Calculate perception based on level: `5 + (level // 2)`
   - Apply enemy-type modifiers (scouts: +3, beasts/undead: -2)
   - Pass perception to Enemy constructor

4. **`src/cli_rpg/game_state.py`** - `calculate_sneak_success_chance()`
   - Add optional `enemy_perception: int = 5` parameter
   - Modify formula to factor in perception: subtract `enemy_perception * 2` from base chance

5. **`src/cli_rpg/random_encounters.py`** - `check_random_encounter()`
   - After spawning enemy, pass enemy perception to sneak check
   - Update message to show detection by enemy type

6. **`src/cli_rpg/ai_config.py`** - `DEFAULT_ENEMY_GENERATION_PROMPT`
   - Add perception to JSON schema in prompt
   - Add perception to stats scaling guidelines

7. **`src/cli_rpg/ai_service.py`** - `_parse_enemy_response()`
   - Add "perception" to optional validated fields
   - Default to level-based calculation if not provided by AI

## Test Plan

1. Run existing `tests/test_enemy.py` - should fail initially for serialization tests
2. Implement Enemy model changes
3. Update tests for new perception field
4. Run `pytest tests/test_enemy.py -v` - should pass
5. Run `pytest --cov=src/cli_rpg` - verify no regressions

## Implementation Order

1. Add perception field to Enemy model + serialization
2. Update tests for Enemy model
3. Calculate perception in spawn_enemy()
4. Update sneak check to use enemy perception
5. Update AI prompt and parsing (optional enhancement)
