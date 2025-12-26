# Implementation Plan: Cleric Class Abilities

## Feature Spec

Cleric class abilities to complete the class system alongside Warrior (bash), Mage (fireball/ice_bolt/heal), Rogue (sneak/pick), and Ranger (track + wilderness bonus):

1. **`bless` command** (combat): Cleric buffs party with attack bonus
   - Costs 20 mana
   - Applies "Blessed" status effect (+25% attack damage) for 3 turns
   - Affects player and all companions
   - Only Clerics can use this ability
   - Can only be used in combat

2. **`smite` command** (combat): Cleric deals holy damage, extra effective vs undead
   - Costs 15 mana
   - Base damage: INT * 2.5
   - Bonus vs undead: double damage (INT * 5.0)
   - 30% chance to stun undead for 1 turn
   - Only Clerics can use this ability
   - Can only be used in combat

3. **Cleric max mana**: Use Mage-like mana scaling (50 + INT * 5)

---

## Phase 1: Tests (TDD)

### Create `tests/test_cleric.py`

Test cases for `bless` command:
- `test_bless_only_available_to_cleric` - Other classes get "Only Clerics can bless!"
- `test_bless_costs_20_mana` - Mana decreases by 20
- `test_bless_fails_without_mana` - Returns error with <20 mana
- `test_bless_applies_buff_to_player` - Player has "Blessed" effect with +25% attack
- `test_bless_applies_buff_to_companions` - All companions receive "Blessed" effect
- `test_bless_buff_lasts_3_turns` - Duration is 3 turns
- `test_bless_only_usable_in_combat` - Cannot use outside combat

Test cases for `smite` command:
- `test_smite_only_available_to_cleric` - Other classes get "Only Clerics can smite!"
- `test_smite_costs_15_mana` - Mana decreases by 15
- `test_smite_fails_without_mana` - Returns error with <15 mana
- `test_smite_deals_int_based_damage` - Damage scales with INT
- `test_smite_deals_double_damage_to_undead` - 2x multiplier for undead enemies
- `test_smite_can_stun_undead` - 30% chance to apply stun to undead
- `test_smite_no_stun_to_living` - No stun chance for non-undead

Test cases for Cleric mana:
- `test_cleric_has_mage_like_max_mana` - 50 + INT * 5 formula

---

## Phase 2: Implementation

### 2.1 Update Cleric max mana in character.py

In `__post_init__` (line ~146-153), add CLERIC to high-mana classes:
```python
if self.character_class in (CharacterClass.MAGE, CharacterClass.CLERIC):
    self.max_mana = 50 + self.intelligence * 5
```

### 2.2 Create `src/cli_rpg/cleric.py` module

```python
"""Cleric class abilities: bless party buff and smite undead."""

BLESS_MANA_COST = 20
BLESS_DURATION = 3
BLESS_ATTACK_MODIFIER = 0.25

SMITE_MANA_COST = 15
SMITE_DAMAGE_MULTIPLIER = 2.5
SMITE_UNDEAD_MULTIPLIER = 5.0
SMITE_UNDEAD_STUN_CHANCE = 0.30

UNDEAD_TERMS = {"skeleton", "zombie", "ghost", "wraith", "undead", "specter", "lich", "vampire"}

def is_undead(enemy_name: str) -> bool:
    """Check if enemy name indicates undead creature."""
    name_lower = enemy_name.lower()
    return any(term in name_lower for term in UNDEAD_TERMS)
```

### 2.3 Add bless and smite methods to combat.py

After `player_heal()` (line ~1141), add:

**player_bless()**:
- Check class is CLERIC
- Check mana >= 20
- Use mana
- Create StatusEffect("Blessed", "buff_attack", 0, 3, 0.25)
- Apply to self.player
- Apply to each companion in self.game_state.companions
- Return message describing blessing

**player_smite(target: str = "")**:
- Check class is CLERIC
- Check not stunned
- Check mana >= 15
- Use mana
- Get target via _get_target()
- Calculate damage: INT * 2.5 (or 5.0 if undead)
- Apply damage
- If undead and random.random() < 0.30: apply stun effect
- Check victory
- Return tuple with victory status and message

### 2.4 Add commands to game_state.py

1. Add `"bless", "smite"` to `KNOWN_COMMANDS` set (line ~54)
2. Add aliases in `parse_command()` (line ~118-133):
   ```python
   "bl": "bless",
   "sm": "smite",
   ```

### 2.5 Add command handlers to main.py

1. Add `"bless", "smite"` to `combat_commands` set (line ~782)

2. Add dispatch blocks after ice_bolt/heal handling (~640-700):

```python
elif command == "bless":
    victory, message = combat.player_bless()
    output = f"\n{message}"
    if victory:
        # Handle victory (same pattern as other abilities)
    else:
        if not message.startswith("Only Clerics") and "Not enough mana" not in message:
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

elif command == "smite":
    target = " ".join(args) if args else ""
    victory, message = combat.player_smite(target=target)
    # Same victory/enemy turn handling as fireball
```

### 2.6 Update help text in main.py

Add to `get_command_reference()` combat commands section:
```
"  bless (bl)       - Bless party with +25% attack (Cleric only, 20 mana)",
"  smite (sm) [target] - Holy damage, 2x vs undead (Cleric only, 15 mana)",
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `tests/test_cleric.py` | CREATE | Unit tests for bless, smite, and mana |
| `src/cli_rpg/cleric.py` | CREATE | Cleric-specific abilities module |
| `src/cli_rpg/models/character.py` | MODIFY | Add CLERIC to high-mana classes |
| `src/cli_rpg/game_state.py` | MODIFY | Add "bless", "smite" to KNOWN_COMMANDS + aliases |
| `src/cli_rpg/main.py` | MODIFY | Add command handlers, update help, add to combat_commands |
| `src/cli_rpg/combat.py` | MODIFY | Add player_bless() and player_smite() methods |

---

## Implementation Order

1. Write tests first (`tests/test_cleric.py`)
2. Update character.py for Cleric mana scaling
3. Create cleric.py with constants and is_undead() helper
4. Add player_bless() and player_smite() to combat.py
5. Add commands to KNOWN_COMMANDS and aliases in game_state.py
6. Wire up command handlers in main.py
7. Update help text
8. Run tests to verify
