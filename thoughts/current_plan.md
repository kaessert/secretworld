# Implementation Plan: TowerGenerator for Procedural Interiors

## Task Summary
Implement `TowerGenerator` class in `procedural_interiors.py` for generating vertical tower layouts extending upward (z > 0), completing Phase 2 item 7 of the Procedural World Generation roadmap.

## Spec

**TowerGenerator** generates vertical layouts for tower-type locations:
- Extends **upward** (z > 0), opposite of dungeon behavior
- Entry at ground level (z=0), boss/treasure at top (z=max)
- Each floor is a single room connected by stairs (up/down)
- Floors use minimal horizontal footprint (tower bounds: 3x3 per floor)
- Room types: ENTRY at z=0, CHAMBER for middle floors, BOSS_ROOM at top
- 30% chance for treasure room on non-boss dead-end floors

## Implementation Steps

### 1. Add TowerGenerator class to `src/cli_rpg/procedural_interiors.py`

Location: After `GridSettlementGenerator` class (~line 990), before `CATEGORY_GENERATORS`

```python
class TowerGenerator:
    """Vertical generator for tower layouts extending upward (z > 0).

    Creates multi-floor towers where each floor is a small room (1-3 tiles)
    connected by stairs. Entry at ground level, boss at top.
    """

    def __init__(self, bounds: tuple[int, int, int, int, int, int], seed: int):
        self.bounds = bounds
        self.seed = seed
        self.rng = random.Random(seed)
        self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z = bounds

    def generate(self) -> list[RoomTemplate]:
        # Generate one room per z-level from 0 to max_z
        # Entry at z=0, boss at z=max_z
        # Optional side rooms on floors (30% chance)
```

### 2. Update `generate_interior_layout()` function

Add handling for `TowerGenerator` in the dispatch logic (~line 1050):

```python
if generator_type == "TowerGenerator":
    generator = TowerGenerator(bounds=bounds, seed=seed)
    return generator.generate()
```

### 3. Add tests to `tests/test_procedural_interiors.py`

Add new `TestTowerGenerator` class after `TestGridSettlementGenerator`:

**Tests to implement:**
1. `test_generator_exists` - TowerGenerator is importable
2. `test_implements_protocol` - follows GeneratorProtocol
3. `test_returns_room_templates` - generate() returns list[RoomTemplate]
4. `test_has_entry_room` - layout includes entry room with is_entry=True
5. `test_entry_at_ground_level` - entry room at z=0
6. `test_boss_at_top_level` - BOSS_ROOM at z=max_z
7. `test_extends_upward` - rooms span z=0 to z=max_z (positive z)
8. `test_has_vertical_connections` - floors connected with up/down
9. `test_deterministic_with_same_seed` - same seed produces identical layout
10. `test_different_seed_different_layout` - different seeds differ
11. `test_small_bounds_works` - handles minimal 3x3x4 bounds

## Files Modified

1. `src/cli_rpg/procedural_interiors.py` - Add TowerGenerator class + dispatch
2. `tests/test_procedural_interiors.py` - Add TestTowerGenerator test class

## Verification

```bash
# Run tests
pytest tests/test_procedural_interiors.py -v

# Run full test suite
pytest --cov=src/cli_rpg
```
