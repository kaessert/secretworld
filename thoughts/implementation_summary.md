# Implementation Summary: Basic Poison Status Effect

## What Was Implemented

### 1. New StatusEffect Model (`src/cli_rpg/models/status_effect.py`)
- Created `StatusEffect` dataclass with fields:
  - `name`: Display name (e.g., "Poison")
  - `effect_type`: Type of effect ("dot", "buff", "debuff")
  - `damage_per_turn`: Damage dealt each tick for DOT effects
  - `duration`: Turns remaining
- Implemented `tick()` method that decrements duration and returns (damage, expired)
- Implemented `to_dict()`/`from_dict()` for serialization/persistence

### 2. Character Model Updates (`src/cli_rpg/models/character.py`)
- Added `status_effects: List[StatusEffect]` field to track active effects
- Implemented `apply_status_effect(effect)` method to add effects
- Implemented `tick_status_effects()` method that:
  - Processes each effect's tick
  - Applies damage from DOT effects
  - Removes expired effects
  - Returns messages describing what happened
- Implemented `clear_status_effects()` method (for combat end)
- Updated `to_dict()`/`from_dict()` for persistence with backward compatibility

### 3. Enemy Model Updates (`src/cli_rpg/models/enemy.py`)
- Added poison capability fields:
  - `poison_chance: float = 0.0` (0.0-1.0 chance to poison on attack)
  - `poison_damage: int = 0` (damage per turn)
  - `poison_duration: int = 0` (turns of poison)
- Updated `to_dict()`/`from_dict()` for serialization with backward compatibility

### 4. Combat System Updates (`src/cli_rpg/combat.py`)
- Updated `enemy_turn()` to:
  - Roll for poison application when enemy has `poison_chance > 0`
  - Apply poison status effect to player on successful roll
  - Tick player's status effects after all enemy attacks
  - Include status effect messages in combat output
- Updated `get_status()` to display active status effects with remaining duration
- Updated `end_combat()` to clear all player status effects

### 5. Enemy Spawning Updates (`src/cli_rpg/combat.py`)
- Modified `spawn_enemy()` to give poison capability to certain enemies:
  - Spider, Snake, Serpent, Viper: 20% poison chance, 4 damage, 3 turns duration

### 6. Tests (`tests/test_status_effects.py`)
Created comprehensive test suite with 17 tests covering:
- StatusEffect model creation and tick behavior
- StatusEffect serialization round-trip
- Character status effect application and tick processing
- Character status effect serialization
- Enemy poison fields and serialization
- Combat integration (poison application, ticking, status display, cleanup)
- Enemy spawning with poison capability

## Test Results

All 1727 tests pass, including:
- 17 new status effect tests
- All existing tests (1 existing test updated to expect new poison fields in Enemy serialization)

## Files Modified/Created

| File | Action | Description |
|------|--------|-------------|
| `src/cli_rpg/models/status_effect.py` | CREATE | New StatusEffect dataclass |
| `src/cli_rpg/models/character.py` | MODIFY | Added status_effects field and methods |
| `src/cli_rpg/models/enemy.py` | MODIFY | Added poison capability fields |
| `src/cli_rpg/combat.py` | MODIFY | Poison application, ticking, and display |
| `tests/test_status_effects.py` | CREATE | New test file with 17 tests |
| `tests/test_enemy.py` | MODIFY | Updated serialization test for new fields |

## Design Decisions

1. **Status effects on Character, not CombatEncounter**: Effects are tracked on the Character model to support persistence across save/load cycles, even though they're currently only active during combat.

2. **Poison application after attack**: Poison is applied after each enemy attack, with a probability roll per attack. This means multiple poison stacks can be applied from a single multi-enemy turn.

3. **Status effect tick timing**: Effects tick at the end of the enemy turn, after all enemy attacks have been processed. This gives the player one turn to react before taking DOT damage.

4. **Backward compatibility**: All serialization changes use `.get()` with default values for backward compatibility with existing save files.

## E2E Validation Points

1. Start a game and navigate to a forest to encounter a Giant Spider
2. Let the spider attack - there's a 20% chance it will poison you
3. When poisoned, the combat status should show "Status: Poison (3 turns)"
4. Each subsequent enemy turn, the poison should tick for 4 damage
5. After 3 turns, the "Poison has worn off" message should appear
6. After combat ends (victory or defeat), status effects should be cleared
