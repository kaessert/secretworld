# Implementation Plan: NPC Dialogue Variety (Greeting Text)

## Summary
Add a `greetings` list to NPCs so talking to them shows varied, randomly-selected greeting text before functional UI (shop/quests), making interactions feel more immersive.

## Spec
- NPCs gain an optional `greetings: List[str]` field (default: empty list)
- When talking to an NPC:
  - If `greetings` is non-empty, display a random greeting from the list
  - Otherwise, fall back to existing `dialogue` field (backward compatible)
- Greeting appears first, then existing shop/quest prompts

## Tests (TDD)

### File: `tests/test_npc_greetings.py`

```python
import pytest
from cli_rpg.models.npc import NPC

class TestNPCGreetings:
    def test_npc_greetings_default_empty(self):
        """NPC greetings defaults to empty list."""
        npc = NPC(name="Guard", description="A guard", dialogue="Halt!")
        assert npc.greetings == []

    def test_npc_with_greetings(self):
        """NPC can be created with greetings list."""
        greetings = ["Hello!", "Welcome!", "Good day!"]
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hi", greetings=greetings)
        assert npc.greetings == greetings

    def test_npc_get_greeting_returns_from_list(self):
        """get_greeting returns a greeting from the list when available."""
        greetings = ["Hello!", "Welcome!"]
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hi", greetings=greetings)
        assert npc.get_greeting() in greetings

    def test_npc_get_greeting_falls_back_to_dialogue(self):
        """get_greeting returns dialogue when greetings is empty."""
        npc = NPC(name="Guard", description="A guard", dialogue="Move along.")
        assert npc.get_greeting() == "Move along."

    def test_npc_greetings_serialization(self):
        """Greetings are serialized to dict."""
        greetings = ["Hello!", "Welcome!"]
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hi", greetings=greetings)
        data = npc.to_dict()
        assert data["greetings"] == greetings

    def test_npc_greetings_deserialization(self):
        """Greetings are deserialized from dict."""
        data = {
            "name": "Merchant",
            "description": "A shopkeeper",
            "dialogue": "Hi",
            "greetings": ["Hello!", "Welcome!"],
            "is_merchant": False,
            "shop": None,
            "is_quest_giver": False,
            "offered_quests": []
        }
        npc = NPC.from_dict(data)
        assert npc.greetings == ["Hello!", "Welcome!"]

    def test_npc_greetings_deserialization_missing(self):
        """Missing greetings in dict defaults to empty list."""
        data = {
            "name": "Guard",
            "description": "A guard",
            "dialogue": "Halt!",
            "is_merchant": False,
            "shop": None
        }
        npc = NPC.from_dict(data)
        assert npc.greetings == []
```

### Test in `tests/test_shop_commands.py` (add to TestTalkCommand):

```python
def test_talk_uses_get_greeting(self, game_with_shop):
    """Talk command uses get_greeting() method for display."""
    # Uses existing dialogue when greetings empty
    cont, msg = handle_exploration_command(game_with_shop, "talk", ["merchant"])
    assert "Welcome to my shop!" in msg  # Falls back to dialogue
```

## Implementation Steps

### Step 1: Add `greetings` field and `get_greeting()` method to NPC model
**File**: `src/cli_rpg/models/npc.py`

```python
# Add import at top
import random

# Add field to NPC dataclass (after line 30):
greetings: List[str] = field(default_factory=list)

# Add method to NPC class (after __post_init__):
def get_greeting(self) -> str:
    """Get a greeting to display when talking to this NPC.

    Returns a random greeting from the greetings list if available,
    otherwise falls back to the dialogue field.
    """
    if self.greetings:
        return random.choice(self.greetings)
    return self.dialogue

# Update to_dict() to include greetings:
"greetings": self.greetings,

# Update from_dict() to parse greetings:
greetings=data.get("greetings", []),
```

### Step 2: Update talk command to use `get_greeting()`
**File**: `src/cli_rpg/main.py` (line 416)

Change:
```python
output = f"\n{npc.name}: \"{npc.dialogue}\""
```

To:
```python
output = f"\n{npc.name}: \"{npc.get_greeting()}\""
```

### Step 3: Update default world NPCs with sample greetings (optional enhancement)
**File**: `src/cli_rpg/world.py` (line 91-95)

Add greetings to the default Merchant NPC:
```python
greetings=[
    "Welcome, traveler! Take a look at my goods.",
    "Ah, a customer! What can I get for you today?",
    "Come in, come in! Best prices in town!",
]
```

## Verification
1. Run: `pytest tests/test_npc_greetings.py -v`
2. Run: `pytest tests/test_shop_commands.py::TestTalkCommand -v`
3. Run full suite: `pytest`
