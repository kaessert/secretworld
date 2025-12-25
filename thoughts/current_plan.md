# Implementation Plan: Bleed Status Effect

## Spec
Add "Bleed" damage-over-time effect following the established poison/burn pattern:
- **Effect type**: DOT (like poison/burn)
- **Bleed chance**: 20% on attack
- **Bleed damage**: 3 per turn (lower than burn's 5, similar to poison's 4)
- **Bleed duration**: 4 turns (longer than burn's 2, slightly longer than poison's 3)
- **Thematic enemies**: Slashing/claw-based enemies (wolf, bear, lion, cat, blade, claw, razor, fang)

## Tests First (TDD)
Add tests to `tests/test_status_effects.py`:

1. **TestBleedStatusEffect class**:
   - `test_bleed_effect_creation` - Verify Bleed DOT effect with expected values
   - `test_bleed_effect_tick_deals_damage` - Verify 3 damage per turn
   - `test_bleed_effect_expires_correctly` - Verify 4 turn duration

2. **TestEnemyBleed class**:
   - `test_enemy_with_bleed_fields` - Verify enemy can have bleed_chance, bleed_damage, bleed_duration
   - `test_enemy_default_no_bleed` - Non-bleed enemies have 0 defaults
   - `test_enemy_bleed_serialization` - Verify to_dict/from_dict round-trip

3. **TestCombatBleed class**:
   - `test_bleed_applies_in_combat` - Enemy with 100% bleed_chance applies Bleed
   - `test_bleed_ticks_during_enemy_turn` - Bleed deals damage each turn

## Implementation Steps

### 1. Enemy model (`src/cli_rpg/models/enemy.py`)
- Add fields after freeze fields (lines 33-34):
  ```python
  bleed_chance: float = 0.0  # Chance (0.0-1.0) to apply bleed on attack
  bleed_damage: int = 0  # Damage per turn if bleed is applied
  bleed_duration: int = 0  # Duration of bleed in turns
  ```
- Add to `to_dict()` method (after freeze serialization ~line 154)
- Add to `from_dict()` method (after freeze deserialization ~line 197)

### 2. Combat system (`src/cli_rpg/combat.py`)
- In `enemy_turn()` method, add bleed application after freeze check (~line 549):
  ```python
  # Check if enemy can apply bleed
  if enemy.bleed_chance > 0 and random.random() < enemy.bleed_chance:
      bleed = StatusEffect(
          name="Bleed",
          effect_type="dot",
          damage_per_turn=enemy.bleed_damage,
          duration=enemy.bleed_duration
      )
      self.player.apply_status_effect(bleed)
      messages.append(
          f"{colors.enemy(enemy.name)}'s attack causes you to {colors.damage('bleed')}!"
      )
  ```

- In `spawn_enemy()`, add bleed detection after freeze (~line 870):
  ```python
  # Wolves, bears, lions get 20% bleed chance, 3 damage, 4 turns
  bleed_chance = 0.0
  bleed_damage = 0
  bleed_duration = 0
  if any(term in enemy_name_lower for term in ["wolf", "bear", "lion", "cat", "claw", "blade", "razor", "fang"]):
      bleed_chance = 0.2
      bleed_damage = 3
      bleed_duration = 4
  ```

- Add bleed fields to Enemy constructor call in `spawn_enemy()` (~line 890)

## Verification
Run: `pytest tests/test_status_effects.py -v`
Run: `pytest --cov=src/cli_rpg tests/test_status_effects.py`
