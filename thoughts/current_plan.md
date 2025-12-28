# Discovery Milestones Implementation Plan

## Feature: Issue 24 - Discovery Milestones (first secret, all treasures, boss defeated)

### Overview
Add discovery milestone tracking and player feedback messages when the player achieves significant exploration accomplishments within a SubGrid.

---

## Spec

**Milestones to track per SubGrid:**
1. **First Secret Found** - When player discovers their first secret (via passive detection or `search` command)
2. **All Treasures Opened** - When player opens the last treasure chest in the SubGrid
3. **Boss Defeated** - When player defeats the boss in the SubGrid (already partially tracked via `boss_defeated`)

**Rewards:**
- Each milestone awards bonus XP (25 per milestone)
- Visual celebration message with star decoration

---

## Implementation

### 1. Extend SubGrid with milestone tracking

**File:** `src/cli_rpg/world_grid.py`

Add fields to `SubGrid` dataclass:
```python
first_secret_found: bool = False
all_treasures_opened: bool = False
boss_milestone_awarded: bool = False
```

Add helper methods:
```python
def get_treasure_stats(self) -> tuple[int, int]:
    """Get (opened_count, total_count) for treasures."""

def are_all_treasures_opened(self) -> bool:
    """Check if all treasures have been opened."""
```

Update `to_dict()` and `from_dict()` for serialization (with backward-compat defaults).

### 2. Add milestone constants and method to GameState

**File:** `src/cli_rpg/game_state.py`

Add constants:
```python
MILESTONE_XP_FIRST_SECRET = 25
MILESTONE_XP_ALL_TREASURES = 25
MILESTONE_XP_BOSS_DEFEATED = 25
```

Add method:
```python
def check_and_award_milestones(self, event_type: str) -> Optional[str]:
    """Check and award discovery milestones based on event type."""
```

### 3. Integrate milestone triggers

**File:** `src/cli_rpg/main.py`

- After `perform_active_search()` succeeds: call `check_and_award_milestones("secret")`
- After `target_chest["opened"] = True`: call `check_and_award_milestones("treasure")`
- After `game_state.mark_boss_defeated()`: call `check_and_award_milestones("boss")`

**File:** `src/cli_rpg/game_state.py`

- In `_trigger_passive_secrets()`: after detecting secrets, trigger "secret" milestone check

---

## Tests

**File:** `tests/test_discovery_milestones.py`

| Test Class | Tests |
|------------|-------|
| `TestSubGridMilestoneTracking` | Default fields, serialization, backward compat |
| `TestTreasureStats` | `get_treasure_stats()`, `are_all_treasures_opened()` |
| `TestFirstSecretMilestone` | Awards XP, only once, message format |
| `TestAllTreasuresMilestone` | Awards XP, only once, partial no award |
| `TestBossDefeatedMilestone` | Awards XP, only once, no award outside SubGrid |

Estimated: ~15 tests

---

## Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/world_grid.py` | +3 fields, +2 methods, serialization |
| `src/cli_rpg/game_state.py` | +3 constants, +1 method, integrate in passive secrets |
| `src/cli_rpg/main.py` | +3 milestone trigger points |
| `tests/test_discovery_milestones.py` | New file (~15 tests) |

---

## Acceptance Criteria

- [ ] First secret discovered in SubGrid triggers milestone (+25 XP)
- [ ] Opening last treasure in SubGrid triggers milestone (+25 XP)
- [ ] Defeating boss in SubGrid triggers milestone (+25 XP)
- [ ] Each milestone only awarded once per SubGrid
- [ ] Milestones persist in save/load
- [ ] Backward compatible with existing saves
