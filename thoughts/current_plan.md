# Implementation Plan: Add "Aggressive" Reputation Type

## Spec

Add a new "aggressive" reputation type that NPCs recognize when players kill enemies frequently (10+ kills). This extends the existing reputation system that currently only tracks "cautious" (fleeing 3+ times).

**Trigger**: Player has 10+ `combat_kill` choices recorded
**Effect**: NPCs acknowledge the player's violent tendencies with unique greetings
**Priority**: Cautious (flee) checked before Aggressive (kill), so chronic fleers are recognized as cowards even if they also kill a lot

---

## Tests (tests/test_npc.py)

Add after existing reputation tests around line 138:

```python
def test_get_greeting_aggressive_reputation(self):
    """get_greeting() returns aggressive greeting when player has 10+ kills."""
    npc = NPC(name="Guard", description="A town guard", dialogue="Hello")
    choices = [{"choice_type": "combat_kill"} for _ in range(10)]
    with patch("cli_rpg.models.npc.random.choice") as mock_choice:
        mock_choice.return_value = "I've heard tales of your... efficiency in combat."
        result = npc.get_greeting(choices=choices)
        # Should call _get_reputation_greeting which uses random.choice on templates
        assert "efficiency" in result or mock_choice.called

def test_get_greeting_no_aggressive_below_threshold(self):
    """get_greeting() returns normal greeting when kills < 10."""
    npc = NPC(name="Guard", description="A town guard", dialogue="Hello")
    choices = [{"choice_type": "combat_kill"} for _ in range(9)]
    result = npc.get_greeting(choices=choices)
    assert result == "Hello"  # Falls back to dialogue

def test_get_greeting_cautious_priority_over_aggressive(self):
    """cautious reputation (flee) takes priority over aggressive (kill)."""
    npc = NPC(name="Guard", description="A town guard", dialogue="Hello")
    choices = (
        [{"choice_type": "combat_flee"} for _ in range(3)] +
        [{"choice_type": "combat_kill"} for _ in range(10)]
    )
    with patch("cli_rpg.models.npc.random.choice") as mock_choice:
        mock_choice.return_value = "Word travels fast. They say you're... careful."
        result = npc.get_greeting(choices=choices)
        # Should get cautious greeting (flee checked first)
        assert "careful" in result.lower() or "run" in result.lower() or "coward" in result.lower() or "survivor" in result.lower()
```

---

## Implementation Steps

### Step 1: Add aggressive templates to NPC._get_reputation_greeting()

**File**: `src/cli_rpg/models/npc.py` (line ~78)

Add "aggressive" key to templates dict:

```python
templates = {
    "cautious": [
        "Ah, I've heard of you... one who knows when to run. Smart.",
        "Word travels fast. They say you're... careful. I respect that.",
        "A survivor, they call you. Some might say coward, but you're alive.",
    ],
    "aggressive": [
        "I've heard tales of your... efficiency in combat. Many have fallen.",
        "The blood of your enemies precedes you. What brings such a warrior here?",
        "A killer walks among us. I hope we remain on friendly terms.",
    ]
}
```

### Step 2: Add aggressive check in NPC.get_greeting()

**File**: `src/cli_rpg/models/npc.py` (line ~62, after cautious check)

```python
# Check for aggressive reputation (10+ kills)
kill_count = sum(1 for c in choices if c.get("choice_type") == "combat_kill")
if kill_count >= 10:
    return self._get_reputation_greeting("aggressive")
```

### Step 3: Record kills as choices in main.py

**File**: `src/cli_rpg/main.py`

**Location 1** (~line 254, after attack victory):
```python
# After: quest_messages = game_state.current_character.record_kill(enemy.name)
# Add:
game_state.record_choice(
    choice_type="combat_kill",
    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
    description=f"Killed {enemy.name}",
    target=enemy.name
)
```

**Location 2** (~line 344, after cast victory):
```python
# Same addition after record_kill call
game_state.record_choice(
    choice_type="combat_kill",
    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
    description=f"Killed {enemy.name}",
    target=enemy.name
)
```

---

## Verification

```bash
pytest tests/test_npc.py -v
pytest tests/test_game_state.py -v
pytest --cov=src/cli_rpg
```
