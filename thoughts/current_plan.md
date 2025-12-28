# Branching Quest Paths Implementation Plan

## Overview
Complete the branching quest system by: (1) fixing quest accept to clone branches, (2) adding branch display in quest details, (3) integrating branch generation into procedural quests, and (4) adding branch templates for fallback content.

## Current State
- `QuestBranch` model exists with full serialization support
- `Character.record_kill/record_talk` already check branches and set `completed_branch_id`
- `Character.claim_quest_rewards` applies branch modifiers (gold_modifier, xp_modifier, faction_effects)
- Tests exist in `tests/test_quest_branching.py` and pass

## Gaps to Fill
1. Quest accept doesn't copy `alternative_branches` or `world_effects`
2. Quest details command doesn't show branch options
3. Procedural quest system doesn't generate branches
4. No fallback branch templates exist

## Implementation Steps

### 1. Fix Quest Accept to Clone Branches
**File**: `src/cli_rpg/main.py` (lines 1753-1777)

Add to quest clone:
```python
alternative_branches=[
    QuestBranch(
        id=b.id,
        name=b.name,
        objective_type=b.objective_type,
        target=b.target,
        target_count=b.target_count,
        current_count=0,
        description=b.description,
        faction_effects=b.faction_effects.copy(),
        gold_modifier=b.gold_modifier,
        xp_modifier=b.xp_modifier,
    )
    for b in matching_quest.alternative_branches
],
world_effects=[
    WorldEffect(
        effect_type=e.effect_type,
        target=e.target,
        description=e.description,
        metadata=e.metadata.copy(),
    )
    for e in matching_quest.world_effects
],
```

### 2. Add Branch Display to Quest Details Command
**File**: `src/cli_rpg/main.py` (after line 1990)

After showing progress, add:
```python
# Show alternative branches if quest has them
if quest.alternative_branches:
    lines.append("")
    lines.append("Alternative Paths:")
    for branch_info in quest.get_branches_display():
        status = "✓" if branch_info["is_complete"] else " "
        lines.append(f"  [{status}] {branch_info['name']}")
        lines.append(f"      {branch_info['objective']} {branch_info['progress']}")
```

### 3. Add Branch Templates to Procedural Quests
**File**: `src/cli_rpg/procedural_quests.py`

Add `BranchTemplate` dataclass:
```python
@dataclass
class BranchTemplate:
    """Template for an alternative quest branch."""
    id: str
    objective_type: ObjectiveType
    gold_modifier: float = 1.0
    xp_modifier: float = 1.0
    faction_effects: dict[str, int] = field(default_factory=dict)
```

Add `BRANCHING_QUEST_TEMPLATES` mapping template types to branch sets:
```python
BRANCHING_QUEST_TEMPLATES: dict[QuestTemplateType, list[list[BranchTemplate]]] = {
    QuestTemplateType.KILL_BOSS: [
        [
            BranchTemplate(id="kill", objective_type=ObjectiveType.KILL),
            BranchTemplate(id="persuade", objective_type=ObjectiveType.TALK,
                          gold_modifier=0.5, xp_modifier=1.5),
        ],
    ],
    # ... more types
}
```

Add `generate_branches_for_template()` function.

### 4. Add Fallback Branch Content
**File**: `src/cli_rpg/fallback_content.py`

Add `BRANCH_NAME_TEMPLATES` and `BRANCH_DESCRIPTION_TEMPLATES`:
```python
BRANCH_NAME_TEMPLATES: dict[str, dict[str, str]] = {
    "kill_boss": {
        "kill": "Eliminate {target}",
        "persuade": "Convince {target}",
        "betray": "Join {target}",
    },
    # ... more template types
}
```

Add `FallbackContentProvider.get_branch_content()` method.

### 5. Integrate into ContentLayer
**File**: `src/cli_rpg/content_layer.py`

Update `generate_quest_from_template()` to:
1. Check if template type has branching options
2. Generate branches with AI or fallback content
3. Attach branches to created Quest

### 6. Write Tests
**File**: `tests/test_branching_quests_integration.py` (new)

- Test quest accept clones branches correctly
- Test quest details shows branch options
- Test procedural quest generation creates branches
- Test branch completion via record_kill/record_talk
- Test branch rewards applied correctly

## Key Files
- `src/cli_rpg/main.py` - Quest accept and display fixes
- `src/cli_rpg/procedural_quests.py` - Add BranchTemplate and generation
- `src/cli_rpg/fallback_content.py` - Add branch content templates
- `src/cli_rpg/content_layer.py` - Integrate branch generation
- `tests/test_branching_quests_integration.py` - Integration tests

## Verification
```bash
pytest tests/test_quest_branching.py -v
pytest tests/test_branching_quests_integration.py -v
pytest tests/test_quest.py -v
pytest -k "branch" -v
```
