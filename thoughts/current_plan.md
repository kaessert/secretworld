# Fix: Cleric Smite ImportError Bug

## Problem
`main.py:911` imports non-existent `get_combat_reaction` and calls it with wrong parameters, causing ImportError when Cleric defeats an enemy with smite.

## Fix
Replace the broken import and function call (lines 911-920) with the pattern used elsewhere in the file (lines 395-397, 558-560, etc.).

**File**: `src/cli_rpg/main.py`

**Change lines 911-920 from**:
```python
            from cli_rpg.companion_reactions import get_combat_reaction

            reaction = get_combat_reaction(
                companions=game_state.companions,
                command=command,
            )
            if reaction:
                companion_name, reaction_text = reaction
                from cli_rpg import colors
                output += f"\n\n{colors.npc(companion_name)}: \"{reaction_text}\""
```

**To**:
```python
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
```

Note: `process_companion_reactions` is already imported at line 16, so no new import is needed.

## Verification
1. Run existing tests: `pytest tests/test_cleric.py -v` (should pass)
2. Run full test suite: `pytest` (all 3403 tests should pass)
