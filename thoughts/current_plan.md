# Plan: Remove NPCs from Unnamed Overworld Locations

## Spec

**Goal**: Unnamed locations (`is_named=False`) should not spawn NPCs. NPCs belong only inside named sub-locations (villages, dungeons) - "you don't find shopkeepers standing in random forests."

**Acceptance Criteria**:
- Unnamed locations created in `game_state.py` at line 551-558 have no NPCs
- AI-generated overworld locations with `is_named=False` skip NPC generation
- Named locations continue to generate NPCs normally
- Fallback locations (`world.py:generate_fallback_location`) with `is_named=False` have no NPCs

## Tests First

Create `tests/test_unnamed_no_npcs.py`:

```python
# Test 1: Unnamed location from template has no NPCs
def test_unnamed_location_template_no_npcs():
    """Unnamed locations from templates should have empty npcs list."""
    # Create unnamed location via game_state._generate_unnamed_location logic
    # Assert location.npcs == []

# Test 2: Named location from template can have NPCs
def test_named_location_template_allows_npcs():
    """Named locations from templates can have NPCs."""
    # Create named location via generate_fallback_location(is_named=True)
    # NPCs could be added (not blocked)

# Test 3: AI expand_world skips NPCs for unnamed locations
def test_expand_world_unnamed_skips_npcs():
    """expand_world should skip NPC generation when location is unnamed."""
    # Mock AI to return location with is_named=False
    # Assert no generate_npcs_for_location call OR npcs empty

# Test 4: AI expand_world generates NPCs for named locations
def test_expand_world_named_generates_npcs():
    """expand_world should generate NPCs when location is named."""
    # Mock AI to return location with is_named=True
    # Assert generate_npcs_for_location called AND npcs populated
```

## Implementation

### Step 1: `src/cli_rpg/ai_world.py` - `expand_world()` (lines 459-466)

Conditionally skip NPC generation for unnamed locations:

```python
# Current (line 459-466):
npcs_data = ai_service.generate_npcs_for_location(...)
location_data["npcs"] = npcs_data

# Change to:
is_named = location_data.get("is_named", True)  # Default True for backward compat
if is_named:
    npcs_data = ai_service.generate_npcs_for_location(...)
    location_data["npcs"] = npcs_data
else:
    location_data["npcs"] = []
```

### Step 2: `src/cli_rpg/ai_world.py` - `expand_area()` (lines 681-684)

Same conditional for area generation:

```python
# Current (line 681-684):
location_npcs = _create_npcs_from_data(loc_data.get("npcs", []))
for npc in location_npcs:
    new_loc.npcs.append(npc)

# Change to:
if loc_data.get("is_named", True):
    location_npcs = _create_npcs_from_data(loc_data.get("npcs", []))
    for npc in location_npcs:
        new_loc.npcs.append(npc)
```

### Step 3: `src/cli_rpg/game_state.py` - Unnamed location creation (line 551-558)

Already correct - Location constructor defaults to empty npcs list. No change needed.

### Step 4: `src/cli_rpg/world.py` - `generate_fallback_location()` (line 202-209)

Already correct - Location constructor defaults to empty npcs list. No change needed.

## Verification

```bash
# Run new tests
pytest tests/test_unnamed_no_npcs.py -v

# Run full test suite to ensure no regressions
pytest tests/ -v
```

## Files to Modify

1. `tests/test_unnamed_no_npcs.py` - **CREATE** (4 tests)
2. `src/cli_rpg/ai_world.py` - **EDIT** lines 459-466 and 681-684
