# Plan: Add "Freeze" Status Effect to Combat System

## Spec
**Freeze**: A control effect that slows enemies, reducing their attack power.
- Effect type: `"freeze"` (new type, like "stun" is for player)
- Applies to enemies (inverse of stun which affects the player)
- Enemies with freeze get 20% chance to apply it on attack
- Duration: 2 turns
- Behavior: Frozen enemies have 50% reduced attack power

## Tests to Add (`tests/test_status_effects.py`)

### 1. Freeze StatusEffect Model Tests
```python
class TestFreezeStatusEffect:
    def test_freeze_effect_creation()  # effect_type="freeze", damage_per_turn=0
    def test_freeze_effect_tick_no_damage()  # Returns 0 damage, decrements duration
```

### 2. Enemy Freeze Fields Tests
```python
class TestEnemyFreeze:
    def test_enemy_freeze_fields()  # freeze_chance, freeze_duration on Enemy
    def test_enemy_default_no_freeze()  # Defaults to 0
    def test_enemy_freeze_serialization()  # to_dict/from_dict
```

### 3. Combat Freeze Behavior Tests
```python
class TestCombatFreeze:
    def test_frozen_enemy_reduced_damage()  # 50% attack reduction
    def test_frozen_enemy_status_display()  # Shows in combat status
    def test_freeze_expires_correctly()  # Effect removed after duration
```

## Implementation Steps

### Step 1: Add Enemy Status Effect Support (`src/cli_rpg/models/enemy.py`)
Currently status effects only exist on Character. Add to Enemy:
- `status_effects: list = field(default_factory=list)`
- `apply_status_effect(effect)` method
- `tick_status_effects()` method
- `clear_status_effects()` method
- `has_effect_type(effect_type: str) -> bool` helper
- Update `to_dict()`/`from_dict()` for persistence

### Step 2: Add Freeze Fields to Enemy (`src/cli_rpg/models/enemy.py`)
Following burn/stun pattern:
- `freeze_chance: float = 0.0`
- `freeze_duration: int = 0`
- Update serialization methods

### Step 3: Update Combat (`src/cli_rpg/combat.py`)
1. In `enemy_turn()`: Check for freeze effect on enemy, apply 50% damage reduction
2. In `enemy_turn()`: Tick enemy status effects after their attack
3. Add freeze application from ice-themed enemies in enemy attack logic
4. In `spawn_enemy()`: Add freeze to ice enemies (Yeti gets 20% chance, 2 turns)
5. In `end_combat()`: Clear enemy status effects
6. In `get_status()`: Display frozen status on enemies

## File Changes
1. `src/cli_rpg/models/enemy.py` - Add status_effects list + freeze fields + methods
2. `src/cli_rpg/combat.py` - Handle freeze damage reduction, add to spawn templates
3. `tests/test_status_effects.py` - Add TestFreezeStatusEffect, TestEnemyFreeze, TestCombatFreeze classes
