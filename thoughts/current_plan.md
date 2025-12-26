# Implementation Plan: `hide` Command in Combat

## Feature Spec
Add `hide` combat command that makes the player untargetable for 1 turn (enemies skip attacking them). Uses the player's action and costs stamina. Any class can use it (not Rogue-only like sneak).

**Mechanics:**
- Costs 10 stamina (same as sneak)
- Applies "Hidden" status effect (`effect_type="hidden"`, duration=1)
- While hidden: enemies skip attacking this target in `enemy_turn()`
- Hidden is consumed after enemy turn (duration ticks down)
- Costs the player's action (enemy turn still happens)

## Implementation Steps

### 1. Add `is_hidden()` helper to Character model
**File:** `src/cli_rpg/models/character.py`

Add after `consume_stealth()` method (~line 786):
```python
def is_hidden(self) -> bool:
    """Check if character has an active hidden effect.

    Returns:
        True if character has a hidden effect, False otherwise.
    """
    return any(e.effect_type == "hidden" for e in self.status_effects)
```

### 2. Add `player_hide()` method to CombatEncounter
**File:** `src/cli_rpg/combat.py`

Add method after `player_sneak()` (~line 809):
```python
def player_hide(self) -> Tuple[bool, str]:
    """
    Player hides to become untargetable for 1 turn.

    Costs 10 stamina. Applies "Hidden" status effect that makes
    enemies skip attacking the player for 1 turn.

    Returns:
        Tuple of (victory, message)
        - victory: Always False (combat continues)
        - message: Description of hide action or error message
    """
    # Check if player is stunned
    stun_msg = self._check_and_consume_stun()
    if stun_msg:
        return False, stun_msg

    # Check stamina cost (10 stamina)
    if not self.player.use_stamina(10):
        return False, f"Not enough stamina! ({self.player.stamina}/{self.player.max_stamina})"

    # Record action for combo tracking
    self._record_action("hide")

    # Apply hidden effect (duration 1: lasts through enemy turn)
    hidden_effect = StatusEffect(
        name="Hidden",
        effect_type="hidden",
        damage_per_turn=0,
        duration=1,
        stat_modifier=0.0
    )
    self.player.apply_status_effect(hidden_effect)

    return False, "You duck into cover, becoming harder to target!"
```

### 3. Modify `enemy_turn()` to skip attacking hidden players
**File:** `src/cli_rpg/combat.py`

At the start of the enemy loop in `enemy_turn()` (~line 1403), add check before processing enemies:
```python
# Check if player is hidden (untargetable this turn)
if self.player.is_hidden():
    messages.append("You remain hidden as enemies search for you...")
    # Tick status effects (hidden will expire)
    status_messages = self.player.tick_status_effects()
    messages.extend(status_messages)
    # Still tick enemy status effects
    for enemy in living:
        enemy_status_messages = enemy.tick_status_effects()
        messages.extend(enemy_status_messages)
    # Still regenerate stamina
    self.player.regen_stamina(1)
    return "\n".join(messages) + f"\nYou have {self.player.health}/{self.player.max_health} HP remaining."
```

### 4. Add command alias in game_state.py
**File:** `src/cli_rpg/game_state.py`

Add to `COMMAND_ALIASES` dict:
```python
"hd": "hide",
```

Add to `KNOWN_COMMANDS` set:
```python
"hide",
```

### 5. Wire up `hide` command in main.py
**File:** `src/cli_rpg/main.py`

Add command handler after the `sneak` handler (~line 476):
```python
elif command == "hide":
    victory, message = combat.player_hide()
    output = f"\n{message}"

    # If hide failed (not enough stamina or stunned), don't trigger enemy turn
    if "Not enough stamina" not in message and "stunned" not in message.lower():
        # Enemy turn
        enemy_turn_message = combat.enemy_turn()
        output += f"\n\n{enemy_turn_message}"

        # Check if player died
        if not player.is_alive():
            output += f"\n\n{combat.end_combat(victory=False)}"
            sound_death()
            game_state.current_combat = None

    return (True, output)
```

Update combat commands set (~line 952):
```python
combat_commands = {"attack", "defend", "block", "cast", "fireball", "ice_bolt", "heal", "bless", "smite", "flee", "sneak", "bash", "hide", "stance", "use", "status", "help", "quit"}
```

Update error message (~line 957):
```python
return (True, "\n✗ Can't do that during combat! Use: attack, defend, block, cast, flee, sneak, hide, use, status, help, or quit")
```

Update available commands (~line 2358):
```python
return ["attack", "defend", "block", "cast", "flee", "hide", "use", "status", "help", "quit"]
```

### 6. Update help text
**File:** `src/cli_rpg/main.py`

In `get_command_reference()` function, add to combat commands section:
```python
hide                 - Hide to become untargetable for 1 turn (10 stamina)
```

## Test Plan

**File:** `tests/test_hide.py` (new file)

Tests to implement:
1. `test_hide_applies_hidden_effect` - Hide command applies hidden status effect
2. `test_hide_works_for_all_classes` - All 5 classes can use hide (parametrized)
3. `test_hide_costs_stamina` - Hide costs 10 stamina
4. `test_hide_fails_without_stamina` - Hide fails if <10 stamina
5. `test_hidden_player_not_attacked` - Enemies skip attacking hidden player
6. `test_hidden_expires_after_enemy_turn` - Hidden effect expires after 1 turn
7. `test_hide_blocked_when_stunned` - Cannot hide while stunned
8. `test_is_hidden_returns_true_when_hidden` - Character.is_hidden() works correctly

## Files Modified

1. `src/cli_rpg/models/character.py` - Add `is_hidden()` method
2. `src/cli_rpg/combat.py` - Add `player_hide()` method, modify `enemy_turn()`
3. `src/cli_rpg/game_state.py` - Add alias and to KNOWN_COMMANDS
4. `src/cli_rpg/main.py` - Wire up hide command, update help text
5. `tests/test_hide.py` - New test file (8 tests)
