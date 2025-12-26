# Implementation Plan: Rogue Exploration Sneak Command

## Feature Spec

**Goal**: Add `sneak` command for Rogues to avoid random encounters when exploring (not in combat).

**Mechanics**:
- Command: `sneak` (exploration mode) - Rogue-only
- Effect: Enters "sneaking" mode that lasts until next move
- Benefit: Reduces random encounter chance during next movement
- Success formula: Base 50% + (DEX * 2%) - (armor defense * 5%) - (15% if lit), capped 10-90%
- Stamina cost: 10 stamina (same as combat sneak)
- Feedback: Clear message on success/failure chance and result

## Test Spec (tests/test_exploration_sneak.py)

```python
"""Tests for Rogue exploration sneak command.

Spec: Rogue's sneak command enables sneaking mode during exploration:
- Command: sneak - Rogue-only exploration action
- Effect: Sets is_sneaking=True on GameState for next move
- Benefit: Reduces random encounter chance (success based on DEX, armor, light)
- Cost: 10 stamina
- Formula: 50% + (DEX * 2%) - (armor defense * 5%) - (15% if lit), capped 10-90%
"""
```

### Test Cases:
1. **TestSneakExplorationRogueOnly**
   - `test_sneak_exploration_rogue_success` - Rogue can use sneak, sets is_sneaking
   - `test_sneak_exploration_non_rogue_fails` - Warrior/Mage/etc get error message

2. **TestSneakExplorationStaminaCost**
   - `test_sneak_costs_10_stamina` - Verify stamina deducted
   - `test_sneak_fails_without_stamina` - Error when stamina < 10

3. **TestSneakClearedAfterMove**
   - `test_sneak_cleared_after_successful_move` - is_sneaking reset to False
   - `test_sneak_cleared_after_blocked_move` - is_sneaking reset even on failed move

4. **TestSneakEncounterAvoidance**
   - `test_sneak_high_dex_avoids_encounter` - High DEX Rogue avoids encounter
   - `test_sneak_low_dex_may_encounter` - Low DEX Rogue can still trigger encounter
   - `test_sneak_heavy_armor_penalty` - Armor reduces sneak success
   - `test_sneak_light_source_penalty` - Light reduces sneak success

5. **TestSneakSuccessFormula**
   - `test_sneak_success_capped_at_90` - Even max DEX caps at 90%
   - `test_sneak_success_minimum_10` - Even worst case has 10% floor

6. **TestSneakNotInCombat**
   - `test_sneak_exploration_separate_from_combat` - Combat sneak unaffected

## Implementation Steps

### Step 1: Add is_sneaking field to GameState
**File**: `src/cli_rpg/game_state.py`

In `__init__()` (~line 233), add:
```python
self.is_sneaking: bool = False  # Rogue exploration sneak mode
```

### Step 2: Add sneak success calculation helper
**File**: `src/cli_rpg/game_state.py`

Add function after `parse_command()` (~line 163):
```python
def calculate_sneak_success_chance(character: "Character") -> int:
    """Calculate sneak success percentage for exploration.

    Formula: 50% + (DEX * 2%) - (armor defense * 5%) - (15% if lit)
    Capped between 10% and 90%.

    Args:
        character: The player character

    Returns:
        Success chance as integer percentage (10-90)
    """
    base_chance = 50
    dex_bonus = character.dexterity * 2

    # Armor penalty
    armor_penalty = 0
    if character.inventory.equipped_armor:
        armor_penalty = character.inventory.equipped_armor.defense_bonus * 5

    # Light penalty
    light_penalty = 15 if character.light_remaining > 0 else 0

    total = base_chance + dex_bonus - armor_penalty - light_penalty
    return max(10, min(90, total))
```

### Step 3: Add exploration sneak handler
**File**: `src/cli_rpg/main.py`

In `handle_exploration_command()`, add handler after the "track" command (~line 1036):
```python
elif command == "sneak":
    from cli_rpg.models.character import CharacterClass
    from cli_rpg.game_state import calculate_sneak_success_chance

    # Rogue-only check
    if game_state.current_character.character_class != CharacterClass.ROGUE:
        return (True, "Only Rogues can sneak past encounters!")

    # Stamina check (10 stamina cost)
    if not game_state.current_character.use_stamina(10):
        stamina = game_state.current_character.stamina
        max_stamina = game_state.current_character.max_stamina
        return (True, f"Not enough stamina to sneak! ({stamina}/{max_stamina})")

    # Enable sneaking mode
    game_state.is_sneaking = True
    success_chance = calculate_sneak_success_chance(game_state.current_character)
    return (True, f"You move carefully into the shadows... ({success_chance}% chance to avoid encounters on next move)")
```

### Step 4: Modify check_for_random_encounter to respect sneaking
**File**: `src/cli_rpg/random_encounters.py`

In `check_for_random_encounter()`, add sneaking check after safe zone check (~line 238):
```python
# Check sneaking mode (Rogue exploration sneak)
if game_state.is_sneaking:
    from cli_rpg.game_state import calculate_sneak_success_chance
    success_chance = calculate_sneak_success_chance(game_state.current_character)
    game_state.is_sneaking = False  # Clear after check (consumed on move)

    if random.random() * 100 < success_chance:
        # Successfully avoided potential encounter
        return None
    # Sneak failed - continue with normal encounter check
```

### Step 5: Clear is_sneaking on move (success or failure)
**File**: `src/cli_rpg/game_state.py`

In `move()` method (~line 389), clear sneaking at the end (for cases where encounter check wasn't triggered):
```python
# At end of move(), before return:
self.is_sneaking = False  # Clear sneaking mode after any move attempt
```

### Step 6: Add to serialization (persistence)
**File**: `src/cli_rpg/game_state.py`

In `to_dict()` method, add:
```python
"is_sneaking": self.is_sneaking,
```

In `from_dict()` method, add:
```python
# In the object creation:
is_sneaking=data.get("is_sneaking", False),
```

### Step 7: Update help text
**File**: `src/cli_rpg/main.py`

In `get_command_reference()` function, add to exploration commands section (~line 69):
```python
"  sneak (sn)    - Move stealthily to avoid encounters (Rogue only, 10 stamina)",
```

## Files Modified
1. `src/cli_rpg/game_state.py` - Add is_sneaking field, calculate_sneak_success_chance(), clear on move, serialization
2. `src/cli_rpg/random_encounters.py` - Check sneaking mode before encounter roll
3. `src/cli_rpg/main.py` - Add exploration sneak command handler, update help
4. `tests/test_exploration_sneak.py` - New test file with ~12 test cases
