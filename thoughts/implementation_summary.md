# Implementation Summary: Combo Combat System

## What Was Implemented

A combo combat system that tracks the player's last 3 actions and unlocks special combo moves when specific action sequences are performed. This addresses the combat tactical depth issue by rewarding strategic action sequencing.

### Features

1. **Action History Tracking**: Combat now tracks the last 3 player actions (`attack`, `defend`, `cast`)

2. **Three Combo Moves**:
   - **Frenzy** (`Attack → Attack → Attack`): Triple attack dealing 1.5x total damage
   - **Revenge** (`Defend → Defend → Attack`): Counter-attack dealing damage equal to damage taken while defending
   - **Arcane Burst** (`Cast → Cast → Cast`): Empowered spell dealing 2x magic damage

3. **Combo State Machine**:
   - Actions are recorded after each player turn
   - When a combo pattern is matched, `pending_combo` is set
   - On the next matching action, the combo triggers and history clears
   - Flee clears action history (breaks combo chain)

4. **UI Notifications**:
   - Combat status shows "Last actions: [Attack] → [Defend]"
   - When combo is ready: "COMBO AVAILABLE: Frenzy!"

## Files Modified

1. **`src/cli_rpg/combat.py`**:
   - Added `COMBOS` dictionary defining combo patterns
   - Added to `CombatEncounter.__init__()`:
     - `action_history: list[str]`
     - `damage_taken_while_defending: int`
     - `pending_combo: Optional[str]`
   - Added combo helper methods:
     - `_record_action()` - Records action and checks for combos
     - `_check_for_combo()` - Matches history against patterns
     - `get_pending_combo()` - Returns current pending combo
     - `_clear_action_history()` - Resets combo state
   - Modified `player_attack()` - Handles Frenzy and Revenge combos
   - Modified `player_defend()` - Records "defend" action
   - Modified `player_cast()` - Handles Arcane Burst combo
   - Modified `player_flee()` - Clears action history
   - Modified `enemy_turn()` - Tracks damage taken while defending
   - Modified `end_combat()` - Clears combo state
   - Modified `get_status()` - Shows action history and pending combo

2. **`tests/test_combo_combat.py`** (new file):
   - 22 tests covering all combo functionality:
     - Action history tracking (7 tests)
     - Combo detection (5 tests)
     - Frenzy combo (3 tests)
     - Revenge combo (3 tests)
     - Arcane Burst combo (2 tests)
     - UI notifications (2 tests)

## Test Results

- **22 new tests** - All passing
- **2055 total tests** - All passing (no regressions)

## Design Decisions

1. **History Length**: Limited to 3 actions (oldest dropped) to keep combos achievable
2. **Combo Trigger**: Combos trigger on the *next* matching action after pattern is complete
3. **Flee Breaks Chain**: Attempting to flee clears action history (prevents fleeing mid-combo)
4. **Damage Tracking**: Revenge tracks damage taken *while defending* (half damage taken)
5. **Frenzy Calculation**: `single_hit = base_damage // 2`, `total = single_hit * 3` (roughly 1.5x)

## E2E Validation

The combo system should validate:
1. Action history appears in combat status after performing actions
2. "COMBO AVAILABLE" message appears after completing a combo sequence
3. Combo attacks show special messages ("FRENZY!", "REVENGE!", "ARCANE BURST!")
4. Damage matches expected values (1.5x for Frenzy, 2x for Arcane Burst)
5. Action history clears after combo triggers or fleeing
