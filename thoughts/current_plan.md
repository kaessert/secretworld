# Implementation Plan: AI-Powered NPC Extended Conversations

## Feature Spec

Extend the `talk` command to support multi-turn contextual conversations with NPCs. The player can continue chatting with an NPC beyond the initial greeting, with the AI maintaining context of the conversation.

**Behavior:**
1. `talk <npc>` - Initiates conversation, shows greeting (existing behavior)
2. While in conversation, player can type messages that get sent to the AI for contextual responses
3. Type `bye`, `leave`, or `exit` to end the conversation
4. Conversation history is maintained per-NPC and persists across save/load
5. Graceful fallback: If AI unavailable, show a generic "NPC nods" response

**Constraints:**
- Conversation history capped at 10 exchanges per NPC (to limit token usage)
- Each response limited to 200 characters
- Player enters "conversation mode" after talking to an NPC

---

## Tests (TDD - write first)

### File: `tests/test_npc_extended_conversations.py`

**NPC Model Tests:**
1. `test_npc_has_conversation_history_field` - NPC has `conversation_history: List[dict]` defaulting to `[]`
2. `test_npc_conversation_history_serialization` - History persists via to_dict/from_dict
3. `test_npc_add_conversation_entry` - `add_conversation(role, content)` adds entry to history
4. `test_npc_conversation_history_capped_at_10` - Oldest entries removed when exceeding 10

**AIService Tests:**
5. `test_generate_conversation_response_returns_string` - `generate_conversation_response()` returns string
6. `test_generate_conversation_response_includes_history` - Prompt includes conversation history
7. `test_generate_conversation_response_includes_npc_context` - Prompt includes NPC name/description/role
8. `test_generate_conversation_response_truncates_long_responses` - Caps at 200 chars
9. `test_generate_conversation_response_raises_on_short` - Raises AIGenerationError if < 10 chars

**GameState Tests:**
10. `test_game_state_in_conversation_property` - `is_in_conversation` returns True when `current_npc` set
11. `test_game_state_conversation_mode_blocks_movement` - `go` returns error when in conversation

**Main Command Handler Tests:**
12. `test_conversation_input_sent_to_ai` - Non-command input during conversation calls AI
13. `test_conversation_bye_exits` - "bye" clears current_npc and exits conversation mode
14. `test_conversation_leave_exits` - "leave" clears current_npc
15. `test_conversation_exit_exits` - "exit" clears current_npc
16. `test_conversation_adds_to_npc_history` - Both player input and AI response added to history
17. `test_conversation_fallback_without_ai` - Without ai_service, returns "NPC nods thoughtfully."

---

## Implementation Steps

### Step 1: Update NPC Model
**File:** `src/cli_rpg/models/npc.py`

- Add field: `conversation_history: List[dict] = field(default_factory=list)`
- Add method: `add_conversation(self, role: str, content: str) -> None`
  - Appends `{"role": role, "content": content}` to history
  - If `len(history) > 10`, remove oldest entry
- Update `to_dict()`: Include `conversation_history`
- Update `from_dict()`: Restore `conversation_history` (default `[]` for backward compat)

### Step 2: Add AIService.generate_conversation_response()
**File:** `src/cli_rpg/ai_service.py`

- Add method: `generate_conversation_response(npc_name, npc_description, npc_role, theme, location_name, conversation_history, player_input) -> str`
- Build prompt with:
  - NPC context (name, description, role, theme, location)
  - Conversation history formatted as dialogue
  - Player's latest input
  - Instructions: respond in-character, 1-2 sentences, 10-200 chars
- Call `_call_llm()`, strip/validate response
- Truncate to 200 chars if needed, raise if < 10 chars

### Step 3: Add Conversation Prompt Template
**File:** `src/cli_rpg/ai_config.py`

- Add `DEFAULT_NPC_CONVERSATION_PROMPT` constant
- Add field to `AIConfig`: `npc_conversation_prompt: str`
- Update `to_dict()` and `from_dict()` for new field

### Step 4: Update GameState
**File:** `src/cli_rpg/game_state.py`

- Add property: `is_in_conversation(self) -> bool` - returns `self.current_npc is not None`

### Step 5: Update Command Handling
**File:** `src/cli_rpg/main.py`

- Add `handle_conversation_input(game_state, user_input) -> tuple[bool, str]`
  - If input is "bye"/"leave"/"exit": clear `current_npc`, return exit message
  - Otherwise: call AI, add entries to NPC history, return AI response
  - Fallback without AI: return "NPC nods thoughtfully."
- Modify `run_game_loop()`:
  - After parsing command, check `game_state.is_in_conversation`
  - If in conversation AND command is "unknown": route to `handle_conversation_input`
  - Block movement commands (`go`) when in conversation
- Update `handle_exploration_command()` for `talk`:
  - After existing talk logic, add prompt: "(Continue chatting or type 'bye' to leave)"

### Step 6: Update Command Reference
**File:** `src/cli_rpg/main.py`

- Update help text to mention extended conversations
