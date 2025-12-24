# Implementation Plan: Quest Acquisition from NPCs

## Spec

Allow players to acquire quests by talking to NPCs. When talking to an NPC that offers quests:
1. Show available quests after NPC dialogue
2. Provide `accept <quest>` command to acquire a quest from the current NPC
3. Quest moves from NPC's `offered_quests` to Character's `quests` with ACTIVE status
4. Persist NPC quest state (which quests have been accepted)

## Implementation Steps

### 1. Extend NPC Model (`src/cli_rpg/models/npc.py`)

Add quest-giver capability (parallel to merchant pattern):
```python
is_quest_giver: bool = False
offered_quests: List["Quest"] = field(default_factory=list)
```

Update `to_dict()` and `from_dict()` to serialize `offered_quests`.

### 2. Add Character Quest Helper (`src/cli_rpg/models/character.py`)

Add method to check if character already has a quest:
```python
def has_quest(self, quest_name: str) -> bool:
    return any(q.name.lower() == quest_name.lower() for q in self.quests)
```

### 3. Update Talk Command (`src/cli_rpg/main.py`, ~line 400)

After showing dialogue and shop info, also show available quests:
```python
if npc.is_quest_giver and npc.offered_quests:
    available = [q for q in npc.offered_quests
                 if not game_state.current_character.has_quest(q.name)]
    if available:
        output += "\n\nAvailable Quests:"
        for q in available:
            output += f"\n  • {q.name}"
        output += "\n\nType 'accept <quest>' to accept a quest."
```

Store current NPC in game_state for accept command context.

### 4. Add GameState NPC Context (`src/cli_rpg/game_state.py`)

Add field to track current NPC being talked to:
```python
current_npc: Optional[NPC] = None
```

### 5. Add Accept Command (`src/cli_rpg/main.py`)

New command handler:
```python
elif command == "accept":
    if game_state.current_npc is None:
        return (True, "\nYou need to talk to an NPC first.")
    if not args:
        return (True, "\nAccept what? Specify a quest name.")
    quest_name = " ".join(args)
    # Find quest in NPC's offered_quests
    # Check character doesn't already have it
    # Clone quest, set status to ACTIVE, add to character.quests
    # Return success message
```

### 6. Write Tests (`tests/test_npc_quests.py`)

New test file covering:
- NPC with `is_quest_giver=True` and `offered_quests`
- NPC serialization/deserialization with quests
- Talk command shows available quests
- Accept command adds quest to character
- Accept command rejects already-acquired quests
- Accept command requires NPC context

### 7. Update Existing NPC Tests (`tests/test_npc.py`)

Add tests for new fields default values and validation.

## File Changes Summary

| File | Change |
|------|--------|
| `src/cli_rpg/models/npc.py` | Add `is_quest_giver`, `offered_quests`, update serialization |
| `src/cli_rpg/models/character.py` | Add `has_quest()` method |
| `src/cli_rpg/game_state.py` | Add `current_npc` field |
| `src/cli_rpg/main.py` | Update talk command, add accept command |
| `tests/test_npc_quests.py` | New test file for NPC quest acquisition |
| `tests/test_npc.py` | Add tests for new default fields |
