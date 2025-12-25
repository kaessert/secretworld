# Implementation Plan: Add ASCII Art for NPCs

## Summary
Add ASCII art display when talking to NPCs, following the established pattern for locations and combat monsters.

## Spec
When a player talks to an NPC, display ASCII art of the NPC above or alongside the greeting dialogue. ASCII art should be:
- AI-generated when AI service is available
- Template-based fallback when AI fails or is unavailable
- 5-7 lines tall, max 40 chars wide (similar to enemy art)
- Based on NPC role: merchant, quest_giver, villager, guard, etc.

## Files to Modify

### 1. `src/cli_rpg/models/npc.py`
- Add `ascii_art: str = ""` field to NPC dataclass
- Update `to_dict()` to include ascii_art (only when non-empty)
- Update `from_dict()` to load ascii_art with fallback

### 2. `src/cli_rpg/npc_art.py` (NEW)
- Create fallback ASCII art templates for NPC roles:
  - merchant, quest_giver, villager, guard, elder, blacksmith, innkeeper, default
- Create `get_fallback_npc_ascii_art(role: Optional[str], npc_name: str) -> str`

### 3. `src/cli_rpg/ai_config.py`
- Add `DEFAULT_NPC_ASCII_ART_PROMPT` template
- Add `npc_ascii_art_generation_prompt` field to `AIConfig`

### 4. `src/cli_rpg/ai_service.py`
- Add `generate_npc_ascii_art()` method (similar to enemy/location art)
- Add `_build_npc_ascii_art_prompt()` helper
- Add `_parse_npc_ascii_art_response()` validation

### 5. `src/cli_rpg/main.py`
- In `handle_exploration_command()` talk command handler:
  - Generate/get NPC ASCII art if not already set
  - Display ASCII art above greeting dialogue

## Tests to Write

### `tests/test_npc_ascii_art.py` (NEW)
1. **TestNPCModelAsciiArt**
   - test_npc_model_has_ascii_art_field
   - test_npc_to_dict_includes_ascii_art
   - test_npc_from_dict_loads_ascii_art
   - test_npc_default_ascii_art_is_empty

2. **TestFallbackNPCAsciiArt**
   - test_get_fallback_art_merchant
   - test_get_fallback_art_quest_giver
   - test_get_fallback_art_villager
   - test_get_fallback_art_guard
   - test_get_fallback_art_default

3. **TestTalkCommandAsciiArt**
   - test_talk_displays_ascii_art_when_present
   - test_talk_generates_art_with_ai
   - test_talk_uses_fallback_without_ai

4. **TestAINPCAsciiArtGeneration**
   - test_ai_npc_ascii_art_generation
   - test_ai_npc_ascii_art_prompt_formatting

## Implementation Order

1. Add ascii_art field to NPC model
2. Create npc_art.py with fallback templates
3. Add prompt template to ai_config.py
4. Add generate_npc_ascii_art() to ai_service.py
5. Update talk command to display art
6. Write and run tests
