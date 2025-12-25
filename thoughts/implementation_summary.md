# Implementation Summary: AI-Generated NPC Conversations

## What Was Implemented

### Feature Overview
Added AI-generated dialogue for NPC conversations. When players talk to an NPC, the AI service can dynamically generate contextual dialogue that persists to the NPC's greetings list for consistency across sessions.

### Files Modified

1. **`src/cli_rpg/ai_config.py`**
   - Added `DEFAULT_NPC_DIALOGUE_PROMPT` constant - template for generating NPC dialogue
   - Added `npc_dialogue_prompt` field to `AIConfig` dataclass
   - Updated `to_dict()` to include the new field
   - Updated `from_dict()` to restore the field with proper default

2. **`src/cli_rpg/ai_service.py`**
   - Added `generate_npc_dialogue()` method - generates contextual dialogue for NPCs
   - Added `_build_npc_dialogue_prompt()` helper - formats the prompt template
   - Dialogue validation: 10-200 chars, strips quotes, truncates if too long

3. **`src/cli_rpg/main.py`**
   - Updated talk command handler (lines 416-429)
   - Triggers AI dialogue generation when NPC has < 3 greetings
   - Appends generated dialogue to NPC's greetings list
   - Silent fallback on errors - graceful degradation

4. **`tests/test_ai_conversations.py`** (new file)
   - 17 tests covering all spec requirements
   - Tests for AIService.generate_npc_dialogue()
   - Tests for talk command integration
   - Tests for persistence through save/load
   - Tests for AIConfig serialization

### Design Decisions

1. **Greetings Limit**: AI generation only triggers when NPC has fewer than 3 greetings. This prevents excessive API calls while still building variety.

2. **Role Detection**: NPC role is determined automatically:
   - `is_merchant=True` → "merchant"
   - `is_quest_giver=True` → "quest_giver"
   - Otherwise → "villager"

3. **Silent Fallback**: Any AI generation errors are silently caught. The existing `get_greeting()` method handles fallback to `dialogue` field.

4. **Persistence**: No changes needed to NPC serialization - existing `greetings` field already persists correctly.

## Test Results

- All 17 new tests pass
- All 30 related NPC/shop tests pass
- Full test suite: 963 passed, 1 skipped

## E2E Validation

To validate the feature end-to-end:
1. Start the game with AI service configured (set OPENAI_API_KEY or ANTHROPIC_API_KEY)
2. Navigate to a location with an NPC
3. Use `talk <npc_name>` command
4. Observe AI-generated dialogue being displayed
5. Talk to same NPC multiple times - should see variety up to 3 greetings
6. Save and reload game - greetings should persist

## Code Quality

- Type hints used throughout
- Docstrings added for new methods
- Follows existing patterns in the codebase
- No linting issues (black/ruff compliant)
