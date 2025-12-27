# Quest Difficulty Indicators Implementation Plan

## Spec

Add difficulty metadata to quests so players can gauge appropriateness before accepting:

1. **QuestDifficulty enum**: `TRIVIAL`, `EASY`, `NORMAL`, `HARD`, `DEADLY`
2. **Quest fields**: `difficulty: QuestDifficulty` (default NORMAL), `recommended_level: int` (default 1)
3. **Display**: Show difficulty and recommended level in quest listings and details
4. **AI Generation**: Include difficulty in generated quests based on region danger level

## Tests (tests/test_quest_difficulty.py)

```python
class TestQuestDifficultyEnum:
    # Enum values exist and serialize correctly
    def test_difficulty_enum_values()
    def test_difficulty_enum_serialization()

class TestQuestDifficultyFields:
    # Default values
    def test_difficulty_defaults_to_normal()
    def test_recommended_level_defaults_to_1()

    # Field assignment
    def test_quest_with_custom_difficulty()
    def test_quest_with_custom_recommended_level()

    # Validation
    def test_recommended_level_must_be_positive()

    # Serialization roundtrip
    def test_difficulty_serialization_roundtrip()
    def test_recommended_level_serialization_roundtrip()
```

## Implementation Steps

### 1. Add QuestDifficulty enum to models/quest.py (after ObjectiveType, ~line 27)

```python
class QuestDifficulty(Enum):
    """Difficulty rating for quests."""
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    DEADLY = "deadly"
```

### 2. Add fields to Quest dataclass in models/quest.py

After `completed_branch_id` field (~line 166):
```python
difficulty: QuestDifficulty = field(default=QuestDifficulty.NORMAL)
recommended_level: int = field(default=1)
```

### 3. Add validation in Quest.__post_init__ (~line 212)

```python
if self.recommended_level < 1:
    raise ValueError("recommended_level must be at least 1")
```

### 4. Update Quest.to_dict() (~line 275)

Add:
```python
"difficulty": self.difficulty.value,
"recommended_level": self.recommended_level,
```

### 5. Update Quest.from_dict() (~line 318)

Add:
```python
difficulty=QuestDifficulty(data.get("difficulty", "normal")),
recommended_level=data.get("recommended_level", 1),
```

### 6. Update quest display in main.py

**Quest journal listing** (~line 1827): Add difficulty indicator
```python
diff_icon = {"trivial": ".", "easy": "-", "normal": "~", "hard": "!", "deadly": "!!"}[quest.difficulty.value]
lines.append(f"  {diff_icon} {quest.name} [{quest.current_count}/{quest.target_count}]")
```

**Quest details** (~line 1873): Add difficulty/level display
```python
lines.append(f"Difficulty: {quest.difficulty.value.capitalize()} (Recommended: Lv.{quest.recommended_level})")
```

**Available quests from NPC** (~line 1350): Show difficulty
```python
output += f"\n  - {q.name} [{q.difficulty.value}]"
```

### 7. Update AI quest generation prompt in ai_config.py (~line 190)

Add to JSON schema:
```json
"difficulty": "trivial|easy|normal|hard|deadly",
"recommended_level": <number>
```

Add to guidelines:
```
Difficulty mapping (based on region danger_level):
- low danger -> trivial/easy, level 1-3
- medium danger -> normal, level 4-7
- high danger -> hard, level 8-12
- deadly danger -> deadly, level 13+
```

### 8. Update _parse_quest_response in ai_service.py

Add parsing for new fields (with defaults for backward compatibility).

### 9. Update quest cloning in main.py accept command (~line 1677)

Add to clone:
```python
difficulty=matching_quest.difficulty,
recommended_level=matching_quest.recommended_level,
```

## Files to Modify

1. `src/cli_rpg/models/quest.py` - Add enum, fields, validation, serialization
2. `src/cli_rpg/main.py` - Display difficulty in UI, clone new fields
3. `src/cli_rpg/ai_config.py` - Update quest generation prompt
4. `src/cli_rpg/ai_service.py` - Parse new fields from AI response
5. `tests/test_quest_difficulty.py` - New test file for difficulty features
