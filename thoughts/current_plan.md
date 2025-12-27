# Plan: Auto-accept single quest when typing bare "accept"

## Spec
When a player types "accept" without arguments while talking to an NPC with exactly one available quest (that the player doesn't already have), auto-accept that quest instead of showing an error.

**Behavior:**
- If NPC has exactly 1 available quest → auto-accept it
- If NPC has 0 available quests → show "X doesn't offer any quests."
- If NPC has 2+ available quests → show "Accept what? Available: Quest1, Quest2" (list quest names)

## Test (update existing test in tests/test_npc_quests.py)

Update `test_accept_requires_quest_name` to test new behavior:

1. **test_accept_auto_accepts_single_quest**: NPC with 1 quest, bare "accept" → quest accepted
2. **test_accept_lists_quests_when_multiple**: NPC with 2+ quests, bare "accept" → shows available quest names
3. **test_accept_no_quests_shows_none**: NPC is not quest giver, bare "accept" → shows "doesn't offer any quests"

## Implementation (src/cli_rpg/main.py, lines 1590-1591)

Replace the current `if not args` block:
```python
if not args:
    return (True, "\nAccept what? Specify a quest name.")
```

With logic that:
1. Gets available quests (filter out quests player already has)
2. If exactly 1 available quest → set `args = [quest.name]` and continue to accept flow
3. If 0 available quests → return "doesn't offer any quests"
4. If 2+ available quests → return "Accept what? Available: Quest1, Quest2, ..."
