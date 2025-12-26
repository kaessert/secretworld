# Implementation Plan: Faction Reputation Consequences for Combat

## Spec

Wire faction reputation changes into combat outcomes. When the player defeats enemies affiliated with a faction, their reputation with that faction decreases, while reputation with opposing factions increases.

**Design:**
- Add `faction_affiliation: Optional[str]` field to Enemy model (name matches a faction)
- Create `FACTION_ENEMIES` mapping: enemy name patterns → faction affiliations
- Create `FACTION_RIVALRIES` mapping: when a faction enemy is killed, rival factions gain rep
- On combat victory in `CombatEncounter.end_combat()`, apply reputation changes via GameState
- Display reputation change messages to player

**Faction Mappings (MVP):**
| Enemy Pattern | Affiliated Faction | Opposing Faction |
|---------------|-------------------|------------------|
| Bandit, Thief, Ruffian, Outlaw | Thieves Guild | Town Guard |
| Guard, Soldier, Knight, Captain | Town Guard | Thieves Guild |

**Reputation Changes:**
- Kill affiliated enemy: -5 reputation with that faction
- Kill affiliated enemy: +3 reputation with opposing faction

## Tests First (TDD)

### `tests/test_faction_combat.py`

1. `TestEnemyFactionAffiliation`:
   - `test_enemy_faction_affiliation_default_none`: Enemy has no faction by default
   - `test_enemy_faction_affiliation_set`: Can set faction_affiliation on Enemy
   - `test_enemy_faction_affiliation_serialization`: Faction persists through to_dict/from_dict

2. `TestFactionEnemyMapping`:
   - `test_get_enemy_faction_bandit`: Returns "Thieves Guild" for bandit-type enemies
   - `test_get_enemy_faction_guard`: Returns "Town Guard" for guard-type enemies
   - `test_get_enemy_faction_none`: Returns None for unaffiliated enemies (e.g., "Goblin")

3. `TestCombatReputationChanges`:
   - `test_combat_victory_reduces_faction_rep`: Killing bandit reduces Thieves Guild rep by 5
   - `test_combat_victory_increases_rival_rep`: Killing bandit increases Town Guard rep by 3
   - `test_combat_victory_no_faction_no_rep_change`: Killing unaffiliated enemy has no effect
   - `test_combat_victory_displays_rep_messages`: Victory message includes rep change info
   - `test_combat_victory_multiple_enemies`: Each affiliated enemy contributes rep changes

## Implementation Steps

### Step 1: Add faction_affiliation to Enemy model
**File:** `src/cli_rpg/models/enemy.py`
- Add `faction_affiliation: Optional[str] = None` field
- Update `to_dict()` to include `faction_affiliation`
- Update `from_dict()` to restore `faction_affiliation`

### Step 2: Create faction combat module
**File:** `src/cli_rpg/faction_combat.py`
- Constants:
  - `FACTION_REPUTATION_LOSS = 5` (killing affiliated enemy)
  - `FACTION_REPUTATION_GAIN = 3` (rival faction bonus)
- `FACTION_ENEMIES`: dict mapping enemy name patterns to faction names
  ```python
  FACTION_ENEMIES = {
      "bandit": "Thieves Guild",
      "thief": "Thieves Guild",
      "ruffian": "Thieves Guild",
      "outlaw": "Thieves Guild",
      "guard": "Town Guard",
      "soldier": "Town Guard",
      "knight": "Town Guard",
      "captain": "Town Guard",
  }
  ```
- `FACTION_RIVALRIES`: dict mapping faction to its rival
  ```python
  FACTION_RIVALRIES = {
      "Thieves Guild": "Town Guard",
      "Town Guard": "Thieves Guild",
  }
  ```
- `get_enemy_faction(enemy_name: str) -> Optional[str]`: Check enemy name against patterns
- `apply_combat_reputation(game_state, enemies: list[Enemy]) -> list[str]`: Apply all rep changes

### Step 3: Wire into CombatEncounter.end_combat()
**File:** `src/cli_rpg/combat.py`
- Add optional `game_state` parameter to `CombatEncounter.__init__()` for faction access
- In `end_combat(victory=True)`, after XP/loot:
  - Import and call `apply_combat_reputation(self.game_state, self.enemies)`
  - Append returned messages to victory output
- Update `GameState.trigger_encounter()` to pass `game_state=self` to CombatEncounter

### Step 4: Run tests and verify
```bash
pytest tests/test_faction_combat.py -v
pytest tests/test_faction.py -v
pytest --cov=src/cli_rpg --cov-report=term-missing
```
