# Implementation Plan: Camping & Wilderness Survival

## Feature Overview

Add wilderness survival mechanics with `camp`, `forage`, and `hunt` commands that integrate with existing dread, inventory, random encounters, and day/night systems.

## Spec

### 1. `camp` Command
- **Requires**: Wilderness location (category: forest, wilderness, cave, ruins - NOT town/village/safe zones)
- **Uses supplies**: Consumes 1 "Camping Supplies" item from inventory
- **Effects**:
  - Heal 50% of max HP (double rest amount)
  - Reduce dread by 30 (50% more than rest)
  - Advance time by 8 hours (camping is longer)
  - Trigger dream with 40% chance (higher than rest's 25%)
  - **Campfire bonus**: If player uses a light source before/during camp, reduce dread by extra 10 (total -40)
- **Random events**: 20% chance of wandering NPC (trader, storyteller) attracted to campfire
- **Blocked in**: Safe zones (use `rest` there), combat

### 2. `forage` Command
- **Requires**: Wilderness/forest location (NOT town/dungeon)
- **Skill check**: Base 40% + (perception × 2%) success rate
- **Success**: Find 1-2 random items:
  - Herbs (heal 10 HP consumable)
  - Wild Berries (heal 15 HP consumable)
  - Medicinal Root (heal 20 HP consumable)
  - Rare: Moonpetal Flower (mana restore 20, only at night)
- **Failure**: "You search but find nothing useful."
- **Cooldown**: 1 hour in-game time (advances on attempt)
- **Blocked in**: Safe zones, dungeons, combat

### 3. `hunt` Command
- **Requires**: Wilderness/forest location (NOT town/dungeon)
- **Skill check**: Base 30% + (dexterity × 2%) + (perception × 1%) success rate
- **Success**: Obtain "Raw Meat" item (heal 30 HP, but only when consumed at camp with campfire)
- **Critical success** (roll ≤ 10% of success chance): Also obtain "Animal Pelt" (sell for 25 gold)
- **Failure**: "The prey escapes before you can catch it."
- **Cooldown**: 2 hours in-game time
- **Blocked in**: Safe zones, dungeons, combat

### 4. New Items
| Item | Type | Effect | Found/Bought |
|------|------|--------|--------------|
| Camping Supplies | Consumable | Required for camp command | Shop (40 gold) |
| Herbs | Consumable | Heal 10 HP | Forage |
| Wild Berries | Consumable | Heal 15 HP | Forage |
| Medicinal Root | Consumable | Heal 20 HP | Forage |
| Moonpetal Flower | Consumable | Restore 20 mana | Forage (night only) |
| Raw Meat | Consumable | Heal 30 HP (campfire only) | Hunt |
| Animal Pelt | Misc | Sell for 25 gold | Hunt (crit) |
| Cooked Meat | Consumable | Heal 40 HP | Cook Raw Meat at camp |

### 5. Campfire Mechanics
- Having active light (light_remaining > 0) when camping = campfire active
- Campfire effects:
  - Extra -10 dread reduction
  - Can cook Raw Meat → Cooked Meat (heal 40 vs 30)
  - Attracts wandering NPCs (20% chance)

## Implementation Steps

### Step 1: Create `camping.py` module
**File**: `src/cli_rpg/camping.py`
- Define campable location categories: `{"forest", "wilderness", "cave", "ruins"}`
- `is_campable_location(location: Location) -> bool`
- `execute_camp(game_state: GameState) -> tuple[bool, str]`
- `execute_forage(game_state: GameState) -> tuple[bool, str]`
- `execute_hunt(game_state: GameState) -> tuple[bool, str]`
- `_spawn_campfire_visitor(game_state: GameState) -> Optional[str]` - spawn wandering NPC

### Step 2: Create forage/hunt item templates
**File**: `src/cli_rpg/camping.py` (same file)
- `FORAGE_ITEMS` list with name, description, type, heal_amount/mana_restore, rarity weight
- `HUNT_RESULTS` dict with success/critical items
- `_generate_forage_item(is_night: bool) -> Item`
- `_generate_hunt_result(is_critical: bool) -> list[Item]`

### Step 3: Add Camping Supplies to shops
**File**: `src/cli_rpg/world.py`
- Add "Camping Supplies" item to Market District shop (40 gold)
- Add to Millbrook Village shop (30 gold - rural discount)

### Step 4: Add cooldown tracking to GameState
**File**: `src/cli_rpg/game_state.py`
- Add `forage_cooldown: int = 0` and `hunt_cooldown: int = 0` fields
- Cooldowns are game time hours, decremented in `game_time.advance()`
- Add to serialization (`to_dict`/`from_dict`) with backward compat

### Step 5: Integrate commands in main.py
**File**: `src/cli_rpg/main.py`
- Add `"camp", "forage", "hunt"` to `KNOWN_COMMANDS`
- Add aliases: `"ca": "camp", "fg": "forage", "hu": "hunt"`
- Add command handlers in `handle_exploration_command()`
- Add to `get_command_reference()` help text

### Step 6: Add Raw Meat cooking logic
**File**: `src/cli_rpg/camping.py`
- In `execute_camp()`: If player has "Raw Meat" and campfire, offer to cook
- Replace "Raw Meat" with "Cooked Meat" (heal 40 HP)
- Display cooking message

### Step 7: Implement campfire visitor spawning
**File**: `src/cli_rpg/camping.py`
- `CAMPFIRE_VISITORS` list with NPC templates:
  - Wandering Storyteller (shares lore, reduces dread by 5)
  - Traveling Merchant (offers 1-2 discounted items)
  - Lost Traveler (just flavor dialogue)
- 20% chance when camping with campfire

## Test Plan

### Test File: `tests/test_camping.py`

#### Unit Tests
1. `test_is_campable_location_forest` - forest is campable
2. `test_is_campable_location_wilderness` - wilderness is campable
3. `test_is_campable_location_town_not_campable` - town is not campable
4. `test_is_campable_location_safe_zone_not_campable` - safe zones not campable

#### Camp Command Tests
5. `test_camp_requires_supplies` - fails without Camping Supplies
6. `test_camp_consumes_supplies` - removes 1 Camping Supplies from inventory
7. `test_camp_heals_50_percent` - heals 50% of max HP
8. `test_camp_reduces_dread_30` - reduces dread by 30
9. `test_camp_with_campfire_extra_dread_reduction` - 40 total dread reduction with light
10. `test_camp_advances_time_8_hours` - time advances by 8
11. `test_camp_blocked_in_safe_zone` - returns error in town
12. `test_camp_blocked_in_combat` - returns error in combat
13. `test_camp_cooks_raw_meat` - Raw Meat becomes Cooked Meat if campfire

#### Forage Command Tests
14. `test_forage_success_adds_item` - item added to inventory on success
15. `test_forage_failure_no_item` - no item on failure
16. `test_forage_blocked_in_town` - returns error in town
17. `test_forage_blocked_in_dungeon` - returns error in dungeon
18. `test_forage_night_moonpetal` - Moonpetal only at night
19. `test_forage_sets_cooldown` - cooldown set to 1 hour
20. `test_forage_blocked_on_cooldown` - cannot forage during cooldown

#### Hunt Command Tests
21. `test_hunt_success_gives_meat` - Raw Meat on success
22. `test_hunt_critical_gives_pelt` - Animal Pelt on critical
23. `test_hunt_failure_no_item` - no item on failure
24. `test_hunt_blocked_in_town` - returns error in town
25. `test_hunt_sets_cooldown` - cooldown set to 2 hours
26. `test_hunt_blocked_on_cooldown` - cannot hunt during cooldown

#### Integration Tests
27. `test_camp_command_in_forest` - full integration in forest location
28. `test_forage_hunt_cooldown_decrements` - cooldowns tick down with time
29. `test_campfire_visitor_spawn` - visitor NPC spawns at camp
30. `test_camping_persistence` - cooldowns save/load correctly

#### Parse Command Tests
31. `test_parse_camp_command` - "camp" recognized
32. `test_parse_camp_alias` - "ca" expands to "camp"
33. `test_parse_forage_command` - "forage" recognized
34. `test_parse_forage_alias` - "fg" expands to "forage"
35. `test_parse_hunt_command` - "hunt" recognized
36. `test_parse_hunt_alias` - "hu" expands to "hunt"

#### Help Text Tests
37. `test_help_includes_camp` - camp in help output
38. `test_help_includes_forage` - forage in help output
39. `test_help_includes_hunt` - hunt in help output

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/camping.py` | **NEW** - Core camping, forage, hunt logic |
| `src/cli_rpg/game_state.py` | Add forage/hunt cooldown fields, serialization |
| `src/cli_rpg/main.py` | Add commands, aliases, handlers, help text |
| `src/cli_rpg/world.py` | Add Camping Supplies to shops |
| `tests/test_camping.py` | **NEW** - All tests for camping feature |
