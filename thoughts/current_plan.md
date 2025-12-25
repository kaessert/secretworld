# Implementation Plan: Companion Banter During Travel

## Scope
Add occasional companion comments that appear during travel (movement), following the whisper system pattern. Companions comment on surroundings, share thoughts, or react to conditions (weather, time, dread level).

---

## 1. Spec: Companion Banter System

### Trigger Behavior
- **25% chance** per move when companions are present (similar to whisper 30%)
- Only one banter per move (pick random companion if multiple)
- No banter during combat
- Higher bond level = more varied/deeper banter

### Banter Categories (by trigger condition)
1. **Location-based**: Comments about location category (town, dungeon, forest, etc.)
2. **Weather-based**: React to weather conditions (rain, storm, fog)
3. **Time-based**: Day/night observations
4. **Dread-based**: Nervous comments at high dread (50%+)
5. **Bond-level-based**: More personal comments at TRUSTED/DEVOTED levels

### Banter Format
```
[Companion] Elara: "I've heard stories about places like this..."
```
Styled with companion name in color, quote formatted similarly to whispers.

---

## 2. Tests to Write First

### File: `tests/test_companion_banter.py`

```python
# Test banter service creation
test_banter_service_creation

# Test banter triggering
test_banter_returns_none_when_no_companions
test_banter_respects_trigger_chance  # ~25% rate
test_banter_selects_random_companion

# Test category-based banter
test_banter_for_town_location
test_banter_for_dungeon_location
test_banter_for_forest_location
test_banter_fallback_for_unknown_category

# Test conditional banter
test_banter_references_weather_in_storm
test_banter_references_night_time
test_banter_nervous_at_high_dread

# Test bond-level influence
test_banter_varies_by_bond_level
test_devoted_companion_more_personal_banter

# Test formatting
test_format_banter_with_companion_name
test_format_banter_has_correct_prefix
```

### File: `tests/test_companion_banter_integration.py`

```python
# Integration with GameState.move()
test_banter_appears_on_move_with_companion
test_no_banter_on_move_without_companions
test_no_banter_during_combat
test_banter_and_whisper_can_coexist  # Both may appear in same move
```

---

## 3. Implementation Steps

### Step 1: Create Companion Banter Module
**File:** `src/cli_rpg/companion_banter.py`

```python
BANTER_CHANCE = 0.25  # 25% chance per move

# Template banter by location category
CATEGORY_BANTER = {
    "town": [
        "It's nice to be somewhere civilized for a change.",
        "I could use a warm meal and a soft bed.",
        "These markets remind me of home...",
    ],
    "dungeon": [
        "Stay close. I don't like the look of this place.",
        "What manner of creature lives in such darkness?",
        "I've got a bad feeling about this...",
    ],
    "forest": [
        "The trees here are ancient. They've seen much.",
        "Listen to the birds. They know when danger is near.",
        "This path looks rarely traveled.",
    ],
    # ... more categories
    "default": [
        "Interesting place...",
        "I wonder what we'll find here.",
        "Stay alert.",
    ],
}

# Weather-specific banter
WEATHER_BANTER = {
    "rain": ["This rain is relentless.", "At least it covers our tracks."],
    "storm": ["We should find shelter!", "I can barely see in this storm!"],
    "fog": ["Stay close, I can barely see you.", "Something feels wrong in this fog."],
}

# Night-specific banter
NIGHT_BANTER = [
    "The darkness makes every sound seem louder.",
    "I'll keep watch. You look tired.",
    "Stars are beautiful tonight, at least.",
]

# High-dread banter (50%+)
DREAD_BANTER = [
    "Did you hear that? ...Never mind.",
    "I don't like this. Not one bit.",
    "Something is watching us. I can feel it.",
]

# Bond-level specific banter (unlocked at higher levels)
TRUSTED_BANTER = [
    "I'm glad you're the one leading us.",
    "We've been through a lot together, haven't we?",
]
DEVOTED_BANTER = [
    "There's no one else I'd rather face this with.",
    "Whatever happens, I've got your back.",
]

class CompanionBanterService:
    def get_banter(
        self,
        companions: list[Companion],
        location_category: Optional[str],
        weather: str = "clear",
        is_night: bool = False,
        dread: int = 0,
    ) -> Optional[tuple[str, str]]:
        """Get banter from a random companion.

        Returns:
            Tuple of (companion_name, banter_text) or None
        """
        # Implementation...

def format_banter(companion_name: str, banter_text: str) -> str:
    """Format banter for display."""
    # [Companion] Name: "text"
```

### Step 2: Integrate with GameState.move()
**File:** `src/cli_rpg/game_state.py`

- Import `CompanionBanterService, format_banter`
- Add `banter_service = CompanionBanterService()` in `__init__`
- In `move()`, after whisper check:
  ```python
  # Check for companion banter (only when not in combat)
  if not self.is_in_combat() and self.companions:
      banter = self.banter_service.get_banter(
          companions=self.companions,
          location_category=location.category,
          weather=self.weather.condition,
          is_night=self.game_time.is_night(),
          dread=self.current_character.dread_meter.dread
      )
      if banter:
          companion_name, banter_text = banter
          message += f"\n{format_banter(companion_name, banter_text)}"
  ```

### Step 3: Add Color Helper for Companion
**File:** `src/cli_rpg/colors.py`
- Add `companion()` function for consistent styling (if not exists)

---

## 4. File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/companion_banter.py` | NEW - Banter service + templates |
| `src/cli_rpg/game_state.py` | Add banter check in move() |
| `src/cli_rpg/colors.py` | Add companion() color helper (if needed) |
| `tests/test_companion_banter.py` | NEW - Banter service tests |
| `tests/test_companion_banter_integration.py` | NEW - Integration tests |

---

## 5. Acceptance Criteria

1. **Banter triggers ~25%** of moves when companions present
2. **No banter** when no companions or during combat
3. **Context-aware**: Location, weather, time, dread influence banter
4. **Bond-level depth**: TRUSTED/DEVOTED companions have richer banter
5. **Formatted correctly**: `[Companion] Name: "text"` format
6. **All tests pass**: Including existing 2160 tests
