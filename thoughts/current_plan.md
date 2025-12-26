# Mage-Specific Spells Implementation Plan

## Summary
Implement Mage-exclusive spells (`fireball`, `ice_bolt`, `heal`) to leverage the existing mana system and give Mages their unique playstyle. Currently the `cast` command is a generic magic attack for all classes - Mages should have access to more powerful, specialized spells.

## Spec

### Mage Spells (Mage-only abilities)
1. **Fireball** (`fireball` / `fb`)
   - Mage-only spell
   - Cost: 20 mana
   - Damage: INT × 2.5 (ignores defense like `cast`)
   - Effect: 25% chance to apply Burn (5 damage/turn, 2 turns)

2. **Ice Bolt** (`ice_bolt` / `ib`)
   - Mage-only spell
   - Cost: 15 mana
   - Damage: INT × 2.0 (ignores defense)
   - Effect: 30% chance to apply Freeze (50% attack reduction, 2 turns) to enemy

3. **Heal** (`heal` / `hl`)
   - Mage-only spell
   - Cost: 25 mana
   - Effect: Heals player for INT × 2 HP (capped at max_health)
   - Can be used in combat (takes player's action, enemy still attacks)

### Design Decisions
- Basic `cast` remains available to all classes (10 mana, INT × 1.5 damage)
- Mage spells are more powerful but cost more mana (leveraging Mage's larger mana pool)
- Spells can trigger enemy status effects (burn, freeze) like enemy attacks do
- Follows existing patterns from `bash` (Warrior-only) and `sneak` (Rogue-only)

## Tests to Write (TDD)

### File: `tests/test_mage_spells.py`

```python
# 1. Fireball class restriction
def test_fireball_mage_only()  # Non-mages get "Only Mages can cast Fireball!"

# 2. Fireball mana cost
def test_fireball_costs_20_mana()  # Deducts 20 mana on use
def test_fireball_fails_without_mana()  # Returns error when mana < 20

# 3. Fireball damage
def test_fireball_deals_int_times_2_5_damage()  # INT=10 → 25 damage
def test_fireball_ignores_enemy_defense()  # Full damage regardless of defense

# 4. Fireball burn effect
def test_fireball_can_apply_burn()  # 25% chance to apply Burn status

# 5. Ice Bolt class restriction
def test_ice_bolt_mage_only()  # Non-mages get error

# 6. Ice Bolt mana cost
def test_ice_bolt_costs_15_mana()
def test_ice_bolt_fails_without_mana()

# 7. Ice Bolt damage
def test_ice_bolt_deals_int_times_2_damage()

# 8. Ice Bolt freeze effect
def test_ice_bolt_can_apply_freeze()  # 30% chance to apply Freeze

# 9. Heal class restriction
def test_heal_mage_only()

# 10. Heal mana cost
def test_heal_costs_25_mana()
def test_heal_fails_without_mana()

# 11. Heal effect
def test_heal_restores_int_times_2_hp()
def test_heal_capped_at_max_health()
def test_heal_fails_at_full_health()

# 12. Combat integration
def test_spells_trigger_enemy_turn()  # Enemy attacks after spell cast
def test_spells_can_defeat_enemy()  # Victory condition
def test_stunned_mage_cannot_cast_spells()  # Stun blocks spells

# 13. Combo system
def test_fireball_records_cast_action()  # Counts toward Arcane Burst
def test_ice_bolt_records_cast_action()  # Counts toward Arcane Burst
```

## Implementation Steps

### 1. Add spell methods to `CombatEncounter` in `src/cli_rpg/combat.py`

```python
def player_fireball(self, target: str = "") -> Tuple[bool, str]:
    """Mage casts Fireball - high damage with burn chance."""
    # Check class restriction
    # Check mana (20)
    # Calculate damage (INT × 2.5)
    # Apply burn effect (25% chance)
    # Record 'cast' action for combo tracking

def player_ice_bolt(self, target: str = "") -> Tuple[bool, str]:
    """Mage casts Ice Bolt - damage with freeze chance."""
    # Similar pattern, 15 mana, INT × 2.0, 30% freeze

def player_heal(self) -> Tuple[bool, str]:
    """Mage casts Heal - restore health."""
    # Check class restriction
    # Check mana (25)
    # Check not at full health
    # Heal INT × 2 HP
    # Record 'cast' action
```

### 2. Add command handlers in `src/cli_rpg/main.py`

In `handle_combat_command()`:
```python
elif command == "fireball":
    # Parse target, call combat.player_fireball()
    # Handle victory/defeat/continue combat flow

elif command == "ice_bolt":
    # Same pattern

elif command == "heal":
    # Call combat.player_heal()
    # Trigger enemy turn after heal
```

### 3. Update command parsing in `src/cli_rpg/main.py`

In `parse_command()` add shorthand aliases:
- `fb` → `fireball`
- `ib` → `ice_bolt`
- `hl` → `heal`

### 4. Update help text in `src/cli_rpg/main.py`

Add to combat commands section:
```
"  fireball (fb) [target] - Cast Fireball (Mage only, 20 mana)",
"  ice_bolt (ib) [target] - Cast Ice Bolt (Mage only, 15 mana)",
"  heal (hl)     - Cast Heal on self (Mage only, 25 mana)",
```

### 5. Update combat command list

Add `fireball`, `ice_bolt`, `heal` to:
- `combat_commands` set in unknown command handling
- `get_available_commands()` for JSON mode

## Files to Modify

1. `src/cli_rpg/combat.py` - Add `player_fireball()`, `player_ice_bolt()`, `player_heal()`
2. `src/cli_rpg/main.py` - Add command handlers, shortcuts, help text
3. `tests/test_mage_spells.py` - New test file

## Order of Implementation

1. Write tests in `tests/test_mage_spells.py`
2. Add spell methods to `combat.py`
3. Add command handlers to `main.py`
4. Run tests to verify
