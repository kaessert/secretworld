# Implementation Plan: Faction-Based Content Unlocks

## Feature Summary
Add faction reputation gating for NPCs, locations, and shops - content becomes accessible only when players reach certain reputation levels with the affiliated faction.

## Existing Infrastructure (No Changes Needed)
- `Faction` model with reputation 1-100 and `ReputationLevel` enum (HOSTILE/UNFRIENDLY/NEUTRAL/FRIENDLY/HONORED)
- `NPC.faction` field exists but is unused for gating
- `_find_faction_by_name()` helper in `faction_combat.py`
- Quest `required_reputation` pattern already working in `main.py`

## Spec

### 1. NPC Gating
- Add `required_reputation: Optional[int]` field to NPC model
- NPCs with faction + required_reputation are hidden from location.npcs display if player doesn't meet requirement
- Talking to gated NPCs shows: "{NPC.name} refuses to speak with you. Your reputation with {faction} is too low."
- Visible NPCs still shown, just can't interact until reputation reached

### 2. Location Gating
- Add `required_faction: Optional[str]` and `required_reputation: Optional[int]` fields to Location model
- `enter` command checks faction reputation before allowing entry
- Blocked message: "The entrance to {location} is guarded. You need higher standing with {faction} to enter."
- Only applies to SubGrid entries (interior locations), not overworld movement

### 3. NPC Faction Dialogue Modifiers
- NPCs with faction affiliations give reputation-appropriate greetings
- HOSTILE: refuse dialogue entirely
- UNFRIENDLY: curt, unwelcoming
- FRIENDLY/HONORED: warm, offer hints about exclusive content

## Implementation Steps

### Step 1: Update NPC Model (`models/npc.py`)
```python
# Add field
required_reputation: Optional[int] = None
```
- Add to `__init__`, `to_dict()`, `from_dict()` with backward compatibility

### Step 2: Update Location Model (`models/location.py`)
```python
# Add fields
required_faction: Optional[str] = None
required_reputation: Optional[int] = None
```
- Add to dataclass, `to_dict()`, `from_dict()` with backward compatibility

### Step 3: Create Faction Content Module (`faction_content.py`)
```python
def check_npc_access(npc: NPC, factions: list[Faction]) -> tuple[bool, str]:
    """Check if player can interact with NPC based on faction reputation."""

def check_location_access(location: Location, factions: list[Faction]) -> tuple[bool, str]:
    """Check if player can enter location based on faction reputation."""

def filter_visible_npcs(npcs: list[NPC], factions: list[Faction]) -> list[NPC]:
    """Filter NPCs to only show those meeting reputation requirements."""

def get_faction_greeting_modifier(npc: NPC, factions: list[Faction]) -> Optional[str]:
    """Get modified greeting based on player's faction standing."""
```

### Step 4: Integrate NPC Gating in `main.py`
- In `talk` command: check `check_npc_access()` before allowing interaction
- Block hostile faction members from dialogue
- Show reputation-aware rejection messages

### Step 5: Integrate Location Gating in `game_state.py`
- In `enter()` method: check `check_location_access()` before entry
- Return blocking message if reputation insufficient

### Step 6: Update Location Display
- In `Location.get_layered_description()`: filter NPCs via `filter_visible_npcs()`
- Pass factions through from caller (or mark as "(requires reputation)")

## Test Plan

### Unit Tests (`tests/test_faction_content.py`)
1. `test_npc_required_reputation_field_defaults_to_none()`
2. `test_npc_required_reputation_serialization()`
3. `test_check_npc_access_no_requirement_always_allowed()`
4. `test_check_npc_access_blocked_when_reputation_too_low()`
5. `test_check_npc_access_allowed_when_reputation_sufficient()`
6. `test_check_npc_access_hostile_faction_blocks_entirely()`
7. `test_location_required_faction_field_defaults_to_none()`
8. `test_location_required_reputation_serialization()`
9. `test_check_location_access_no_requirement_always_allowed()`
10. `test_check_location_access_blocked_when_reputation_too_low()`
11. `test_check_location_access_allowed_when_reputation_sufficient()`
12. `test_filter_visible_npcs_removes_gated_npcs()`
13. `test_filter_visible_npcs_keeps_ungated_npcs()`
14. `test_get_faction_greeting_modifier_hostile_returns_rejection()`
15. `test_get_faction_greeting_modifier_friendly_returns_warm()`

### Integration Tests (`tests/test_faction_content_integration.py`)
1. `test_talk_command_blocked_by_npc_faction_requirement()`
2. `test_talk_command_allowed_when_reputation_met()`
3. `test_enter_command_blocked_by_location_faction_requirement()`
4. `test_enter_command_allowed_when_reputation_met()`
5. `test_location_display_hides_gated_npcs()`

## Files to Modify
1. `src/cli_rpg/models/npc.py` - Add `required_reputation` field
2. `src/cli_rpg/models/location.py` - Add `required_faction`, `required_reputation` fields
3. `src/cli_rpg/faction_content.py` - NEW FILE: gating logic
4. `src/cli_rpg/main.py` - Integrate NPC gating in talk command
5. `src/cli_rpg/game_state.py` - Integrate location gating in enter command
6. `tests/test_faction_content.py` - NEW FILE: unit tests
7. `tests/test_faction_content_integration.py` - NEW FILE: integration tests
