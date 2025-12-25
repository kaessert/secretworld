# Implementation Plan: NPC Echo Consequences MVP

## Feature Spec

**Goal**: NPCs reference tracked player choices when greeting the player, making past decisions matter.

**MVP Scope**: NPC greetings vary based on combat flee history. If a player has fled from enemies multiple times, some NPCs may comment on their "cautious reputation."

**Behavior**:
1. When `get_greeting()` is called, check the game's choice history
2. If player has 3+ `combat_flee` choices, return a reputation-aware greeting variant
3. The NPC must have access to game state's choices to make this determination
4. Fallback to normal greeting behavior if no significant reputation exists

**Design Decision**: Pass choice history to `get_greeting()` rather than modifying NPC to store game_state reference (cleaner, more testable).

---

## Tests First (TDD)

### File: `tests/test_npc_consequences.py`

```python
"""Tests for NPC consequence system - NPCs react to player choices."""
```

**Test 1**: `test_get_greeting_acknowledges_flee_reputation`
- Create NPC with standard greetings
- Pass choices list with 3+ `combat_flee` entries to `get_greeting()`
- Assert greeting contains reputation reference (e.g., "cautious" or "run")

**Test 2**: `test_get_greeting_normal_when_few_flees`
- Create NPC with greetings
- Pass choices list with <3 `combat_flee` entries
- Assert normal greeting returned (no reputation comment)

**Test 3**: `test_get_greeting_normal_when_no_choices`
- Create NPC with greetings
- Pass empty choices list or None
- Assert normal greeting returned

**Test 4**: `test_reputation_greeting_serializes_correctly`
- Verify NPC serialization still works (no regression)

---

## Implementation Steps

### Step 1: Update `NPC.get_greeting()` signature

**File**: `src/cli_rpg/models/npc.py`

Modify `get_greeting()` to accept optional `choices` parameter:

```python
def get_greeting(self, choices: list[dict] | None = None) -> str:
    """Get a greeting, optionally modified by player reputation."""
    # Check for reputation-based greetings first
    if choices:
        flee_count = sum(1 for c in choices if c.get("choice_type") == "combat_flee")
        if flee_count >= 3:
            return self._get_reputation_greeting("cautious")

    # Normal greeting logic
    if self.greetings:
        return random.choice(self.greetings)
    return self.dialogue
```

### Step 2: Add `_get_reputation_greeting()` helper

**File**: `src/cli_rpg/models/npc.py`

```python
def _get_reputation_greeting(self, reputation_type: str) -> str:
    """Get greeting based on player reputation."""
    templates = {
        "cautious": [
            "Ah, I've heard of you... one who knows when to run. Smart.",
            "Word travels fast. They say you're... careful. I respect that.",
            "A survivor, they call you. Some might say coward, but you're alive.",
        ]
    }
    options = templates.get(reputation_type, [])
    if options:
        return random.choice(options)
    return self.get_greeting(choices=None)  # Fallback to normal
```

### Step 3: Pass choices in `main.py` talk command

**File**: `src/cli_rpg/main.py` (around line 603)

Update the `talk` command to pass choices:

```python
# Current:
output += f"\n{npc.name}: \"{npc.get_greeting()}\""

# Change to:
output += f"\n{npc.name}: \"{npc.get_greeting(choices=game_state.choices)}\""
```

### Step 4: Update existing test mocks (if needed)

**File**: `tests/test_npc.py`

Verify `test_get_greeting_with_greetings_list` and `test_get_greeting_without_greetings_list` still pass (signature is backward compatible due to default `None`).

---

## Verification

1. Run `pytest tests/test_npc_consequences.py -v` - new tests pass
2. Run `pytest tests/test_npc.py -v` - existing tests still pass
3. Run `pytest tests/test_choices.py -v` - choice foundation tests still pass
4. Run full suite `pytest` - all 1885+ tests pass
