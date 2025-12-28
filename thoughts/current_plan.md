# NPC Arc Integration with Talk Command

## Spec
Integrate NPC character arcs into the `talk` command so dialogue interactions record `TALKED` interactions and modify arc points (1-3 per conversation). This enables relationship progression over time, with visual feedback when arc stage changes.

## Tests (TDD)
Create `tests/test_talk_arc_integration.py`:
1. `test_talk_initializes_npc_arc_if_none`: NPCs without arc get one created on first talk
2. `test_talk_records_talked_interaction`: Talking adds TALKED interaction to arc history
3. `test_talk_adds_arc_points`: Talking increases arc_points by 1-3
4. `test_talk_uses_game_time_timestamp`: Interaction timestamp is game_state.game_time.total_hours
5. `test_talk_displays_stage_change_message`: When arc crosses threshold, output includes stage change message
6. `test_arc_persists_across_multiple_talks`: Repeated talks accumulate points
7. `test_arc_stage_affects_greeting`: Arc stage modifies NPC greeting (TRUSTED/DEVOTED get warmer greetings)

## Implementation

### 1. Update NPC greeting logic in `src/cli_rpg/models/npc.py`
Add arc-aware greeting method:
```python
def get_arc_greeting_modifier(self) -> Optional[str]:
    """Get greeting modifier based on arc stage."""
    if self.arc is None:
        return None
    stage = self.arc.get_stage()
    if stage == NPCArcStage.DEVOTED:
        return "Ah, my dear friend! It's always a pleasure to see you."
    elif stage == NPCArcStage.TRUSTED:
        return "Good to see you again! What can I do for you today?"
    elif stage == NPCArcStage.ACQUAINTANCE:
        return "Oh, you again. What do you need?"
    # STRANGER and negative stages use default greeting
    return None
```

### 2. Update talk command handler in `src/cli_rpg/main.py` (~line 1285)
After greeting is displayed, before quest tracking:
```python
import random
from cli_rpg.models.npc_arc import NPCArc, InteractionType

# Initialize NPC arc if not present
if npc.arc is None:
    npc.arc = NPCArc()

# Record TALKED interaction (+1 to +3 points)
points_delta = random.randint(1, 3)
stage_change_msg = npc.arc.record_interaction(
    interaction_type=InteractionType.TALKED,
    points_delta=points_delta,
    description=f"Conversation at {game_state.current_location}",
    timestamp=game_state.game_time.total_hours,
)
if stage_change_msg:
    output += f"\n\n{colors.highlight(stage_change_msg)}"
```

### 3. Integrate arc greeting into get_greeting() in `src/cli_rpg/models/npc.py`
Modify `get_greeting()` to check arc stage before other reputation modifiers:
```python
def get_greeting(self, choices=None, quest_outcomes=None) -> str:
    # Check arc-based greeting first (warmest greetings for high relationship)
    arc_greeting = self.get_arc_greeting_modifier()
    if arc_greeting:
        return arc_greeting
    # ... rest of existing logic
```

## Verification
```bash
pytest tests/test_talk_arc_integration.py -v
pytest tests/test_npc_arc.py -v  # Ensure no regressions
pytest tests/test_npc.py -v  # Ensure NPC model still works
```
