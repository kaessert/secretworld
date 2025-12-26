# Implementation Plan: Warrior Bash Command

## Feature Spec

Add `bash` combat command for Warriors that:
- **Costs 15 stamina** (higher than sneak's 10, balanced for powerful stun effect)
- **Deals STR-based damage** (0.75x normal attack damage, so not a straight upgrade)
- **Applies 1-turn stun** to the target enemy (uses existing stun StatusEffect)
- **Warrior-only** (mirrors sneak being Rogue-only)

## Tests (TDD)

Create `tests/test_bash.py`:

1. **test_bash_only_available_to_warrior** - Non-warriors get "Only Warriors can bash!"
2. **test_bash_costs_15_stamina** - Stamina decreases by 15 after bash
3. **test_bash_fails_without_stamina** - Returns error with <15 stamina, stamina unchanged
4. **test_bash_deals_reduced_damage** - Deals 0.75x STR-based damage (reduced from normal attack)
5. **test_bash_applies_stun_to_enemy** - Enemy has stun StatusEffect after bash
6. **test_bash_stun_lasts_1_turn** - Stun duration is 1
7. **test_bash_fails_when_stunned** - Can't bash while player is stunned
8. **test_bash_can_defeat_enemy** - Returns victory=True if enemy dies from bash damage
9. **test_bash_records_action_for_combo** - Action recorded as "bash" in action_history

## Implementation Steps

### 1. Add `player_bash()` method to CombatEncounter

**File**: `src/cli_rpg/combat.py`
**Location**: After `player_sneak()` method (around line 772)

```python
def player_bash(self, target: str = "") -> Tuple[bool, str]:
    """
    Warrior performs a stunning bash attack.

    Deals reduced damage (0.75x) but applies 1-turn stun to enemy.
    Costs 15 stamina. Only Warriors can use this ability.

    Args:
        target: Target enemy name (partial match). Empty = first living enemy.

    Returns:
        Tuple of (victory, message)
    """
    from cli_rpg.models.character import CharacterClass

    # Check if player is stunned
    stun_msg = self._check_and_consume_stun()
    if stun_msg:
        return False, stun_msg

    # Only Warriors can bash
    if self.player.character_class != CharacterClass.WARRIOR:
        return False, "Only Warriors can bash!"

    # Check stamina cost (15 stamina)
    if not self.player.use_stamina(15):
        return False, f"Not enough stamina! ({self.player.stamina}/{self.player.max_stamina})"

    # Get target enemy
    enemy, error = self._get_target(target)
    if enemy is None:
        return False, error or "No target found."

    # Record action for combo tracking
    self._record_action("bash")

    # Calculate damage: 0.75x normal attack, minimum 1
    base_dmg = max(1, self.player.get_attack_power() - enemy.defense)
    dmg = max(1, int(base_dmg * 0.75))
    enemy.take_damage(dmg)

    # Apply stun effect to enemy (1 turn)
    stun = StatusEffect(
        name="Stun",
        effect_type="stun",
        damage_per_turn=0,
        duration=1
    )
    enemy.apply_status_effect(stun)

    message = (
        f"You {colors.damage('BASH')} {colors.enemy(enemy.name)} for "
        f"{colors.damage(str(dmg))} damage and {colors.warning('stun')} them!"
    )

    if not enemy.is_alive():
        message += f"\n{colors.enemy(enemy.name)} has been defeated!"

    # Check if all enemies are dead
    if not self.get_living_enemies():
        message += f" {colors.heal('Victory!')}"
        return True, message

    if enemy.is_alive():
        message += f"\n{colors.enemy(enemy.name)} has {enemy.health}/{enemy.max_health} HP remaining."

    return False, message
```

### 2. Add "bash" to KNOWN_COMMANDS

**File**: `src/cli_rpg/game_state.py`
**Location**: Line 53
**Change**: Add "bash" to KNOWN_COMMANDS set (after "block")

### 3. Add "ba" alias

**File**: `src/cli_rpg/game_state.py`
**Location**: aliases dict (line 118)
**Change**: Add `"ba": "bash"` to aliases

### 4. Add bash command handler

**File**: `src/cli_rpg/main.py`
**Location**: After sneak handler (around line 391)

```python
elif command == "bash":
    # Parse target from args
    target = " ".join(args) if args else ""
    victory, message = combat.player_bash(target=target)
    output = f"\n{message}"

    if victory:
        # Same victory handling as attack/cast
        for enemy in combat.enemies:
            game_state.current_character.record_enemy_defeat(enemy)
        end_message = combat.end_combat(victory=True)
        output += f"\n{end_message}"
        for enemy in combat.enemies:
            quest_messages = game_state.current_character.record_kill(enemy.name)
            for msg in quest_messages:
                output += f"\n{msg}"
            game_state.record_choice(...)
        # ... companion reactions, invasion check, autosave ...
        game_state.current_combat = None
    else:
        # If bash succeeded (not an error message), enemies attack back
        if "Only Warriors" not in message and "Not enough stamina" not in message and "stunned" not in message.lower():
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

    return (True, output)
```

### 5. Update combat help text

**File**: `src/cli_rpg/main.py`
**Location**: `get_command_reference()` (around line 83)
**Change**: Add after sneak:

```python
"  bash (ba) [target] - Stun an enemy (Warrior only, 15 stamina)",
```

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/combat.py` | Add `player_bash()` method (~45 lines) |
| `src/cli_rpg/game_state.py` | Add "bash" to KNOWN_COMMANDS, add "ba" alias |
| `src/cli_rpg/main.py` | Add command handler (~40 lines), add help text |
| `tests/test_bash.py` | New test file (~150 lines) |

## Verification

```bash
pytest tests/test_bash.py -v
pytest tests/test_combat.py -v  # Ensure no regressions
pytest  # Full suite
```
