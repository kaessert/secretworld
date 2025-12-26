# Implementation Summary: Rogue Exploration Sneak Command

## What Was Implemented

### Feature: Exploration Sneak for Rogues
A new `sneak` command that allows Rogue characters to enter a sneaking mode during exploration (outside of combat). When activated, the Rogue has a chance to avoid random encounters on their next move.

### Files Modified

1. **src/cli_rpg/game_state.py**
   - Added `is_sneaking: bool = False` field to GameState class (line 261)
   - Added `calculate_sneak_success_chance(character)` function (lines 165-189)
     - Formula: 50% + (DEX * 2%) - (armor defense * 5%) - (15% if lit)
     - Capped between 10% and 90%
   - Added `self.is_sneaking = False` to all early return paths in `move()` method to ensure sneaking is cleared on any move attempt

2. **src/cli_rpg/random_encounters.py**
   - Added sneaking mode check in `check_for_random_encounter()` (lines 239-248)
   - When `is_sneaking=True`, calculates success chance and potentially avoids encounter
   - Clears `is_sneaking` after the check (consumed on move)
   - Also clears `is_sneaking` when entering safe zones

3. **src/cli_rpg/main.py**
   - Added exploration sneak command handler in `handle_exploration_command()` (lines 1036-1054)
   - Rogue-only check with appropriate error message
   - 10 stamina cost
   - Sets `is_sneaking=True` and displays success chance
   - Added help text entry: `"sneak (sn) - Move stealthily to avoid encounters (Rogue only, 10 stamina)"`

4. **tests/test_exploration_sneak.py** (NEW FILE)
   - 13 test cases covering:
     - Rogue-only access
     - Stamina cost (10)
     - Sneaking cleared after move (success or failure)
     - Encounter avoidance based on DEX, armor, light
     - Success formula capping (10-90%)
     - Combat sneak independence

## Technical Details

### Sneak Success Formula
```
success_chance = 50 + (DEX * 2) - (armor_defense * 5) - (15 if lit else 0)
capped between 10 and 90
```

### Key Design Decisions
- `is_sneaking` is stored on GameState (not Character) since it's exploration state
- Sneaking is consumed on ANY move attempt, even failed ones
- Sneaking is separate from combat sneak (which uses `is_hidden`)
- The "sn" alias works for both combat sneak and exploration sneak (context-aware)

## Test Results

All 13 new tests pass:
```
tests/test_exploration_sneak.py::TestSneakExplorationRogueOnly::test_sneak_exploration_rogue_success PASSED
tests/test_exploration_sneak.py::TestSneakExplorationRogueOnly::test_sneak_exploration_non_rogue_fails PASSED
tests/test_exploration_sneak.py::TestSneakExplorationStaminaCost::test_sneak_costs_10_stamina PASSED
tests/test_exploration_sneak.py::TestSneakExplorationStaminaCost::test_sneak_fails_without_stamina PASSED
tests/test_exploration_sneak.py::TestSneakClearedAfterMove::test_sneak_cleared_after_successful_move PASSED
tests/test_exploration_sneak.py::TestSneakClearedAfterMove::test_sneak_cleared_after_blocked_move PASSED
tests/test_exploration_sneak.py::TestSneakEncounterAvoidance::test_sneak_high_dex_avoids_encounter PASSED
tests/test_exploration_sneak.py::TestSneakEncounterAvoidance::test_sneak_low_dex_may_encounter PASSED
tests/test_exploration_sneak.py::TestSneakEncounterAvoidance::test_sneak_heavy_armor_penalty PASSED
tests/test_exploration_sneak.py::TestSneakEncounterAvoidance::test_sneak_light_source_penalty PASSED
tests/test_exploration_sneak.py::TestSneakSuccessFormula::test_sneak_success_capped_at_90 PASSED
tests/test_exploration_sneak.py::TestSneakSuccessFormula::test_sneak_success_minimum_10 PASSED
tests/test_exploration_sneak.py::TestSneakNotInCombat::test_sneak_exploration_separate_from_combat PASSED
```

Full test suite: 3028 passed, 1 failed (pre-existing flaky test unrelated to this change)

## E2E Validation

To validate the feature end-to-end:
1. Start a new game as a Rogue
2. Navigate to a non-safe zone (e.g., "go north" from town)
3. Use `sneak` command - should see stamina cost and success percentage
4. Move in any direction - sneaking should be consumed
5. Verify non-Rogues get error message when trying to sneak
6. Verify sneak fails with insufficient stamina (<10)
