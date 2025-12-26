# Camping Feature Implementation Summary

## What Was Implemented

### New Module: `src/cli_rpg/camping.py`
Created a comprehensive wilderness survival module with the following features:

#### Camp Command
- **Mechanics**: Heals 50% of max HP, reduces dread by 30 (40 with campfire), advances time 8 hours
- **Requirements**: Requires Camping Supplies item (consumed on use)
- **Location restrictions**: Only works in campable categories (forest, wilderness, cave, ruins)
- **Safe zone blocking**: Redirects to "rest" command in safe zones
- **Combat blocking**: Cannot camp during combat
- **Campfire features**:
  - Active light source = campfire
  - Extra -10 dread reduction
  - Cooks Raw Meat → Cooked Meat (40 HP heal vs 30 HP raw)
  - 20% chance of friendly visitor spawn
- **Dream integration**: 40% chance of dream during camp (uses existing dream system)

#### Forage Command
- **Mechanics**: Search for herbs/berries based on Perception stat
- **Success rate**: 40% base + 2% per PER (capped at 95%)
- **Items**: Herbs (10 HP), Wild Berries (15 HP), Medicinal Root (20 HP), Moonpetal Flower (20 mana, night only)
- **Cooldown**: 1 hour after use
- **Location restrictions**: Forest and wilderness only

#### Hunt Command
- **Mechanics**: Hunt game based on Dexterity and Perception
- **Success rate**: 30% base + 2% per DEX + 1% per PER (capped at 95%)
- **Results**: Raw Meat (30 HP) on success, Animal Pelt (25 gold sell value) on critical
- **Cooldown**: 2 hours after use
- **Location restrictions**: Forest and wilderness only

### GameState Modifications (`src/cli_rpg/game_state.py`)
- Added `forage_cooldown` and `hunt_cooldown` fields
- Added to serialization/deserialization for save/load persistence
- Added "camp", "forage", "hunt" to KNOWN_COMMANDS
- Added aliases: "ca" → camp, "fg" → forage, "hu" → hunt

### Command Integration (`src/cli_rpg/main.py`)
- Added command handlers for camp, forage, hunt in handle_exploration_command
- Added commands to help text with aliases

### Shop Integration (`src/cli_rpg/world.py`)
- Added Camping Supplies to Market District merchant (40 gold)
- Added Camping Supplies to Millbrook Village Innkeeper (30 gold - rural discount)
- Created Innkeeper shop with supplies for travelers

## Test Results
- **44 new tests** in `tests/test_camping.py`
- All tests pass
- Full test suite (2837 tests) passes

## Key Design Decisions

1. **Campable locations** are defined by category, not by name, allowing easy extension
2. **Cooldowns** are stored in GameState and serialized for persistence
3. **Campfire detection** uses existing `has_active_light()` method (torch, lantern, etc.)
4. **Dream integration** reuses the existing `maybe_trigger_dream()` system
5. **Meat cooking** is automatic when camping with campfire - no separate command needed

## Files Modified

1. **New files**:
   - `src/cli_rpg/camping.py` - Core camping module (360 lines)
   - `tests/test_camping.py` - Test suite (440 lines)

2. **Modified files**:
   - `src/cli_rpg/game_state.py` - Added cooldown fields and aliases
   - `src/cli_rpg/main.py` - Added command handlers and help text
   - `src/cli_rpg/world.py` - Added Camping Supplies to shops

## E2E Test Validation Scenarios

1. **Buy supplies in town** → Travel to forest → Camp → Verify healing and dread reduction
2. **Forage in wilderness** → Get item → Try again (should be on cooldown)
3. **Hunt in forest** → Get meat → Camp with torch → Verify meat is cooked
4. **Try camping in town** → Should redirect to rest command
5. **Save game with cooldowns** → Load game → Verify cooldowns persist
