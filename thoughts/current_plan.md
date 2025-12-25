# Random Travel Encounters - Implementation Plan

## Feature Summary
Add a random encounter system that triggers occasional events (hostile enemies, friendly merchants, or neutral wanderers) when the player moves between locations, adding urgency and emergent gameplay.

## Spec

### RandomEncounter Model
- **Type**: `dataclass` in new file `src/cli_rpg/models/random_encounter.py`
- **Fields**:
  - `encounter_type`: str ("hostile", "merchant", "wanderer")
  - `entity`: Union[Enemy, NPC] - the encounter entity
  - `description`: str - flavor text for the encounter
- **Serialization**: `to_dict()` / `from_dict()` for persistence

### Encounter Trigger Logic
- **Location**: Inside `GameState.move()` after successful movement (before whispers/combat)
- **Trigger chance**: 15% per move (configurable constant `RANDOM_ENCOUNTER_CHANCE = 0.15`)
- **Encounter types by weight**:
  - Hostile (60%): Triggers combat using existing `trigger_encounter()` pattern
  - Merchant (25%): Spawns a wandering merchant NPC with random wares
  - Wanderer (15%): Spawns a passive NPC with lore/hints

### Integration Points
- Hostile encounters: Reuse `spawn_enemy()` / `ai_spawn_enemy()` from `combat.py`
- Merchant encounters: Create temporary NPC with `is_merchant=True`, shop with 2-3 items
- Wanderer encounters: Create temporary NPC with atmospheric dialogue

### Output Format
```
You head north to Forest...

[Random Encounter!]
A traveling merchant blocks your path!
"Greetings traveler! Care to see my wares?"
(Use 'talk Merchant' to interact)
```

## Tests (TDD)

### File: `tests/test_random_encounters.py`

1. **test_random_encounter_model_creation** - RandomEncounter dataclass with required fields
2. **test_random_encounter_serialization** - to_dict/from_dict roundtrip
3. **test_move_can_trigger_random_encounter** - Move with seeded RNG triggers encounter (mock random)
4. **test_random_encounter_chance_configurable** - Verify 15% chance constant exists
5. **test_hostile_encounter_starts_combat** - Hostile encounter type creates CombatEncounter
6. **test_merchant_encounter_creates_npc** - Merchant encounter creates talkable NPC at location
7. **test_wanderer_encounter_creates_npc** - Wanderer encounter creates NPC at location
8. **test_no_encounter_when_already_in_combat** - Skip random encounters if combat active
9. **test_encounter_respects_location_category** - Hostile encounters use location category for enemy type
10. **test_encounter_message_format** - Verify output includes "[Random Encounter!]" marker

## Implementation Steps

1. **Create `src/cli_rpg/models/random_encounter.py`**
   - Define `RandomEncounter` dataclass
   - Add `to_dict()` / `from_dict()` methods

2. **Create `src/cli_rpg/random_encounters.py`**
   - Constants: `RANDOM_ENCOUNTER_CHANCE = 0.15`
   - Encounter type weights: `ENCOUNTER_WEIGHTS = {"hostile": 0.60, "merchant": 0.25, "wanderer": 0.15}`
   - `check_for_random_encounter(game_state) -> Optional[str]` - main trigger function
   - `spawn_wandering_merchant(level: int) -> NPC` - creates merchant NPC with shop
   - `spawn_wanderer(theme: str) -> NPC` - creates atmospheric NPC
   - `format_encounter_message(encounter: RandomEncounter) -> str` - formats output

3. **Modify `src/cli_rpg/game_state.py`**
   - Import `check_for_random_encounter` from new module
   - In `move()`: After successful movement and before whispers, call `check_for_random_encounter()`
   - If encounter returned, append message and handle side effects (start combat or add NPC)

4. **Write tests in `tests/test_random_encounters.py`**
   - Follow existing test patterns from `test_game_state.py`
   - Use `unittest.mock.patch` to control RNG for deterministic tests

## Files to Create/Modify
- **Create**: `src/cli_rpg/models/random_encounter.py`
- **Create**: `src/cli_rpg/random_encounters.py`
- **Create**: `tests/test_random_encounters.py`
- **Modify**: `src/cli_rpg/game_state.py` (add encounter check in move())
