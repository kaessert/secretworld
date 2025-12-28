# Plan: Procedural Quest Generation with ContentLayer Integration

## Overview
Implement procedural quest generation using templates that ContentLayer can populate with AI content. This follows the same pattern as RoomTemplates for procedural interiors - procedural structure + AI content.

---

## Spec: Quest Template System

### Core Concept
**QuestTemplate** defines procedural quest structure (objective type, difficulty scaling, reward formula), while **ContentLayer** fills in narrative content (name, description, target names) via AI or fallback.

### New Types

```python
# src/cli_rpg/procedural_quests.py

class QuestTemplateType(Enum):
    """Quest template archetypes for procedural generation."""
    KILL_BOSS = "kill_boss"       # Kill a boss enemy
    KILL_MOBS = "kill_mobs"       # Kill X creatures
    COLLECT_ITEMS = "collect"     # Collect X items
    EXPLORE_AREA = "explore"      # Reach a specific location
    TALK_NPC = "talk"             # Talk to an NPC
    ESCORT = "escort"             # Escort NPC to destination
    FETCH = "fetch"               # Retrieve item from location

@dataclass
class QuestTemplate:
    """Blueprint for procedurally generated quests."""
    template_type: QuestTemplateType
    objective_type: ObjectiveType  # maps to existing Quest.objective_type
    base_target_count: int         # e.g., 5 for "kill 5 wolves"
    difficulty_scaling: float      # multiplier based on player level
    base_gold_reward: int
    base_xp_reward: int
    category_tags: list[str]       # e.g., ["dungeon", "cave"] for where this spawns
    chain_position: int = 0        # 0=standalone, 1+=chain position
```

### Difficulty Scaling Formula
```python
difficulty = QuestDifficulty based on:
- player_level * region_danger_level * template_scaling

target_count = base_target_count + (player_level // 3)
gold_reward = base_gold_reward * (1 + player_level * 0.1) * difficulty_multiplier
xp_reward = base_xp_reward * (1 + player_level * 0.15) * difficulty_multiplier
```

---

## Implementation Steps

### Phase 1: Core Template Infrastructure

**1. Create `src/cli_rpg/procedural_quests.py`**
- `QuestTemplateType` enum (7 types listed above)
- `QuestTemplate` dataclass with fields:
  - template_type, objective_type, base_target_count
  - difficulty_scaling, base_gold_reward, base_xp_reward
  - category_tags, chain_position
- `QUEST_TEMPLATES` dict mapping category → list[QuestTemplate]
  - dungeon: KILL_BOSS, EXPLORE_AREA, COLLECT_ITEMS
  - cave: KILL_MOBS, COLLECT_ITEMS, TALK_NPC (find lost miner)
  - ruins: EXPLORE_AREA, COLLECT_ITEMS, KILL_BOSS
  - temple: TALK_NPC, EXPLORE_AREA, ESCORT
  - town/village: FETCH, TALK_NPC, ESCORT
- `select_quest_template(category, seed)` - deterministic template selection
- `scale_quest_difficulty(template, player_level, danger_level)` - returns scaled values

**2. Create `src/cli_rpg/models/content_request.py` updates**
- Add `QuestTemplateContentRequest` dataclass:
  - template_type, category, player_level, npc_name
  - coordinates for cache keying
- Extends existing request/response pattern

### Phase 2: ContentLayer Integration

**3. Update `src/cli_rpg/content_layer.py`**
- Add `generate_quest_from_template()` method:
  - Takes QuestTemplate + context
  - Calls AIService for name/description/target OR uses FallbackContentProvider
  - Returns fully populated Quest object
- Pattern matches existing `generate_npc_content()` flow

**4. Update `src/cli_rpg/fallback_content.py`**
- Expand `QUEST_TEMPLATES` to cover all QuestTemplateType values
- Add target name pools per category:
  - `QUEST_TARGETS`: enemy names, item names, location names, NPC names
- Add `get_quest_from_template()` method that selects appropriate target

### Phase 3: Quest Chain Support

**5. Create quest chain templates**
- Add `QUEST_CHAINS` dict in `procedural_quests.py`:
  - chain_id → list of QuestTemplate with ascending chain_position
- Add `generate_quest_chain()` function:
  - Returns list of Quest with prerequisites set

**6. Update `QuestNetworkManager` integration**
- Add method to register procedurally generated chains
- Ensure chain_id and unlocks_quests are populated

### Phase 4: Game Integration

**7. Update NPC quest assignment**
- Modify quest giver NPC creation to use `generate_quest_from_template()`
- Pass location category and player level
- Fallback to existing `generate_quest()` if template generation fails

**8. Add spawn triggers**
- Quest NPCs spawn with templates appropriate to their location category
- Interior events can spawn quest-related encounters (tie into rival adventurers)

### Phase 5: Testing

**9. Unit tests: `tests/test_procedural_quests.py`**
- Test QuestTemplateType enum values
- Test QuestTemplate creation and validation
- Test `select_quest_template()` determinism
- Test `scale_quest_difficulty()` calculations
- Test QUEST_TEMPLATES coverage for all categories

**10. Integration tests: `tests/test_quest_template_content.py`**
- Test ContentLayer.generate_quest_from_template() with AI mock
- Test ContentLayer.generate_quest_from_template() fallback
- Test quest chain generation
- Test determinism with same seed

---

## Files to Create
- `src/cli_rpg/procedural_quests.py` (new)
- `tests/test_procedural_quests.py` (new)
- `tests/test_quest_template_content.py` (new)

## Files to Modify
- `src/cli_rpg/content_layer.py` - add generate_quest_from_template()
- `src/cli_rpg/fallback_content.py` - expand QUEST_TEMPLATES, add target pools
- `src/cli_rpg/models/content_request.py` - add QuestTemplateContentRequest

---

## Success Criteria
1. QuestTemplate provides deterministic quest structure from seed
2. ContentLayer populates templates with AI content (or fallback)
3. Difficulty scales with player level and region danger
4. Quest chains can be generated procedurally
5. All tests pass (target: 20+ new tests)
