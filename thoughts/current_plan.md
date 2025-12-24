# Fix: Misleading error message when using `talk` without arguments in NPC-less location

## Spec

When user types `talk` without arguments:
- **If location has NPCs**: Show "Talk to whom? Specify an NPC name."
- **If location has no NPCs**: Show "There are no NPCs here to talk to."

## Test (add to `tests/test_shop_commands.py`)

```python
def test_talk_no_args_no_npcs_in_location(self):
    """Talk command shows 'no NPCs here' when location has no NPCs."""
    # Create game with location that has no NPCs
    character = Character(name="Test", character_class="Warrior", strength=10, intelligence=10, agility=10)
    location = Location(name="Empty Cave", description="A dark cave.", connections={})
    game = GameState(current_character=character, current_location="Empty Cave", world={"Empty Cave": location})

    cont, msg = handle_exploration_command(game, "talk", [])
    assert cont is True
    assert "no npc" in msg.lower() or "no one" in msg.lower()
```

## Implementation

**File**: `src/cli_rpg/main.py`, line ~389-391

**Change the `talk` command handler from**:
```python
elif command == "talk":
    if not args:
        return (True, "\nTalk to whom? Specify an NPC name.")
```

**To**:
```python
elif command == "talk":
    if not args:
        location = game_state.world.get(game_state.current_location)
        if location is None or not location.npcs:
            return (True, "\nThere are no NPCs here to talk to.")
        return (True, "\nTalk to whom? Specify an NPC name.")
```

## Verification

```bash
pytest tests/test_shop_commands.py -v -k "talk"
```
