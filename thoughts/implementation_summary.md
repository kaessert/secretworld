# Implementation Summary: Light Sources to Reduce Dread Buildup

## What Was Implemented

Light sources are now consumable items that reduce dread buildup when entering dark areas. When a light source is active:
- Dread increases from location category are reduced by 50%
- Night dread bonus is negated
- Light sources last for a limited number of moves (e.g., 5 moves for a Torch)
- Multiple light sources stack by extending duration (not multiplying effect)

## Files Modified

### 1. `src/cli_rpg/models/item.py`
- Added `light_duration: int = 0` field to the Item dataclass
- Added validation in `__post_init__`: `light_duration` cannot be negative
- Updated `to_dict()` to include `light_duration`
- Updated `from_dict()` to deserialize `light_duration` (with backward compatibility default of 0)
- Updated `__str__()` to display "X moves of light" for light source items

### 2. `src/cli_rpg/models/character.py`
- Added `light_remaining: int = 0` field to Character dataclass
- Added `use_light_source(duration: int)` method: Activates or extends light duration
- Added `tick_light() -> Optional[str]` method: Decrements light, returns message when it expires
- Added `has_active_light() -> bool` method: Checks if character has active light
- Updated `use_item()` to handle light source items (activates light, removes item from inventory)
- Updated `to_dict()` to include `light_remaining`
- Updated `from_dict()` to restore `light_remaining` (with backward compatibility default of 0)

### 3. `src/cli_rpg/game_state.py`
- Modified `_update_dread_on_move()` to:
  - Check for active light with `has_light = self.current_character.has_active_light()`
  - Halve category dread when light is active: `dread_increase = dread_increase // 2`
  - Skip night bonus when light is active
  - Tick light on every move (including towns)
  - Combine dread messages with light expiration messages

### 4. `src/cli_rpg/world.py`
- Added Torch item to the default merchant shop:
  - Name: "Torch"
  - Description: "A wooden torch that provides light in dark places"
  - Type: CONSUMABLE
  - Light duration: 5 moves
  - Price: 15 gold

## Test Files Created/Modified

### 1. `tests/test_light_source.py` (New - 19 tests)
- `TestItemLightDuration`: 5 tests for Item light_duration field
- `TestCharacterLightRemaining`: 9 tests for Character light tracking
- `TestUseLightSourceItem`: 5 tests for using light source items

### 2. `tests/test_dread_integration.py` (Modified - 7 new tests)
- `TestLightSourceDreadReduction`: 7 tests for light + dread integration
  - Light halves category dread
  - Light negates night bonus
  - Light ticks down on move
  - Light expires after duration
  - Light expiration message appears
  - Dread returns to normal after light expires
  - Light does not affect town dread reduction

## Test Results

All 2129 tests pass, including:
- 26 new tests specifically for light sources
- All existing tests continue to pass (backward compatibility verified)

## Design Decisions

1. **Light ticks in towns too**: Even though towns reduce dread, light still ticks down when moving through towns (represents passage of time)

2. **Light only affects category dread and night bonus**: Weather and low-health dread modifiers are not reduced by light (these represent different dangers)

3. **Stacking extends duration**: Using multiple torches adds to the remaining duration rather than creating separate timers

4. **Integer division for halving**: `dread_increase // 2` ensures predictable behavior (e.g., 5 becomes 2, not 2.5)

## E2E Testing Recommendations

1. Start game, buy a Torch from Merchant
2. Travel to Dark Cave with torch equipped
3. Verify dread increase is halved compared to traveling without torch
4. Travel at night to verify night dread bonus is negated
5. Travel multiple times to verify torch expires after 5 moves
6. Verify expiration message appears when torch runs out
7. Verify dread returns to normal after torch expires
