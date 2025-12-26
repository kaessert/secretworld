# Implementation Plan: Ranger Class Abilities

## Feature Spec

Ranger class abilities to bring parity with Warrior (bash), Mage (fireball/ice_bolt/heal), and Rogue (sneak):

1. **`track` command** (exploration): Rangers can detect enemies in adjacent locations
   - Costs 10 stamina
   - Shows enemy count and types in adjacent connected locations
   - Success based on PER stat (base 50% + 3% per PER)
   - Only Rangers can use this ability
   - Can only be used outside combat

2. **Wilderness bonus**: Rangers get combat bonuses in wilderness/forest locations
   - +15% attack damage in wilderness/forest category locations
   - Applied automatically during combat when location category matches

---

## Phase 1: Tests (TDD)

### Create `tests/test_ranger.py`

Test cases for `track` command:
- `test_track_only_available_to_ranger` - Other classes get "Only Rangers can track!"
- `test_track_costs_10_stamina` - Stamina decreases by 10
- `test_track_fails_without_stamina` - Returns error with <10 stamina
- `test_track_detects_enemies_in_adjacent_locations` - Reports enemy types and counts
- `test_track_fails_during_combat` - Cannot use while in combat
- `test_track_reports_safe_when_no_enemies` - "No enemies detected nearby"
- `test_track_success_scales_with_perception` - Higher PER = higher success rate

Test cases for wilderness bonus:
- `test_ranger_wilderness_bonus_in_forest` - +15% damage in forest category
- `test_ranger_wilderness_bonus_in_wilderness` - +15% damage in wilderness category
- `test_ranger_no_bonus_in_dungeon` - No bonus in dungeon category
- `test_ranger_no_bonus_in_town` - No bonus in town category
- `test_non_ranger_no_wilderness_bonus` - Warriors/Mages/Rogues don't get bonus

---

## Phase 2: Implementation

### 2.1 Add `track` command to game_state.py

1. Add `"track"` to `KNOWN_COMMANDS` set (line ~54)

### 2.2 Create `src/cli_rpg/ranger.py` module

```python
"""Ranger class abilities: track command and wilderness bonuses."""

def execute_track(game_state: "GameState") -> Tuple[bool, str]:
    """Ranger tracks enemies in adjacent locations.

    - Costs 10 stamina
    - Success: base 50% + 3% per PER
    - Returns enemy types/counts in connected locations
    """
```

Constants:
- `TRACK_STAMINA_COST = 10`
- `TRACK_BASE_CHANCE = 50`
- `TRACK_PER_BONUS = 3`
- `WILDERNESS_DAMAGE_BONUS = 0.15`
- `WILDERNESS_CATEGORIES = {"forest", "wilderness"}`

### 2.3 Integrate track into main.py exploration commands

In `handle_exploration_command()` (around line 835), add:
```python
elif command == "track":
    from cli_rpg.ranger import execute_track
    success, message = execute_track(game_state)
    return (True, f"\n{message}")
```

### 2.4 Add wilderness bonus to combat.py

In `CombatEncounter.player_attack()` (around line 637), after calculating base damage:
```python
# Apply Ranger wilderness bonus
if self.player.character_class == CharacterClass.RANGER:
    if hasattr(self, 'location_category') and self.location_category in WILDERNESS_CATEGORIES:
        dmg = int(dmg * (1 + WILDERNESS_DAMAGE_BONUS))
```

Modify `CombatEncounter.__init__()` to accept optional `location_category` parameter.

Update `GameState.trigger_encounter()` and boss spawning to pass location category.

### 2.5 Update help text in main.py

Add to `get_command_reference()`:
```
"  track            - Track enemies in nearby areas (Ranger only)"
```

### 2.6 Update completer.py (optional)

Add `"track"` completion support (already handled by KNOWN_COMMANDS).

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `tests/test_ranger.py` | CREATE | Unit tests for track and wilderness bonus |
| `src/cli_rpg/ranger.py` | CREATE | Ranger-specific abilities module |
| `src/cli_rpg/game_state.py` | MODIFY | Add "track" to KNOWN_COMMANDS |
| `src/cli_rpg/main.py` | MODIFY | Add track command handler, update help |
| `src/cli_rpg/combat.py` | MODIFY | Add wilderness bonus, location_category param |

---

## Implementation Order

1. Write tests first (`tests/test_ranger.py`)
2. Create ranger.py with `execute_track()` and constants
3. Add "track" to KNOWN_COMMANDS in game_state.py
4. Wire up track command in main.py exploration handler
5. Add wilderness bonus to combat.py
6. Update help text
7. Run tests to verify
