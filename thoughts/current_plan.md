# Plan: World Event Resolution System

## Overview
Add player actions to resolve world events before they expire, giving players agency over living world events.

## Specification

### Event Resolution Mechanics

| Event Type | Resolution Action | Location Requirement | Reward |
|------------|-------------------|---------------------|--------|
| **Plague** | Use cure item while at affected location | Must be at affected location | XP, gold, reputation |
| **Invasion** | Defeat combat at affected location | Must be at affected location | XP, gold, loot |
| **Caravan** | Trade with caravan (buy/sell) | Must be at affected location | Trade opportunity only |

### New Command: `resolve <event>`
- Attempts to resolve an active event
- Requires player to be at an affected location
- Each event type has specific resolution requirements

### Resolution Requirements by Type

**Plague Events**:
- Player must have a "Cure" or "Antidote" item in inventory
- Item is consumed on use
- Success message + rewards

**Invasion Events**:
- Triggers combat encounter with event-specific enemies
- Victory resolves the event
- Defeat = flee, event remains active

**Caravan Events**:
- Already resolvable by trading (existing shop system)
- Add auto-resolution when player makes a purchase

---

## Implementation Steps

### 1. Add "Cure" item type and drop from combat/shops
**File:** `src/cli_rpg/models/item.py`
- Add `CURE_EFFECT` tag or new ItemType for cure items

**File:** `src/cli_rpg/combat.py`
- Add cure items to loot tables (rare drop)

### 2. Create resolution functions
**File:** `src/cli_rpg/world_events.py`
- `can_resolve_event(game_state, event) -> tuple[bool, str]`: Check if resolution is possible
- `get_resolution_requirements(event) -> str`: Display what's needed to resolve
- Update existing `resolve_event()` to handle type-specific resolution

### 3. Add "resolve" command
**File:** `src/cli_rpg/game_state.py`
- Add "resolve" to `KNOWN_COMMANDS`

**File:** `src/cli_rpg/main.py`
- Add `handle_exploration_command` case for "resolve"
- Parse event name/ID argument
- Check requirements, execute resolution

### 4. Auto-resolve caravan on trade
**File:** `src/cli_rpg/main.py`
- In "buy" command handler, check if caravan event at location
- Mark as resolved after successful purchase

### 5. Add tab completion for resolve command
**File:** `src/cli_rpg/completer.py`
- Add `_complete_resolve()` method returning active event names

### 6. Update events display to show resolution hints
**File:** `src/cli_rpg/world_events.py`
- Enhance `get_active_events_display()` to show resolution requirements

---

## Test Plan

**File:** `tests/test_world_events.py`

### Tests for resolution mechanics:
1. `test_resolve_plague_with_cure_item` - Cure item consumed, event resolved
2. `test_resolve_plague_without_cure_fails` - Error message, event unchanged
3. `test_resolve_event_wrong_location_fails` - Must be at affected location
4. `test_resolve_invasion_triggers_combat` - Combat encounter spawns
5. `test_caravan_auto_resolves_on_purchase` - Buy item → event resolved
6. `test_resolve_command_unknown_event` - Error handling for invalid event
7. `test_resolve_gives_rewards` - XP and gold awarded

### Tests for cure items:
1. `test_cure_item_drops_from_combat` - Rare loot table entry
2. `test_cure_item_in_shop` - Available at healer NPCs

---

## Files Modified
1. `src/cli_rpg/models/item.py` - Add cure item support
2. `src/cli_rpg/world_events.py` - Resolution logic
3. `src/cli_rpg/game_state.py` - Add "resolve" command
4. `src/cli_rpg/main.py` - Handle resolve command, auto-resolve caravan
5. `src/cli_rpg/completer.py` - Tab completion for resolve
6. `src/cli_rpg/combat.py` - Cure item drops
7. `tests/test_world_events.py` - Resolution tests
