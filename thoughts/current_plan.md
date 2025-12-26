# Implementation Plan: Faction Reputation System MVP

## Spec

Add a basic faction reputation system that tracks player standing with different factions. This MVP provides the infrastructure for future faction-based content gating.

**Components:**
1. `Faction` model: name, description, reputation (1-100 scale)
2. `ReputationLevel` enum: HOSTILE (1-19), UNFRIENDLY (20-39), NEUTRAL (40-59), FRIENDLY (60-79), HONORED (80-100)
3. `factions` field on GameState to track player faction standings
4. `reputation` command to view faction standings
5. Default factions in starting world

**Reputation levels:**
- HOSTILE (1-19): Faction members attack on sight
- UNFRIENDLY (20-39): Won't trade or offer quests
- NEUTRAL (40-59): Basic interactions available
- FRIENDLY (60-79): Discounts, additional quests
- HONORED (80-100): Best prices, exclusive content

## Tests First (TDD)

### `tests/test_faction.py`
1. `TestFaction`:
   - `test_faction_creation`: Create faction with name, description, reputation=50
   - `test_faction_reputation_clamped`: Reputation clamped to 1-100
   - `test_get_reputation_level`: Returns correct ReputationLevel for each threshold
   - `test_add_reputation`: Adds rep, returns level-up message if threshold crossed
   - `test_reduce_reputation`: Reduces rep, returns level-down message if threshold crossed
   - `test_reputation_display`: Visual bar like companion bond display
   - `test_faction_serialization`: `to_dict()` and `from_dict()` work correctly

2. `TestGameStateFactions`:
   - `test_factions_field_default_empty`: New GameState has empty factions list
   - `test_factions_persistence`: Factions saved/loaded correctly
   - `test_factions_backward_compat`: Old saves without factions load with empty list

3. `TestReputationCommand`:
   - `test_reputation_command_no_factions`: Shows "No factions discovered yet"
   - `test_reputation_command_shows_standings`: Lists all factions with bars

## Implementation Steps

### Step 1: Create faction model
**File:** `src/cli_rpg/models/faction.py`
- `ReputationLevel` enum with 5 levels
- `Faction` dataclass with:
  - `name: str`
  - `description: str`
  - `reputation: int = 50` (starts neutral)
  - `get_reputation_level() -> ReputationLevel`
  - `add_reputation(amount: int) -> Optional[str]`
  - `reduce_reputation(amount: int) -> Optional[str]`
  - `get_reputation_display() -> str` (visual bar)
  - `to_dict() -> dict`
  - `from_dict(data: dict) -> Faction`

### Step 2: Update models/__init__.py
**File:** `src/cli_rpg/models/__init__.py`
- Export `Faction` and `ReputationLevel`

### Step 3: Add factions to GameState
**File:** `src/cli_rpg/game_state.py`
- Add `factions: list[Faction] = []` field in `__init__`
- Add `"reputation"` to `KNOWN_COMMANDS` set
- Add to `to_dict()`: serialize factions list
- Add to `from_dict()`: deserialize factions (default empty for backward compat)

### Step 4: Add reputation command to main.py
**File:** `src/cli_rpg/main.py`
- Add `reputation` and alias `rep` to command aliases in `parse_command()`
- Add command handler that displays faction standings
- Add to `get_command_reference()` help text

### Step 5: Add default factions to world.py
**File:** `src/cli_rpg/world.py`
- Create helper `get_default_factions()` returning list of starter factions:
  - Town Guard (description: "The local militia protecting settlements")
  - Merchant Guild (description: "Traders and shopkeepers")
  - Thieves Guild (description: "A shadowy network of rogues")

### Step 6: Initialize factions in game setup
**File:** `src/cli_rpg/main.py`
- In `run_game()` after creating GameState, call `get_default_factions()` and assign to `game_state.factions`

### Step 7: Run tests and verify
```bash
pytest tests/test_faction.py -v
pytest --cov=src/cli_rpg --cov-report=term-missing
```
