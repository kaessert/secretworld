# Implementation Plan: Multiple NPCs per Location (Enhanced UX)

## Summary
The Location model already supports `npcs: List[NPC]`. This plan enhances UX and world generation to make better use of this capability.

## Spec
- When `talk` is called with no arguments at a location with 1 NPC, auto-start conversation
- When `talk` is called with no arguments at a location with 2+ NPCs, list available NPCs
- World generation adds multiple NPCs (2) to Town Square for testing the feature

## Tests

### File: `tests/test_multiple_npcs.py`

```python
"""Tests for multiple NPCs per location feature."""
import pytest
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.game_state import GameState
from cli_rpg.models.character import Character


class TestTalkCommandMultipleNPCs:
    """Test talk command with multiple NPCs."""

    def test_talk_no_args_single_npc_auto_starts(self):
        """talk with no args at single-NPC location starts conversation directly."""
        npc = NPC(name="Merchant", description="Sells goods", dialogue="Welcome!")
        location = Location(
            name="Town Square",
            description="A busy square.",
            npcs=[npc],
            coordinates=(0, 0)
        )
        character = Character(name="Hero", character_class="warrior")
        game_state = GameState(character, {"Town Square": location}, "Town Square")

        from cli_rpg.main import handle_exploration_command
        _, msg = handle_exploration_command(game_state, "talk", [])
        assert "Welcome!" in msg
        assert game_state.current_npc == npc

    def test_talk_no_args_multiple_npcs_lists_all(self):
        """talk with no args at multi-NPC location lists available NPCs."""
        npc1 = NPC(name="Merchant", description="Sells goods", dialogue="Hello!")
        npc2 = NPC(name="Guard", description="Watches gate", dialogue="Move along.")
        location = Location(
            name="Town Square",
            description="A busy square.",
            npcs=[npc1, npc2],
            coordinates=(0, 0)
        )
        character = Character(name="Hero", character_class="warrior")
        game_state = GameState(character, {"Town Square": location}, "Town Square")

        from cli_rpg.main import handle_exploration_command
        _, msg = handle_exploration_command(game_state, "talk", [])
        assert "Merchant" in msg
        assert "Guard" in msg
        assert game_state.current_npc is None  # No conversation started

    def test_talk_with_name_selects_specific_npc(self):
        """talk <name> talks to the named NPC among multiple."""
        npc1 = NPC(name="Merchant", description="Sells goods", dialogue="Buy something!")
        npc2 = NPC(name="Guard", description="Watches gate", dialogue="Move along.")
        location = Location(
            name="Town Square",
            description="A busy square.",
            npcs=[npc1, npc2],
            coordinates=(0, 0)
        )
        character = Character(name="Hero", character_class="warrior")
        game_state = GameState(character, {"Town Square": location}, "Town Square")

        from cli_rpg.main import handle_exploration_command
        _, msg = handle_exploration_command(game_state, "talk", ["Guard"])
        assert "Move along." in msg
        assert game_state.current_npc == npc2
```

## Implementation Steps

### 1. Update `talk` command in `src/cli_rpg/main.py` (lines 505-515)

**Current code:**
```python
elif command == "talk":
    if not args:
        location = game_state.world.get(game_state.current_location)
        if location is None or not location.npcs:
            return (True, "\nThere are no NPCs here to talk to.")
        return (True, "\nTalk to whom? Specify an NPC name.")
    npc_name = " ".join(args)
    location = game_state.world.get(game_state.current_location)
    npc = location.find_npc_by_name(npc_name) if location else None
```

**New code:**
```python
elif command == "talk":
    location = game_state.world.get(game_state.current_location)
    if location is None or not location.npcs:
        return (True, "\nThere are no NPCs here to talk to.")

    if not args:
        if len(location.npcs) == 1:
            # Auto-select the single NPC
            npc = location.npcs[0]
        else:
            # Multiple NPCs - list them
            npc_names = [n.name for n in location.npcs]
            return (True, f"\nTalk to whom? Available: {', '.join(npc_names)}")
    else:
        npc_name = " ".join(args)
        npc = location.find_npc_by_name(npc_name)
        if npc is None:
            return (True, f"\nYou don't see '{npc_name}' here.")
```

### 2. Add Guard NPC to default world in `src/cli_rpg/world.py` (after line 104)

```python
# Create Guard NPC for Town Square
guard = NPC(
    name="Guard",
    description="A vigilant town guard keeping watch over the square",
    dialogue="Stay out of trouble, adventurer.",
    greetings=[
        "Stay out of trouble, adventurer.",
        "The roads have been dangerous lately.",
        "Keep your weapons sheathed in town.",
    ]
)
town_square.npcs.append(guard)
```

### 3. Add quest-giver NPC to AI world in `src/cli_rpg/ai_world.py` (after line 122)

```python
# Add quest giver NPC to starting location
quest_giver = NPC(
    name="Town Elder",
    description="A wise figure who knows of many adventures",
    dialogue="Ah, a new adventurer! I may have tasks for you.",
    is_quest_giver=True,
    offered_quests=[]
)
starting_location.npcs.append(quest_giver)
```

## Verification
```bash
pytest tests/test_multiple_npcs.py -v
pytest tests/test_world.py tests/test_location.py -v
```

## Files Modified
1. `src/cli_rpg/main.py` - Update talk command logic
2. `src/cli_rpg/world.py` - Add Guard NPC to default world
3. `src/cli_rpg/ai_world.py` - Add quest-giver NPC
4. `tests/test_multiple_npcs.py` - New test file (create)
