# Plan: Integrate AI-Generated Quests into NPC Interactions

## Spec
When a player talks to a quest-giver NPC who has no available quests (either no `offered_quests` or all already accepted), dynamically generate a quest using `AIService.generate_quest()` and add it to the NPC's `offered_quests` list.

**Behavior:**
- If `game_state.ai_service` is available AND NPC is a quest-giver AND has no unaccepted quests, generate one
- Follow the existing pattern from NPC dialogue generation (lines 416-429 in main.py)
- Silent fallback on AI failure (don't break the conversation)
- Generated quest is added to `npc.offered_quests` for persistence

---

## Tests (new file: tests/test_main_ai_quest_integration.py)

1. **test_talk_quest_giver_no_quests_generates_ai_quest** - When AI available, quest-giver with empty `offered_quests` gets a generated quest added
2. **test_talk_quest_giver_all_quests_accepted_generates_new** - Quest-giver whose quests are all accepted by player gets new quest generated
3. **test_talk_quest_giver_ai_unavailable_no_error** - Without AI service, no quest generation occurs (graceful skip)
4. **test_talk_quest_giver_ai_failure_silent_fallback** - AI exception doesn't break talk command
5. **test_generated_quest_appears_in_available_quests_output** - Generated quest shows in "Available Quests:" output

---

## Implementation

### File: `src/cli_rpg/main.py`

**Location:** Insert after line 434 (end of merchant/shop block), before line 436 (turn-in check).

```python
# Generate AI quest if NPC is quest-giver with no available quests
if npc.is_quest_giver and game_state.ai_service:
    available_quests = [
        q for q in npc.offered_quests
        if not game_state.current_character.has_quest(q.name)
    ]
    if not available_quests:
        try:
            from cli_rpg.models.quest import Quest, ObjectiveType
            quest_data = game_state.ai_service.generate_quest(
                theme=game_state.theme,
                npc_name=npc.name,
                player_level=game_state.current_character.level,
                location_name=game_state.current_location
            )
            new_quest = Quest(
                name=quest_data["name"],
                description=quest_data["description"],
                objective_type=ObjectiveType(quest_data["objective_type"]),
                target=quest_data["target"],
                target_count=quest_data["target_count"],
                gold_reward=quest_data["gold_reward"],
                xp_reward=quest_data["xp_reward"],
                quest_giver=quest_data["quest_giver"]
            )
            npc.offered_quests.append(new_quest)
        except Exception:
            pass  # Silent fallback - NPC just has no new quests
```

---

## Verification

```bash
pytest tests/test_main_ai_quest_integration.py -v
pytest tests/test_ai_quest_generation.py -v  # Existing tests still pass
```
