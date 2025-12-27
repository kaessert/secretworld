# Quest Difficulty UI/AI Integration Plan

## Spec

Complete the quest difficulty feature by wiring it up to UI displays and AI generation. The model layer is already complete (QuestDifficulty enum, difficulty/recommended_level fields, validation, serialization).

**Remaining work:**
1. Display difficulty in quest journal listing
2. Display difficulty in quest details view
3. Display difficulty when NPC offers quests
4. Update AI generation prompt to request difficulty/level
5. Parse difficulty fields from AI responses
6. Clone difficulty fields when player accepts quest

## Tests (tests/test_quest_difficulty_ui.py)

```python
class TestQuestDifficultyDisplay:
    # Journal shows difficulty indicator
    def test_journal_shows_difficulty_indicator()

    # Quest details shows difficulty and level
    def test_quest_details_shows_difficulty_and_level()

    # NPC quest list shows difficulty
    def test_npc_available_quests_shows_difficulty()

class TestQuestDifficultyClone:
    # Accept command copies difficulty fields
    def test_accept_copies_difficulty()
    def test_accept_copies_recommended_level()

class TestQuestDifficultyAIParsing:
    # AI response parsing handles difficulty
    def test_parse_quest_includes_difficulty()
    def test_parse_quest_includes_recommended_level()
    def test_parse_quest_defaults_difficulty_when_missing()
```

## Implementation Steps

### 1. Add difficulty display to quest journal (main.py ~line 1827)

Before:
```python
lines.append(f"  * {quest.name} [{quest.current_count}/{quest.target_count}]")
```

After:
```python
diff_icons = {"trivial": ".", "easy": "-", "normal": "~", "hard": "!", "deadly": "!!"}
diff_icon = diff_icons.get(quest.difficulty.value, "~")
lines.append(f"  {diff_icon} {quest.name} [{quest.current_count}/{quest.target_count}]")
```

### 2. Add difficulty to quest details (main.py ~line 1872)

After line with "Objective:":
```python
lines.append(f"Difficulty: {quest.difficulty.value.capitalize()} (Recommended: Lv.{quest.recommended_level})")
```

### 3. Add difficulty to NPC quest offers (main.py ~line 1350)

Before:
```python
output += f"\n  - {q.name}"
```

After:
```python
output += f"\n  - {q.name} [{q.difficulty.value.capitalize()}]"
```

### 4. Update quest generation prompt (ai_config.py ~line 182-191)

Add to JSON schema:
```json
"difficulty": "trivial|easy|normal|hard|deadly",
"recommended_level": <number 1-20>
```

Add difficulty guidelines after rewards section:
```
Difficulty mapping (based on region danger level):
- "low" danger -> trivial/easy difficulty, recommended_level 1-3
- "medium" danger -> easy/normal difficulty, recommended_level 3-7
- "high" danger -> normal/hard difficulty, recommended_level 7-12
- "deadly" danger -> hard/deadly difficulty, recommended_level 12+
```

### 5. Update _parse_quest_response (ai_service.py ~line 2055-2064)

Add to return dict:
```python
"difficulty": data.get("difficulty", "normal"),
"recommended_level": int(data.get("recommended_level", 1)),
```

### 6. Clone difficulty fields in accept (main.py ~line 1697)

Add before closing paren of Quest():
```python
difficulty=matching_quest.difficulty,
recommended_level=matching_quest.recommended_level,
```

## Files to Modify

1. `src/cli_rpg/main.py` - Display in journal, details, NPC offers; clone on accept
2. `src/cli_rpg/ai_config.py` - Update DEFAULT_QUEST_GENERATION_PROMPT
3. `src/cli_rpg/ai_service.py` - Parse difficulty/recommended_level in _parse_quest_response
4. `tests/test_quest_difficulty_ui.py` - New test file for UI/parsing tests
