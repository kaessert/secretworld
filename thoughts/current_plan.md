# Implementation Plan: Add `lore` Command

## Summary
Add a player-accessible `lore` command that exposes the existing `AIService.generate_lore()` method, allowing players to discover AI-generated lore snippets about their current location.

## Spec
- **Command**: `lore` (no shorthand alias needed - low-frequency use)
- **Behavior**:
  - Generates an AI-powered lore snippet about the current location using `AIService.generate_lore()`
  - Falls back to a default message when AI is unavailable
  - Uses the game's current theme and location name for context
  - Randomly selects a lore category (history, legend, secret) for variety
- **Output**: Displays lore wrapped in an immersive header like "=== Ancient Lore ===" or "=== Local Legend ==="

## Tests First (TDD)

**File**: `tests/test_lore_command.py`

1. `test_lore_command_is_recognized` - parse_command recognizes "lore" as valid
2. `test_lore_command_without_ai_shows_fallback` - Returns fallback message when no AI service
3. `test_lore_command_with_ai_calls_generate_lore` - Calls AIService.generate_lore with correct args
4. `test_lore_command_displays_lore_with_header` - Output includes header and lore text
5. `test_lore_command_handles_ai_error_gracefully` - Catches AI exceptions, shows fallback

## Implementation Steps

### 1. Add "lore" to known commands
**File**: `src/cli_rpg/game_state.py` (line ~66)
- Add `"lore"` to `known_commands` set in `parse_command()`

### 2. Add lore command handler
**File**: `src/cli_rpg/main.py` (in `handle_exploration_command()`, around line ~740)
- Add `elif command == "lore":` branch
- Implementation:
  ```python
  elif command == "lore":
      import random
      if game_state.ai_service is None:
          return (True, "\n=== Ancient Lore ===\nNo mystical knowledge is available in this realm.")

      categories = ["history", "legend", "secret"]
      category = random.choice(categories)
      headers = {
          "history": "Ancient History",
          "legend": "Local Legend",
          "secret": "Forbidden Secret"
      }

      try:
          lore = game_state.ai_service.generate_lore(
              theme=game_state.theme,
              location_name=game_state.current_location,
              lore_category=category
          )
          return (True, f"\n=== {headers[category]} ===\n{lore}")
      except Exception:
          return (True, "\n=== Ancient Lore ===\nThe mysteries of this place remain hidden...")
  ```

### 3. Add to help text
**File**: `src/cli_rpg/main.py` (in `get_command_reference()`, around line 37)
- Add: `"  lore             - Discover lore about your current location",` after the map command
