# Implementation Plan: Safe Zone Checking for Random Encounters

## Spec

**Goal**: Locations marked with `is_safe_zone=True` should not trigger random hostile encounters.

**Behavior**:
- In `check_for_random_encounter()`, skip ALL random encounters (hostile, merchant, wanderer) when `is_safe_zone=True`
- This prevents combat interruptions in safe zones (towns, villages, inns, temples)
- Non-hostile encounters (merchants, wanderers) are also skipped since safe zones are populated areas with existing NPCs

## Tests First

Add to `tests/test_random_encounters.py`:

```python
class TestSafeZoneEncounters:
    """Tests for safe zone encounter behavior."""

    @pytest.fixture
    def game_state_with_safe_zone(self, monkeypatch):
        """Create game state with a safe zone location."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)

        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Town": Location(
                "Town Square", "A safe town square",
                {"north": "Road"}, coordinates=(0, 0), is_safe_zone=True
            ),
            "Road": Location(
                "Road", "A dangerous road",
                {"south": "Town"}, coordinates=(0, 1), is_safe_zone=False
            ),
        }
        return GameState(character, world, "Town")

    def test_no_encounter_in_safe_zone(self, game_state_with_safe_zone, monkeypatch):
        """No random encounters in safe zones.

        Spec: is_safe_zone=True prevents all random encounters
        """
        # Mock random to always trigger encounter (if not blocked)
        mock_random = MagicMock(return_value=0.05)  # Would trigger encounter
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        result = check_for_random_encounter(game_state_with_safe_zone)

        # Should be None because we're in a safe zone
        assert result is None
        assert not game_state_with_safe_zone.is_in_combat()

    def test_encounter_allowed_in_non_safe_zone(self, game_state_with_safe_zone, monkeypatch):
        """Random encounters work in non-safe zones.

        Spec: is_safe_zone=False allows normal encounter behavior
        """
        # Move to the dangerous road first
        game_state_with_safe_zone.current_location = "Road"

        # Mock to trigger hostile encounter
        random_values = [0.05, 0.30]  # trigger=True, type=hostile
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)
        monkeypatch.setattr("cli_rpg.combat.random.choice", lambda x: x[0])
        monkeypatch.setattr("cli_rpg.combat.random.randint", lambda a, b: a)

        result = check_for_random_encounter(game_state_with_safe_zone)

        # Should trigger encounter in non-safe zone
        assert result is not None
        assert "[Random Encounter!]" in result
```

## Implementation

**File**: `src/cli_rpg/random_encounters.py`

**Change**: Add safe zone check at the start of `check_for_random_encounter()` function (after line 230, before the RNG roll):

```python
def check_for_random_encounter(game_state: "GameState") -> Optional[str]:
    # ... existing docstring ...

    # Don't trigger if already in combat
    if game_state.is_in_combat():
        return None

    # Don't trigger in safe zones (towns, villages, etc.)
    location = game_state.get_current_location()
    if location.is_safe_zone:
        return None

    # Roll for encounter
    if random.random() > RANDOM_ENCOUNTER_CHANCE:
        return None

    # ... rest of function unchanged ...
```

**Location**: Insert the safe zone check between line 231 and 233 (after combat check, before RNG roll).

## Verification

1. Run existing tests to ensure no regressions: `pytest tests/test_random_encounters.py -v`
2. Run new safe zone tests: `pytest tests/test_random_encounters.py::TestSafeZoneEncounters -v`
3. Run full test suite: `pytest`
