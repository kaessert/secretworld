# Implementation Plan: AI Agent Player for Long-Running Simulation Test Suite

## Overview

Create a heuristic-based Python agent that plays CLI-RPG autonomously via `--json` mode, making contextual decisions based on game state. This is the "missing piece" for the simulation test suite per ISSUES.md.

## Spec

The agent must:
1. Parse JSON Lines output from `cli-rpg --json --skip-character-creation --seed=N`
2. Track game state (HP, gold, dread, location, combat status, inventory, quests)
3. Make contextual decisions using priority-based heuristics
4. Run for configurable duration (command count or time limit)
5. Report session statistics (locations visited, enemies defeated, deaths, etc.)

## Decision Heuristics (Priority Order)

### In Combat:
1. **Flee** if HP < 25% max health
2. **Use potion** if HP < 50% and has healing item
3. **Attack** otherwise

### Out of Combat:
1. **Rest** if HP < 50% or dread > 60%
2. **Use potion** if HP < 30% and has healing item
3. **Buy potion** if at shop, gold > 50, no potion in inventory
4. **Accept quest** if NPC offers quest (opportunistic)
5. **Complete quest** if quest ready to turn in
6. **Explore** - move to random available exit

## File Structure

```
scripts/
├── __init__.py
├── ai_agent.py          # Main agent implementation
├── state_parser.py      # JSON output parsing utilities
└── run_simulation.py    # Entry point with CLI args
tests/
└── test_ai_agent.py     # Agent unit tests
```

## Implementation Steps

### 1. Create `scripts/` directory structure
- Create `scripts/__init__.py`
- Create `scripts/state_parser.py` with JSON parsing utilities

### 2. Create state parser (`scripts/state_parser.py`)
Parse JSON Lines output types:
- `state`: location, health, max_health, gold, level
- `actions`: exits, npcs, commands
- `combat`: enemy, enemy_health, player_health
- `narrative`: text (for quest/event detection)
- `error`: code, message
- `dump_state`: full game state snapshot

### 3. Create agent core (`scripts/ai_agent.py`)
Classes:
- `AgentState`: Tracks parsed game state
- `Agent`: Decision engine with heuristic methods
- `GameSession`: Subprocess management and I/O

### 4. Create CLI runner (`scripts/run_simulation.py`)
Args:
- `--seed`: RNG seed (default: random)
- `--max-commands`: Command limit (default: 1000)
- `--timeout`: Session timeout in seconds (default: 300)
- `--output`: JSON report file path
- `--verbose`: Print agent decisions

### 5. Create tests (`tests/test_ai_agent.py`)
Test cases:
- State parser correctly handles all JSON message types
- Agent flees when HP critical
- Agent uses potions when available and HP low
- Agent explores when healthy
- Agent rests when dread high
- Session runs without crash for 100 commands

## Key Implementation Details

### JSON Message Parsing
```python
def parse_line(line: str) -> dict:
    """Parse single JSON line from game output."""
    return json.loads(line)

def update_state(state: AgentState, message: dict) -> None:
    """Update agent state from parsed message."""
    msg_type = message.get("type")
    if msg_type == "state":
        state.location = message["location"]
        state.health = message["health"]
        state.max_health = message["max_health"]
        state.gold = message["gold"]
        state.level = message["level"]
    elif msg_type == "combat":
        state.in_combat = True
        state.enemy = message["enemy"]
        state.enemy_health = message["enemy_health"]
    elif msg_type == "actions":
        state.exits = message["exits"]
        state.npcs = message["npcs"]
        state.in_combat = "attack" in message["commands"]
```

### Decision Engine
```python
def decide(self, state: AgentState) -> str:
    """Return next command based on current state."""
    if state.in_combat:
        return self._combat_decision(state)
    return self._explore_decision(state)

def _combat_decision(self, state: AgentState) -> str:
    hp_pct = state.health / state.max_health
    if hp_pct < 0.25:
        return "flee"
    if hp_pct < 0.5 and state.has_potion():
        return f"use {state.get_potion_name()}"
    return "attack"
```

### Session Management
```python
def run_session(seed: int, max_commands: int) -> SessionReport:
    proc = subprocess.Popen(
        ["cli-rpg", "--json", "--skip-character-creation", f"--seed={seed}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    # Read initial state
    # Loop: parse output -> decide -> send command
    # Collect statistics
```

## Test Plan

1. **Unit tests for state parser**
   - Parse each JSON message type correctly
   - Handle malformed input gracefully

2. **Unit tests for decision engine**
   - Flee at low HP
   - Attack when healthy in combat
   - Rest when dread high
   - Explore when healthy and not in combat

3. **Integration test**
   - Run 100-command session with fixed seed
   - Verify no crashes
   - Verify reasonable behavior (some exploration, some combat)

## Success Criteria

- Agent runs 1000+ commands without crashing
- Agent makes reasonable decisions (survives longer than random)
- Session statistics are collected and reportable
- Tests pass for core functionality
