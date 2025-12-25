# Implementation Plan: Combo Combat System

## Overview
Add a combo system to combat that tracks the player's last 2-3 actions and unlocks special combo moves when specific action chains are performed. This addresses the "Combat lacks tactical depth - players just attack repeatedly" issue by rewarding strategic action sequencing.

## Specification

### Combo Definitions (MVP - 3 Combos)
| Combo Name | Sequence | Effect |
|------------|----------|--------|
| **Frenzy** | Attack → Attack → Attack | Triple attack: deal 3 smaller hits totaling 1.5x normal damage |
| **Revenge** | Defend → Defend → Attack | Counter-attack: deal damage equal to damage taken while defending |
| **Arcane Burst** | Cast → Cast → Cast | Empowered spell: deal 2x magic damage |

### Action History Tracking
- Track last 3 combat actions in `CombatEncounter.action_history: list[str]`
- Valid actions: `"attack"`, `"defend"`, `"cast"`, `"flee"`, `"use"`
- History resets when combat ends
- History persists during combat (not across save/load - combat isn't saved mid-fight)

### Combo Detection & Execution
- After each action, check if `action_history[-3:]` matches a combo pattern
- If combo available, show notification: `"COMBO AVAILABLE: Frenzy - Your next attack will strike 3 times!"`
- Combo triggers on the next matching action (Attack for Frenzy, Attack for Revenge, Cast for Arcane Burst)
- Once combo triggers, history resets and combo effect applies

### Combo State Machine
1. Player takes action → action recorded in history
2. Check for pending combo match
3. If pending combo exists and action matches trigger → execute combo, clear history
4. If no match → normal action, keep building history
5. If action breaks chain (flee/use) → clear history

---

## Tests (TDD - write before implementation)

### File: `tests/test_combo_combat.py`

#### Action History Tracking
1. `test_combat_encounter_has_action_history` - CombatEncounter has action_history attribute (empty list)
2. `test_attack_records_action` - player_attack() adds "attack" to action_history
3. `test_defend_records_action` - player_defend() adds "defend" to action_history
4. `test_cast_records_action` - player_cast() adds "cast" to action_history
5. `test_flee_clears_history` - player_flee() clears action_history (breaks combo)
6. `test_action_history_max_length` - History never exceeds 3 entries (oldest dropped)
7. `test_end_combat_clears_history` - end_combat() clears action_history

#### Combo Detection
8. `test_detect_frenzy_combo` - After Attack→Attack→Attack, `get_pending_combo()` returns "frenzy"
9. `test_detect_revenge_combo` - After Defend→Defend→Attack, `get_pending_combo()` returns "revenge"
10. `test_detect_arcane_burst_combo` - After Cast→Cast→Cast, `get_pending_combo()` returns "arcane_burst"
11. `test_no_combo_partial_sequence` - After Attack→Attack, `get_pending_combo()` returns None
12. `test_no_combo_broken_sequence` - After Attack→Defend→Attack, `get_pending_combo()` returns None

#### Combo Execution - Frenzy
13. `test_frenzy_deals_bonus_damage` - Frenzy attack deals 1.5x total damage via 3 hits
14. `test_frenzy_clears_after_trigger` - After Frenzy triggers, action_history is cleared
15. `test_frenzy_message_shows_triple_hit` - Frenzy attack message mentions "strikes three times"

#### Combo Execution - Revenge
16. `test_revenge_tracks_damage_taken` - Damage taken during defend actions is tracked
17. `test_revenge_deals_damage_equal_to_taken` - Revenge attack deals damage = damage taken while defending
18. `test_revenge_resets_damage_counter` - After Revenge triggers, damage counter resets

#### Combo Execution - Arcane Burst
19. `test_arcane_burst_double_damage` - Arcane Burst cast deals 2x magic damage
20. `test_arcane_burst_message` - Message mentions "arcane energy explodes"

#### Combo UI Notifications
21. `test_combo_available_notification` - When combo is pending, status shows "COMBO AVAILABLE: ..."
22. `test_get_status_shows_action_history` - Combat status shows "Last actions: [Attack] → [Defend]"

---

## Implementation Steps

### Step 1: Add Action History to CombatEncounter
**File**: `src/cli_rpg/combat.py`

Add to `CombatEncounter.__init__()`:
```python
self.action_history: list[str] = []
self.damage_taken_while_defending: int = 0  # For Revenge combo
self.pending_combo: Optional[str] = None
```

Add combo definitions:
```python
COMBOS = {
    "frenzy": {"sequence": ["attack", "attack", "attack"], "trigger": "attack"},
    "revenge": {"sequence": ["defend", "defend", "attack"], "trigger": "attack"},
    "arcane_burst": {"sequence": ["cast", "cast", "cast"], "trigger": "cast"},
}
```

### Step 2: Add Action Recording Methods
**File**: `src/cli_rpg/combat.py`

```python
def _record_action(self, action: str) -> None:
    """Record a combat action in history."""
    self.action_history.append(action)
    if len(self.action_history) > 3:
        self.action_history.pop(0)
    self._check_for_combo()

def _check_for_combo(self) -> None:
    """Check if current action history matches a combo."""
    for combo_name, combo_def in COMBOS.items():
        if self.action_history == combo_def["sequence"]:
            self.pending_combo = combo_name
            return
    self.pending_combo = None

def get_pending_combo(self) -> Optional[str]:
    """Get the currently pending combo, if any."""
    return self.pending_combo

def _clear_action_history(self) -> None:
    """Clear action history and pending combo."""
    self.action_history.clear()
    self.pending_combo = None
    self.damage_taken_while_defending = 0
```

### Step 3: Modify player_attack() for Frenzy and Revenge
**File**: `src/cli_rpg/combat.py`

In `player_attack()`:
```python
# Check for Frenzy combo
if self.pending_combo == "frenzy":
    # Triple hit for 1.5x total damage
    single_hit = max(1, (self.player.get_attack_power() - enemy.defense) // 2)
    total_damage = single_hit * 3
    enemy.take_damage(total_damage)
    message = f"FRENZY! You strike {enemy.name} three times for {total_damage} total damage!"
    self._clear_action_history()
    # ... rest of victory check

# Check for Revenge combo
elif self.pending_combo == "revenge":
    revenge_damage = max(1, self.damage_taken_while_defending)
    enemy.take_damage(revenge_damage)
    message = f"REVENGE! You channel your pain into a devastating counter for {revenge_damage} damage!"
    self._clear_action_history()
    # ... rest of victory check
else:
    # Normal attack
    self._record_action("attack")
    # ... existing attack logic
```

### Step 4: Modify player_defend() for Revenge Tracking
**File**: `src/cli_rpg/combat.py`

In `player_defend()`:
```python
self._record_action("defend")
# ... existing defend logic
```

In `enemy_turn()` when player is defending:
```python
if self.defending:
    dmg = max(1, base_damage // 2)
    self.damage_taken_while_defending += dmg  # Track for Revenge combo
```

### Step 5: Modify player_cast() for Arcane Burst
**File**: `src/cli_rpg/combat.py`

In `player_cast()`:
```python
if self.pending_combo == "arcane_burst":
    # Double magic damage
    dmg = max(1, int(self.player.intelligence * 1.5) * 2)
    enemy.take_damage(dmg)
    message = f"ARCANE BURST! Magical energy explodes around {enemy.name} for {dmg} damage!"
    self._clear_action_history()
else:
    # Normal cast
    self._record_action("cast")
    # ... existing cast logic
```

### Step 6: Clear History on Flee/Use
**File**: `src/cli_rpg/combat.py`

In `player_flee()`:
```python
self._clear_action_history()  # Flee breaks combo chain
# ... existing flee logic
```

### Step 7: Update Combat Status Display
**File**: `src/cli_rpg/combat.py`

In `get_status()`:
```python
# Add action history display
if self.action_history:
    actions_display = " → ".join(f"[{a.capitalize()}]" for a in self.action_history)
    lines.append(f"Last actions: {actions_display}")

# Add pending combo notification
if self.pending_combo:
    combo_name = self.pending_combo.replace("_", " ").title()
    lines.append(f"COMBO AVAILABLE: {combo_name}!")
```

### Step 8: Update end_combat()
**File**: `src/cli_rpg/combat.py`

In `end_combat()`:
```python
self._clear_action_history()  # Reset for next combat
# ... existing end_combat logic
```

---

## Files Modified
1. `src/cli_rpg/combat.py` - Main combo logic
2. `tests/test_combo_combat.py` - New test file

## Files NOT Modified
- `src/cli_rpg/game_state.py` - No changes needed (combat handled in CombatEncounter)
- `src/cli_rpg/main.py` - No changes needed (uses existing combat methods)
- `src/cli_rpg/models/character.py` - No changes needed
- Persistence files - Combat state is not persisted mid-fight
