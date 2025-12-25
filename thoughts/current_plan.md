# AI-Powered Quest Generation Implementation Plan

## Feature Spec

Add `AIService.generate_quest()` method following the existing 3-layer pattern (public method → build prompt → parse response) to dynamically generate quests appropriate to the world theme, location, and player level.

**Output dict fields:**
- `name`: str (2-30 chars) - Quest name
- `description`: str (1-200 chars) - Quest narrative
- `objective_type`: str - One of "kill", "collect", "explore", "talk", "drop"
- `target`: str - Target name (enemy type, item name, location, or NPC)
- `target_count`: int (≥1) - Number to complete
- `gold_reward`: int (≥0) - Gold reward
- `xp_reward`: int (≥0) - XP reward
- `quest_giver`: str - Set to the NPC name passed in

---

## Implementation Steps

### Step 1: Add prompt template to ai_config.py

Add `DEFAULT_QUEST_GENERATION_PROMPT` constant after line 137, following the pattern of existing prompts:
```python
DEFAULT_QUEST_GENERATION_PROMPT = """Generate a quest for a {theme} RPG.
NPC Quest Giver: {npc_name}
Location: {location_name}
Player Level: {player_level}

Requirements:
1. Create a unique quest name (2-30 characters)
2. Write a quest description (1-200 characters)
3. Choose an appropriate objective type
4. Set target and target_count for the objective
5. Calculate balanced rewards for the player level

Objective types:
- kill: Defeat enemy type (target = enemy name, target_count = how many)
- collect: Gather items (target = item name, target_count = how many)
- explore: Visit location (target = location name, target_count = 1)
- talk: Speak to NPC (target = NPC name, target_count = 1)
- drop: Deliver item (target = item name, target_count = 1)

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Quest Name",
  "description": "A brief description of the quest objective.",
  "objective_type": "kill|collect|explore|talk|drop",
  "target": "target name",
  "target_count": <number>,
  "gold_reward": <number>,
  "xp_reward": <number>
}}

Rewards scaling guidelines (based on player level {player_level}):
- gold_reward: 30 + (player_level * 15) with some variance
- xp_reward: 25 + (player_level * 12) with some variance"""
```

Add field to `AIConfig` dataclass (after line 170):
```python
quest_generation_prompt: str = field(default=DEFAULT_QUEST_GENERATION_PROMPT)
```

Update `to_dict()` and `from_dict()` methods to include `quest_generation_prompt`.

### Step 2: Add generate_quest method to ai_service.py

**Location:** After `generate_lore()` method (around line 1092)

Add three methods:

1. `_build_quest_prompt(self, theme: str, npc_name: str, player_level: int, location_name: str = "") -> str`
   - Format the quest_generation_prompt template with provided context

2. `_parse_quest_response(self, response_text: str, npc_name: str) -> dict`
   - Parse JSON response
   - Validate name length (2-30 chars)
   - Validate description length (1-200 chars)
   - Validate objective_type is one of: "kill", "collect", "explore", "talk", "drop"
   - Validate target is non-empty string
   - Validate target_count >= 1
   - Validate gold_reward >= 0
   - Validate xp_reward >= 0
   - Add quest_giver = npc_name to result
   - Raise `AIGenerationError` on validation failure

3. `generate_quest(self, theme: str, npc_name: str, player_level: int, location_name: str = "") -> dict`
   - Build prompt using `_build_quest_prompt`
   - Check cache if enabled
   - Call `_call_llm()` with prompt
   - Parse response using `_parse_quest_response`
   - Store in cache
   - Return validated dict

### Step 3: Create test file tests/test_ai_quest_generation.py

**Test Categories:**

1. **Spec Tests** (unit tests with mocked OpenAI):
   - `test_generate_quest_returns_valid_structure` - Returns dict with all required fields
   - `test_generate_quest_validates_name_length_too_short` - Rejects names <2 chars
   - `test_generate_quest_validates_name_length_too_long` - Rejects names >30 chars
   - `test_generate_quest_validates_description_length_too_short` - Rejects descriptions <1 char
   - `test_generate_quest_validates_description_length_too_long` - Rejects descriptions >200 chars
   - `test_generate_quest_validates_objective_type` - Rejects invalid objective types
   - `test_generate_quest_validates_target_not_empty` - Rejects empty target
   - `test_generate_quest_validates_target_count_positive` - Rejects target_count < 1
   - `test_generate_quest_validates_rewards_non_negative` - Rejects negative rewards
   - `test_generate_quest_sets_quest_giver` - Sets quest_giver to npc_name
   - `test_generate_quest_uses_context` - Prompt includes theme, npc, location, level
   - `test_generate_quest_handles_api_error` - Raises AIServiceError on failure

2. **Integration Tests** (Quest model compatibility):
   - `test_generate_quest_can_create_valid_quest_instance` - Result can construct Quest model
   - `test_generate_quest_kill_objective_valid` - Kill quests have valid structure
   - `test_generate_quest_collect_objective_valid` - Collect quests have valid structure
   - `test_generate_quest_explore_objective_valid` - Explore quests have valid structure

Follow the test patterns in `tests/test_ai_item_generation.py` using:
- `@pytest.fixture` for basic_config and mock responses
- `@patch('cli_rpg.ai_service.OpenAI')` decorator
- `pytest.raises(AIGenerationError, match=...)` for validation errors

---

## Files to Modify

1. `src/cli_rpg/ai_config.py` - Add prompt template and config field
2. `src/cli_rpg/ai_service.py` - Add generate_quest(), _build_quest_prompt(), _parse_quest_response()
3. `tests/test_ai_quest_generation.py` (new file) - Comprehensive test coverage

---

## Verification

Run tests to verify implementation:
```bash
pytest tests/test_ai_quest_generation.py -v
pytest tests/test_ai_config.py -v
pytest --cov=src/cli_rpg -k "quest" --cov-report=term-missing
```
