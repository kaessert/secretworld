# Implementation Plan: Block Combat Command

## Spec

**Block Command**: A new combat action that allows players to prepare for incoming attacks, reducing damage taken at the cost of their action. Unlike `defend` (which halves damage), `block` provides a stronger damage reduction but requires stamina.

**Mechanics**:
- Costs 5 stamina to use
- Reduces incoming damage by 75% (vs defend's 50%)
- Like defend, resets after enemy turn
- Requires stamina check - fails if insufficient stamina
- Works within the existing combo system (counts as a distinct action, not "defend")

**Justification**: Block is a more active defensive action requiring resource management (stamina), giving players meaningful tactical choices between:
- `defend`: Free, 50% reduction, available always
- `block`: 5 stamina, 75% reduction, more protective

## Tests (TDD)

Add to `tests/test_combat.py`:

```python
class TestPlayerBlock:
    """Test player_block() method."""

    def test_player_block_sets_blocking_stance(self):
        """Spec: player_block() should set blocking stance for 75% damage reduction."""
        # Create combat, call player_block()
        # Assert blocking is True
        # Assert message mentions "block"

    def test_player_block_costs_5_stamina(self):
        """Spec: player_block() should cost 5 stamina."""
        # Create combat, note initial stamina
        # Call player_block()
        # Assert stamina reduced by 5

    def test_player_block_fails_without_stamina(self):
        """Spec: player_block() should fail if player has < 5 stamina."""
        # Create combat, set player stamina to 3
        # Call player_block()
        # Assert failure message, blocking is False
        # Assert stamina unchanged

    def test_block_reduces_damage_by_75_percent(self):
        """Spec: Blocking should reduce incoming damage by 75%."""
        # Create combat with known enemy attack
        # Set combat.blocking = True
        # Call enemy_turn() with mocked random
        # Assert damage = max(1, base_damage // 4)

    def test_block_resets_after_enemy_turn(self):
        """Spec: Blocking stance should reset after enemy turn."""
        # Create combat, set blocking = True
        # Call enemy_turn()
        # Assert blocking is False

    def test_player_block_fails_when_stunned(self):
        """Spec: player_block() should fail if player is stunned."""
        # Create combat, apply stun effect
        # Call player_block()
        # Assert stun message, blocking not set
```

## Implementation Steps

### 1. Add `blocking` attribute to CombatEncounter

**File**: `src/cli_rpg/combat.py`
**Location**: `CombatEncounter.__init__` (around line 350)
**Change**: Add `self.blocking = False` alongside existing `self.defending = False`

### 2. Add `player_block()` method to CombatEncounter

**File**: `src/cli_rpg/combat.py`
**Location**: After `player_defend()` method (around line 701)
**Change**: Add new method:

```python
def player_block(self) -> Tuple[bool, str]:
    """
    Player actively blocks incoming attacks.

    Costs 5 stamina. Reduces incoming damage by 75% (vs defend's 50%).

    Returns:
        Tuple of (victory, message)
        - victory: Always False (combat continues)
        - message: Description of block action or error
    """
    # Check if player is stunned
    stun_msg = self._check_and_consume_stun()
    if stun_msg:
        return False, stun_msg

    # Check stamina cost (5 stamina)
    if not self.player.use_stamina(5):
        return False, f"Not enough stamina to block! ({self.player.stamina}/{self.player.max_stamina})"

    # Record action for combo tracking
    self._record_action("block")

    self.blocking = True
    message = "You raise your guard, bracing to block the enemy's attack!"
    return False, message
```

### 3. Update `enemy_turn()` to handle blocking

**File**: `src/cli_rpg/combat.py`
**Location**: In `enemy_turn()` method, after defending check (around line 922-935)
**Change**: Add blocking check before defending check:

```python
# Apply block reduction (75%) if player is blocking
if self.blocking:
    dmg = max(1, base_damage // 4)  # 75% reduction
    # Track for Revenge combo
    self.damage_taken_while_defending += dmg
    if is_crit:
        msg = (
            f"{colors.damage('CRITICAL HIT!')} {colors.enemy(enemy.name)} attacks! "
            f"You block the blow, taking only {colors.damage(str(dmg))} damage!"
        )
    else:
        msg = (
            f"{colors.enemy(enemy.name)} attacks! You block the blow, "
            f"taking only {colors.damage(str(dmg))} damage!"
        )
# Apply defense reduction if player is defending (50%)
elif self.defending:
    # ... existing code ...
```

### 4. Reset blocking after enemy turn

**File**: `src/cli_rpg/combat.py`
**Location**: End of `enemy_turn()` (around line 1044)
**Change**: Add `self.blocking = False` alongside `self.defending = False`

### 5. Add "block" to KNOWN_COMMANDS

**File**: `src/cli_rpg/game_state.py`
**Location**: KNOWN_COMMANDS set (line 53)
**Change**: Add "block" to the set

### 6. Add "bl" alias

**File**: `src/cli_rpg/game_state.py`
**Location**: aliases dict (line 117-118)
**Change**: Add `"bl": "block"` to aliases

### 7. Add block command handler in main.py

**File**: `src/cli_rpg/main.py`
**Location**: In `handle_combat_command()` after the defend handler (around line 350)
**Change**: Add handler similar to defend:

```python
elif command == "block":
    _, message = combat.player_block()
    output = f"\n{message}"

    # If block failed (not enough stamina), don't trigger enemy turn
    if "Not enough stamina" not in message and "stunned" not in message.lower():
        # Enemy attacks
        enemy_message = combat.enemy_turn()
        output += f"\n{enemy_message}"

        # Check if player died
        if not game_state.current_character.is_alive():
            death_message = combat.end_combat(victory=False)
            output += f"\n{death_message}"
            output += "\n\n=== GAME OVER ==="
            sound_death()
            game_state.current_combat = None

    return (True, output)
```

### 8. Update combat help text

**File**: `src/cli_rpg/main.py`
**Location**: `get_command_reference()` combat commands section (around line 78-79)
**Change**: Add block command to help:

```python
"  block (bl)    - Actively block attacks (5 stamina, 75% reduction)",
```

### 9. Update combat command lists

**File**: `src/cli_rpg/main.py`
**Locations**:
- Line 533: combat_commands set (add "block")
- Lines 538, 541: Error message strings (add "block")
- Line 1875: get_available_commands() return list (add "block")

### 10. Clear blocking state at combat end

**File**: `src/cli_rpg/combat.py`
**Location**: In `end_combat()` method
**Change**: Ensure blocking is reset (should happen via __init__ on next combat)

## Verification

Run tests:
```bash
pytest tests/test_combat.py -v -k "block"
pytest tests/test_combat.py -v  # Full suite to ensure no regressions
```
