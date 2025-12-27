# Implementation Plan: Issue 13 - NPC Character Arcs

## Overview
Add character arc progression for NPCs based on player interactions. NPCs evolve from strangers to allies/rivals based on cumulative interactions, with arc stage affecting dialogue, quests, and behavior.

## Key Design Decisions

1. **Arc stages mirror Companion bond levels** for consistency: STRANGER → ACQUAINTANCE → TRUSTED → DEVOTED (or STRANGER → WARY → HOSTILE → ENEMY for negative arcs)
2. **Track interaction history** with typed events (talked, helped_quest, failed_quest, intimidated, bribed, etc.)
3. **Integrate with existing NPC model** via optional `arc` field for backward compatibility
4. **Arc affects NPC behavior** via greeting selection, quest availability, price modifiers

## Spec

**NPCArcStage** enum:
- `STRANGER` (0-24 points): Default, minimal trust
- `ACQUAINTANCE` (25-49): Some familiarity, basic quests available
- `TRUSTED` (50-74): Real trust, personal quests available
- `DEVOTED` (75-100): Unbreakable bond, best prices/exclusive content

**NPCArcStage (Negative path)**:
- `WARY` (-1 to -24): Suspicious of player
- `HOSTILE` (-25 to -49): Actively unfriendly
- `ENEMY` (-50 to -100): Refuses interaction, may attack

**InteractionType** enum: `TALKED`, `HELPED_QUEST`, `FAILED_QUEST`, `INTIMIDATED`, `BRIBED`, `DEFENDED`, `ATTACKED`, `GIFTED`

**NPCArc** dataclass:
- `arc_points: int` (default 0, range -100 to 100)
- `interactions: List[NPCInteraction]` (history of events)
- `get_stage() -> NPCArcStage` (compute from points)
- `record_interaction(type, delta, desc)` (add points, log event)
- Serialization: `to_dict()` / `from_dict()`

## Tests (tests/test_npc_arc.py)

### TestNPCArcStage
1. `test_arc_stage_stranger_exists` - STRANGER enum exists with value "stranger"
2. `test_arc_stage_acquaintance_exists` - ACQUAINTANCE enum exists
3. `test_arc_stage_trusted_exists` - TRUSTED enum exists
4. `test_arc_stage_devoted_exists` - DEVOTED enum exists
5. `test_arc_stage_wary_exists` - WARY enum exists
6. `test_arc_stage_hostile_exists` - HOSTILE enum exists
7. `test_arc_stage_enemy_exists` - ENEMY enum exists

### TestInteractionType
8. `test_interaction_type_talked_exists` - TALKED enum exists
9. `test_interaction_type_helped_quest_exists` - HELPED_QUEST enum exists
10. `test_interaction_type_failed_quest_exists` - FAILED_QUEST enum exists
11. `test_interaction_type_intimidated_exists` - INTIMIDATED enum exists
12. `test_interaction_type_bribed_exists` - BRIBED enum exists
13. `test_interaction_type_defended_exists` - DEFENDED enum exists
14. `test_interaction_type_attacked_exists` - ATTACKED enum exists
15. `test_interaction_type_gifted_exists` - GIFTED enum exists

### TestNPCInteraction
16. `test_interaction_creation` - NPCInteraction stores type, delta, description, timestamp
17. `test_interaction_to_dict` - Serializes correctly
18. `test_interaction_from_dict` - Deserializes correctly

### TestNPCArc
19. `test_arc_default_values` - arc_points=0, interactions=[], stage=STRANGER
20. `test_arc_get_stage_stranger` - 0-24 points returns STRANGER
21. `test_arc_get_stage_acquaintance` - 25-49 points returns ACQUAINTANCE
22. `test_arc_get_stage_trusted` - 50-74 points returns TRUSTED
23. `test_arc_get_stage_devoted` - 75-100 points returns DEVOTED
24. `test_arc_get_stage_wary` - -1 to -24 returns WARY
25. `test_arc_get_stage_hostile` - -25 to -49 returns HOSTILE
26. `test_arc_get_stage_enemy` - -50 to -100 returns ENEMY
27. `test_arc_record_interaction_adds_points` - Points increase correctly
28. `test_arc_record_interaction_logs_event` - Interaction added to history
29. `test_arc_points_clamped_max` - Points capped at 100
30. `test_arc_points_clamped_min` - Points capped at -100
31. `test_arc_to_dict` - Serializes arc_points and interactions
32. `test_arc_from_dict` - Deserializes correctly
33. `test_arc_roundtrip` - Survives save/load cycle

### TestNPCIntegration
34. `test_npc_arc_field_optional` - NPC works without arc field
35. `test_npc_arc_serialization` - NPC with arc serializes correctly
36. `test_npc_arc_deserialization` - NPC with arc deserializes correctly
37. `test_npc_backward_compat` - Old saves without arc field load correctly

## Implementation Steps

### Step 1: Create npc_arc.py

**File**: `src/cli_rpg/models/npc_arc.py`

```python
"""NPC character arc model for tracking relationship progression with player."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class NPCArcStage(Enum):
    """Character arc stages based on accumulated interaction points."""
    # Positive stages (0 to 100)
    STRANGER = "stranger"        # 0-24: Default, no history
    ACQUAINTANCE = "acquaintance"  # 25-49: Some familiarity
    TRUSTED = "trusted"          # 50-74: Real trust established
    DEVOTED = "devoted"          # 75-100: Unbreakable bond
    # Negative stages (-1 to -100)
    WARY = "wary"                # -1 to -24: Suspicious
    HOSTILE = "hostile"          # -25 to -49: Actively unfriendly
    ENEMY = "enemy"              # -50 to -100: Refuses interaction


class InteractionType(Enum):
    """Types of player-NPC interactions that affect arc progression."""
    TALKED = "talked"              # +1-3 per conversation
    HELPED_QUEST = "helped_quest"  # +10-20 for completing their quest
    FAILED_QUEST = "failed_quest"  # -10-15 for failing their quest
    INTIMIDATED = "intimidated"    # -5-10 for intimidation
    BRIBED = "bribed"              # -2 to +5 depending on context
    DEFENDED = "defended"          # +15-25 for defending in combat
    ATTACKED = "attacked"          # -30-50 for attacking
    GIFTED = "gifted"              # +5-15 for giving gifts


@dataclass
class NPCInteraction:
    """A single recorded interaction between player and NPC."""
    interaction_type: InteractionType
    points_delta: int
    description: Optional[str] = None
    timestamp: int = 0  # Game hour when interaction occurred

    def to_dict(self) -> dict:
        return {
            "interaction_type": self.interaction_type.value,
            "points_delta": self.points_delta,
            "description": self.description,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCInteraction":
        return cls(
            interaction_type=InteractionType(data["interaction_type"]),
            points_delta=data["points_delta"],
            description=data.get("description"),
            timestamp=data.get("timestamp", 0),
        )


@dataclass
class NPCArc:
    """Tracks an NPC's relationship arc with the player."""
    arc_points: int = 0
    interactions: List[NPCInteraction] = field(default_factory=list)

    def get_stage(self) -> NPCArcStage:
        """Compute arc stage from current points."""
        if self.arc_points >= 75:
            return NPCArcStage.DEVOTED
        elif self.arc_points >= 50:
            return NPCArcStage.TRUSTED
        elif self.arc_points >= 25:
            return NPCArcStage.ACQUAINTANCE
        elif self.arc_points >= 0:
            return NPCArcStage.STRANGER
        elif self.arc_points >= -24:
            return NPCArcStage.WARY
        elif self.arc_points >= -49:
            return NPCArcStage.HOSTILE
        else:
            return NPCArcStage.ENEMY

    def record_interaction(
        self,
        interaction_type: InteractionType,
        points_delta: int,
        description: Optional[str] = None,
        timestamp: int = 0,
    ) -> Optional[str]:
        """Record an interaction and return message if stage changed."""
        old_stage = self.get_stage()

        self.arc_points = max(-100, min(100, self.arc_points + points_delta))

        self.interactions.append(NPCInteraction(
            interaction_type=interaction_type,
            points_delta=points_delta,
            description=description,
            timestamp=timestamp,
        ))
        # Cap interaction history at 20 entries
        while len(self.interactions) > 20:
            self.interactions.pop(0)

        new_stage = self.get_stage()
        if new_stage != old_stage:
            return f"Relationship changed: {old_stage.value} → {new_stage.value}"
        return None

    def to_dict(self) -> dict:
        return {
            "arc_points": self.arc_points,
            "interactions": [i.to_dict() for i in self.interactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCArc":
        return cls(
            arc_points=data.get("arc_points", 0),
            interactions=[
                NPCInteraction.from_dict(i) for i in data.get("interactions", [])
            ],
        )
```

### Step 2: Integrate into NPC model

**File**: `src/cli_rpg/models/npc.py`

Add import:
```python
from cli_rpg.models.npc_arc import NPCArc
```

Add field to NPC dataclass:
```python
arc: Optional[NPCArc] = None  # Character arc tracking (optional for backward compat)
```

Update `to_dict()`:
```python
result["arc"] = self.arc.to_dict() if self.arc else None
```

Update `from_dict()`:
```python
arc_data = data.get("arc")
arc = NPCArc.from_dict(arc_data) if arc_data else None
# ... add arc=arc to cls() call
```

### Step 3: Create tests

**File**: `tests/test_npc_arc.py`

Implement all 37 tests per spec above.

## Files Changed

1. **Create**: `src/cli_rpg/models/npc_arc.py` - NPCArcStage, InteractionType, NPCInteraction, NPCArc
2. **Create**: `tests/test_npc_arc.py` - 37 tests
3. **Modify**: `src/cli_rpg/models/npc.py` - Add optional `arc` field with serialization

## Future Integration Points (Not in this issue)

These are documented for future work but NOT implemented in Issue 13:

- `get_greeting()` could select dialogue based on arc stage
- Shops could apply price modifiers based on arc
- Quests could have arc stage prerequisites
- `talk` command could call `arc.record_interaction(TALKED, +2)`
