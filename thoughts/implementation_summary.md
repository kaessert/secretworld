# Implementation Summary: Bleed Status Effect

## What Was Implemented

Added "Bleed" damage-over-time (DOT) effect following the established poison/burn pattern:
- **Effect type**: DOT (uses existing StatusEffect infrastructure)
- **Bleed chance**: 20% on attack
- **Bleed damage**: 3 per turn
- **Bleed duration**: 4 turns
- **Thematic enemies**: Wolf, bear, lion, cat, claw, blade, razor, fang

## Files Modified

### 1. `src/cli_rpg/models/enemy.py`
- Added three new dataclass fields:
  - `bleed_chance: float = 0.0`
  - `bleed_damage: int = 0`
  - `bleed_duration: int = 0`
- Added bleed fields to `to_dict()` serialization
- Added bleed fields to `from_dict()` deserialization

### 2. `src/cli_rpg/combat.py`
- Added bleed application logic in `enemy_turn()` method (after freeze check, ~line 551-563)
- Added bleed detection in `spawn_enemy()` function (~line 885-892)
- Added bleed fields to Enemy constructor call in `spawn_enemy()` (~line 913-915)

### 3. `tests/test_status_effects.py`
- Added `TestBleedStatusEffect` class with 3 tests:
  - `test_bleed_effect_creation` - Verifies Bleed DOT effect with expected values
  - `test_bleed_effect_tick_deals_damage` - Verifies 3 damage per turn
  - `test_bleed_effect_expires_correctly` - Verifies 4 turn duration

- Added `TestEnemyBleed` class with 3 tests:
  - `test_enemy_with_bleed_fields` - Verifies enemy can have bleed_chance, bleed_damage, bleed_duration
  - `test_enemy_default_no_bleed` - Non-bleed enemies have 0 defaults
  - `test_enemy_bleed_serialization` - Verifies to_dict/from_dict round-trip

- Added `TestCombatBleed` class with 2 tests:
  - `test_bleed_applies_in_combat` - Enemy with 100% bleed_chance applies Bleed
  - `test_bleed_ticks_during_enemy_turn` - Bleed deals damage each turn

### 4. `tests/test_enemy.py`
- Updated `test_to_dict_serializes_enemy` to include bleed fields in expected dict

## Test Results

All 1790 tests pass, including 8 new bleed-specific tests.

## Design Decisions

1. **Followed existing patterns**: Bleed implementation mirrors the poison/burn pattern exactly, ensuring consistency.
2. **Thematic enemy selection**: Chose slashing/claw-based enemies (wolf, bear, lion, etc.) for bleed since they have natural claws/fangs that would cause bleeding wounds.
3. **Balanced stats**:
   - Lower damage (3) than burn (5) but higher than base
   - Longer duration (4 turns) than burn (2) and poison (3)
   - Same 20% chance as other DOT effects

## E2E Validation

To validate manually:
1. Start a game and encounter a Wolf or Bear enemy
2. Get attacked - there's a 20% chance to apply Bleed
3. When Bleed is applied, you should see "causes you to bleed!" message
4. Each turn, Bleed should deal 3 damage with "Bleed" in the status messages
5. After 4 turns, Bleed expires with "worn off" message
