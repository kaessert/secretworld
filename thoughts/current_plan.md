# Phase 1: Procedural Interior Generation - Step 1

## Task: Create `procedural_interiors.py` with foundational data structures

This is the first step of the Procedural World Generation refactoring (CRITICAL BLOCKER). Create the foundational data structures before implementing the actual generators.

---

## Spec

Create `src/cli_rpg/procedural_interiors.py` with:

1. **RoomType Enum** - Room classifications for procedural layouts:
   - `ENTRY` - Entry/exit points
   - `CORRIDOR` - Connecting passages
   - `CHAMBER` - Standard rooms
   - `BOSS_ROOM` - Boss encounter locations
   - `TREASURE` - Treasure rooms
   - `PUZZLE` - Puzzle rooms

2. **RoomTemplate Dataclass** - Procedural room blueprint:
   - `coords: tuple[int, int, int]` - 3D position
   - `room_type: RoomType` - Classification
   - `connections: list[str]` - Connected directions
   - `is_entry: bool = False` - Entry point flag
   - `suggested_hazards: list[str] = field(default_factory=list)` - Hazard hints

3. **Generator Protocol** - Abstract interface for generators:
   - `generate(seed: int) -> list[RoomTemplate]` method

4. **Category Mapping** - Maps categories to generator types (placeholder):
   ```python
   CATEGORY_GENERATORS: dict[str, str] = {
       "dungeon": "BSPGenerator",
       "cave": "CellularAutomataGenerator",
       "town": "GridSettlementGenerator",
       "tower": "TowerGenerator",
       # ... mappings for all ENTERABLE_CATEGORIES
   }
   ```

5. **Factory Function** - Entry point for procedural generation:
   ```python
   def generate_interior_layout(category: str, bounds: tuple, seed: int) -> list[RoomTemplate]
   ```
   - Initially returns fallback layout (existing behavior)
   - Placeholder for Phase 1 Step 2 (actual generators)

---

## Tests

Create `tests/test_procedural_interiors.py`:

1. **Test RoomType enum values** - Verify all 6 types exist
2. **Test RoomTemplate creation** - Create with all fields, verify defaults
3. **Test RoomTemplate validation** - Valid/invalid room types
4. **Test CATEGORY_GENERATORS mapping** - All enterable categories mapped
5. **Test generate_interior_layout** - Returns valid RoomTemplate list
6. **Test determinism** - Same seed produces same layout

---

## Implementation Steps

1. Create `tests/test_procedural_interiors.py` with tests for:
   - RoomType enum members (ENTRY, CORRIDOR, CHAMBER, BOSS_ROOM, TREASURE, PUZZLE)
   - RoomTemplate dataclass creation and field defaults
   - CATEGORY_GENERATORS coverage of ENTERABLE_CATEGORIES
   - generate_interior_layout returns list[RoomTemplate]
   - Determinism: same seed → same output

2. Create `src/cli_rpg/procedural_interiors.py` with:
   - RoomType(Enum) with 6 values
   - RoomTemplate dataclass with coords, room_type, connections, is_entry, suggested_hazards
   - CATEGORY_GENERATORS dict mapping all ENTERABLE_CATEGORIES
   - generate_interior_layout() stub returning fallback layout

3. Run tests: `pytest tests/test_procedural_interiors.py -v`

---

## Files

| File | Action |
|------|--------|
| `tests/test_procedural_interiors.py` | CREATE |
| `src/cli_rpg/procedural_interiors.py` | CREATE |

---

## Notes

- This is a **foundational step** - no modification to existing code yet
- Generators (BSP, cellular automata) come in Step 2
- Integration with `ai_world.py` comes in Step 5 (Phase 1 Integration)
- Seed derivation: `hash((location.name, location.coordinates, "interior"))`
