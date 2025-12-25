# Implementation Plan: Bond System - Companions Foundation (MVP)

## Scope
Implement the foundational companion system: `Companion` model with bond levels, `companions` command to view party, and `recruit` command stub for recruitable NPCs.

---

## 1. Spec: Companion Model

### Bond Levels (Enum)
- `STRANGER` (0-24) - Just met, no trust
- `ACQUAINTANCE` (25-49) - Some familiarity
- `TRUSTED` (50-74) - Genuine trust
- `DEVOTED` (75-100) - Unbreakable bond

### Companion Dataclass Fields
- `name: str` - Companion's name
- `description: str` - Brief description
- `bond_points: int` (0-100, default 0)
- `bond_level: BondLevel` (computed from bond_points)
- `recruited_at: str` - Location name where recruited

### Methods
- `get_bond_level() -> BondLevel` - Compute level from points
- `add_bond(amount: int) -> Optional[str]` - Add points, return message if level changes
- `get_bond_display() -> str` - Formatted bond bar with level name
- `to_dict() / from_dict()` - Serialization

---

## 2. Tests to Write First

### File: `tests/test_companion.py`

```python
# Test companion creation
test_create_companion_basic
test_companion_default_bond_is_stranger

# Test bond progression
test_bond_level_thresholds  # 0-24=stranger, 25-49=acquaintance, 50-74=trusted, 75-100=devoted
test_add_bond_increases_points
test_add_bond_returns_message_on_level_up
test_add_bond_caps_at_100

# Test display
test_get_bond_display_format

# Test serialization
test_companion_to_dict
test_companion_from_dict
test_companion_roundtrip_serialization
```

### File: `tests/test_companion_commands.py`

```python
# Test companions command
test_companions_command_no_companions
test_companions_command_with_one_companion
test_companions_command_with_multiple_companions

# Test recruit command (stub)
test_recruit_no_npc_specified
test_recruit_npc_not_found
test_recruit_npc_not_recruitable
test_recruit_success_adds_companion
test_recruit_already_in_party
```

### File: `tests/test_companion_persistence.py`

```python
# Test GameState serialization with companions
test_gamestate_companions_serialization
test_gamestate_companions_deserialization
test_gamestate_companions_backward_compatibility  # Empty list for old saves
```

---

## 3. Implementation Steps

### Step 1: Create Companion Model
**File:** `src/cli_rpg/models/companion.py`
- Create `BondLevel` enum with 4 levels
- Create `Companion` dataclass with fields above
- Implement `get_bond_level()` with threshold logic
- Implement `add_bond()` returning optional level-up message
- Implement `get_bond_display()` with visual bar (like dread meter)
- Implement `to_dict()` / `from_dict()`

### Step 2: Add NPC Recruitable Flag
**File:** `src/cli_rpg/models/npc.py`
- Add `is_recruitable: bool = False` field
- Update `to_dict()` to include new field
- Update `from_dict()` with backward compatibility (default False)

### Step 3: Add Companions to GameState
**File:** `src/cli_rpg/game_state.py`
- Add `companions: List[Companion] = []` attribute in `__init__`
- Update `to_dict()` to serialize companions
- Update `from_dict()` to deserialize with backward compatibility

### Step 4: Add Commands
**File:** `src/cli_rpg/main.py`
- Add "companions" and "recruit" to `KNOWN_COMMANDS` set
- Implement `companions` command in `handle_exploration_command`:
  - Show "No companions in your party." if empty
  - Otherwise list each companion with bond display
- Implement `recruit` command stub in `handle_exploration_command`:
  - Find NPC by name in current location
  - Check `is_recruitable` flag
  - Create Companion from NPC data
  - Add to `game_state.companions`
  - Return success message

### Step 5: Update Help
**File:** `src/cli_rpg/main.py`
- Add to `get_command_reference()`:
  - `companions     - View your party members and bond levels`
  - `recruit <npc>  - Recruit an NPC to join your party`

### Step 6: Export from Models Package
**File:** `src/cli_rpg/models/__init__.py`
- Add `Companion, BondLevel` to imports and `__all__`

---

## 4. File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/models/companion.py` | NEW - Companion model + BondLevel enum |
| `src/cli_rpg/models/npc.py` | Add `is_recruitable` field |
| `src/cli_rpg/models/__init__.py` | Export Companion, BondLevel |
| `src/cli_rpg/game_state.py` | Add `companions` list + serialization |
| `src/cli_rpg/main.py` | Add commands, help text, KNOWN_COMMANDS |
| `tests/test_companion.py` | NEW - Companion model tests |
| `tests/test_companion_commands.py` | NEW - Command tests |
| `tests/test_companion_persistence.py` | NEW - Serialization tests |

---

## 5. Acceptance Criteria

1. **Companion model works**: Can create, check bond level, add bond points
2. **Bond levels are correct**: 0-24 Stranger, 25-49 Acquaintance, 50-74 Trusted, 75-100 Devoted
3. **`companions` command**: Shows party list or "no companions" message
4. **`recruit` command**: Can recruit NPCs marked as recruitable
5. **Persistence**: Companions saved/loaded with game state
6. **Backward compatible**: Old saves load without companions (empty list)
7. **All tests pass**: Including existing 2129 tests
