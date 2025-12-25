# Implementation Plan: Basic Poison Status Effect

## Spec

Add a **poison** status effect as the foundation for the status effect system:
- Poison deals damage-over-time (DOT) at the end of each combat turn
- Poison has a duration (turns remaining) that decrements each turn
- Enemies can apply poison to the player (20% chance on attack)
- Poison damage: 3-5 per tick, duration: 3 turns
- Status effects are displayed in combat status and tick messages are shown
- Status effects are tracked on Character model for persistence

## Implementation Steps

### 1. Create StatusEffect model (`src/cli_rpg/models/status_effect.py`)
```python
@dataclass
class StatusEffect:
    name: str           # "Poison", "Burn", etc.
    effect_type: str    # "dot" (damage over time), "buff", "debuff"
    damage_per_turn: int
    duration: int       # Turns remaining

    def tick() -> Tuple[int, bool]  # Returns (damage, expired)
    def to_dict() / from_dict()     # Serialization
```

### 2. Add status_effects list to Character model (`src/cli_rpg/models/character.py`)
- Add `status_effects: List[StatusEffect] = field(default_factory=list)`
- Add `apply_status_effect(effect: StatusEffect)` method
- Add `tick_status_effects() -> List[str]` method (returns messages)
- Add `clear_status_effects()` method (called on combat end)
- Update `to_dict()` and `from_dict()` for serialization

### 3. Add poison application to Enemy model (`src/cli_rpg/models/enemy.py`)
- Add `poison_chance: float = 0.0` field
- Add `poison_damage: int = 0` and `poison_duration: int = 0` fields
- Update `to_dict()` and `from_dict()` for serialization

### 4. Update CombatEncounter (`src/cli_rpg/combat.py`)
- In `enemy_turn()`: Check if enemy has poison_chance > 0, roll to apply poison
- After enemy attacks, call `player.tick_status_effects()` and append messages
- In `get_status()`: Display active status effects on player
- In `end_combat()`: Clear player status effects

### 5. Update enemy spawning (`src/cli_rpg/combat.py`)
- Modify `spawn_enemy()` to give some enemies poison capability
  - Spiders, snakes get 20% poison chance, 4 damage, 3 turns

## Test Plan

Create `tests/test_status_effects.py`:

1. **StatusEffect model tests**
   - `test_status_effect_tick_deals_damage_and_decrements()`
   - `test_status_effect_tick_returns_expired_when_duration_zero()`
   - `test_status_effect_serialization()`

2. **Character status effect tests**
   - `test_apply_status_effect_adds_to_list()`
   - `test_tick_status_effects_damages_character()`
   - `test_tick_status_effects_removes_expired()`
   - `test_clear_status_effects()`
   - `test_status_effects_serialization_round_trip()`

3. **Combat integration tests**
   - `test_enemy_with_poison_can_apply_poison()`
   - `test_poison_ticks_during_enemy_turn()`
   - `test_combat_status_shows_active_effects()`
   - `test_status_effects_cleared_on_combat_end()`

## Files to Modify/Create

| File | Action |
|------|--------|
| `src/cli_rpg/models/status_effect.py` | CREATE |
| `src/cli_rpg/models/character.py` | MODIFY |
| `src/cli_rpg/models/enemy.py` | MODIFY |
| `src/cli_rpg/combat.py` | MODIFY |
| `tests/test_status_effects.py` | CREATE |
