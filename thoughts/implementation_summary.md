# Implementation Summary: Faction Reputation Consequences for Combat

## What Was Implemented

This feature wires faction reputation changes into combat outcomes. When the player defeats enemies affiliated with a faction, their reputation with that faction decreases, while reputation with opposing factions increases.

### New Files

- **`src/cli_rpg/faction_combat.py`**: New module containing:
  - `FACTION_REPUTATION_LOSS = 5`: Constant for rep lost when killing faction enemy
  - `FACTION_REPUTATION_GAIN = 3`: Constant for rep gained with rival faction
  - `FACTION_ENEMIES`: Mapping of enemy name patterns to factions (bandit/thief/ruffian/outlaw → Thieves Guild, guard/soldier/knight/captain → Town Guard)
  - `FACTION_RIVALRIES`: Mapping of factions to their rivals (Thieves Guild ↔ Town Guard)
  - `get_enemy_faction(enemy_name: str) -> Optional[str]`: Determine faction from enemy name patterns
  - `apply_combat_reputation(factions, enemies) -> list[str]`: Apply reputation changes after combat victory

- **`tests/test_faction_combat.py`**: Comprehensive test suite with 14 tests covering:
  - Enemy faction affiliation field (default None, setting, serialization)
  - Faction enemy mapping (bandit-type, guard-type, unaffiliated)
  - Combat reputation changes (reduces faction rep, increases rival rep, handles mixed enemies, unknown factions)

### Modified Files

1. **`src/cli_rpg/models/enemy.py`**:
   - Added `faction_affiliation: Optional[str] = None` field to Enemy dataclass
   - Updated `to_dict()` to include `faction_affiliation`
   - Updated `from_dict()` to restore `faction_affiliation`

2. **`src/cli_rpg/combat.py`**:
   - Added `game_state: Optional["GameState"] = None` parameter to `CombatEncounter.__init__()`
   - Added `from cli_rpg.game_state import GameState` to TYPE_CHECKING block
   - Updated `end_combat()` to call `apply_combat_reputation()` and append reputation change messages to victory output

3. **`src/cli_rpg/game_state.py`**:
   - Updated `trigger_encounter()` to pass `game_state=self` to CombatEncounter
   - Updated boss encounter in `enter_location()` to pass `game_state=self`

4. **`src/cli_rpg/shadow_creature.py`**:
   - Updated CombatEncounter creation to pass `game_state=game_state`

5. **`src/cli_rpg/hallucinations.py`**:
   - Updated CombatEncounter creation to pass `game_state=game_state`

6. **`src/cli_rpg/world_events.py`**:
   - Updated CombatEncounter creation to pass `game_state=game_state`

7. **`src/cli_rpg/random_encounters.py`**:
   - Updated CombatEncounter creation to pass `game_state=game_state`

8. **`tests/test_enemy.py`**:
   - Updated `test_to_dict_serializes_enemy` to include new `faction_affiliation` field

## Test Results

All 3128 tests pass, including:
- 14 new tests in `test_faction_combat.py`
- 75 combat tests
- 14 enemy tests
- 27 faction tests

## Design Decisions

1. **Pattern-based faction detection**: The `get_enemy_faction()` function uses case-insensitive substring matching, allowing "Forest Bandit" or "Bandit Leader" to be recognized as Thieves Guild enemies.

2. **Optional game_state**: CombatEncounter's game_state parameter is optional for backward compatibility. If not provided (or if factions list is empty), no reputation changes occur.

3. **Explicit faction affiliation**: Enemies can have an explicit `faction_affiliation` field that overrides pattern-based detection. This allows for more control over faction associations.

4. **Graceful handling of unknown factions**: If an enemy has a faction_affiliation that doesn't exist in the game's factions list, no reputation changes occur (silently ignored).

## Reputation Changes (MVP)

| Enemy Pattern | Affiliated Faction | Opposing Faction |
|---------------|-------------------|------------------|
| Bandit, Thief, Ruffian, Outlaw | Thieves Guild | Town Guard |
| Guard, Soldier, Knight, Captain | Town Guard | Thieves Guild |

- Kill affiliated enemy: -5 reputation with that faction
- Kill affiliated enemy: +3 reputation with opposing faction

## E2E Validation

To validate this feature end-to-end:
1. Start a new game with factions enabled (Thieves Guild and Town Guard)
2. Travel to an area where bandits spawn
3. Defeat a bandit in combat
4. Verify the victory message shows "Your reputation with Thieves Guild decreased by 5." and "Your reputation with Town Guard increased by 3."
5. Use the `reputation` command to verify faction standings changed correctly
