# Implementation Plan: Fix KILL Quest Target Spawn Mismatch

## Problem

KILL quests generate enemy targets (e.g., "Giant Spider") that never spawn in the game world, making quests impossible to complete. Confirmed reproducible with seed 999.

## Root Cause

- `ai_service.py:_parse_quest_response()` validates quest JSON structure but not target validity
- `ai_config.py` prompt lists valid enemies as guidance but AI ignores it
- `combat.py:spawn_enemy()` has hardcoded `enemy_templates` dict but doesn't export it
- No validation connects quest targets to spawnable enemies

## Spec

For KILL objective quests, the target must match one of the spawnable enemy types from combat.py templates:
- Forest: Wolf, Bear, Wild Boar, Giant Spider
- Cave: Bat, Goblin, Troll, Cave Dweller
- Dungeon: Skeleton, Zombie, Ghost, Dark Knight
- Mountain: Eagle, Goat, Mountain Lion, Yeti
- Village: Bandit, Thief, Ruffian, Outlaw
- Default: Monster, Creature, Beast, Fiend

## Implementation

### 1. Export VALID_ENEMY_TYPES from combat.py

**File:** `src/cli_rpg/combat.py` (after line ~2147)

Add constant that flattens all enemy templates into a set:

```python
# Exported set of all spawnable enemy types for validation
VALID_ENEMY_TYPES: set[str] = {
    enemy.lower()
    for enemies in enemy_templates.values()
    for enemy in enemies
}
```

Note: The `enemy_templates` dict is defined inside `spawn_enemy()`. Either:
- Move dict to module level (preferred), OR
- Define VALID_ENEMY_TYPES with hardcoded values matching the dict

### 2. Validate KILL quest targets in ai_service.py

**File:** `src/cli_rpg/ai_service.py:_parse_quest_response()` (after line ~1867)

```python
# Validate KILL quest targets against spawnable enemies
if objective_type == "kill":
    from cli_rpg.combat import VALID_ENEMY_TYPES
    if target.lower() not in VALID_ENEMY_TYPES:
        raise AIGenerationError(
            f"Invalid KILL quest target '{target}'. Must be a spawnable enemy type."
        )
```

### 3. Tests

**File:** `tests/test_quest_validation.py` (new file)

```python
"""Tests for quest target validation."""
import pytest
from cli_rpg.combat import VALID_ENEMY_TYPES
from cli_rpg.ai_service import AIService, AIGenerationError

class TestValidEnemyTypes:
    """Tests for VALID_ENEMY_TYPES constant."""

    def test_contains_expected_forest_enemies(self):
        assert "wolf" in VALID_ENEMY_TYPES
        assert "bear" in VALID_ENEMY_TYPES
        assert "giant spider" in VALID_ENEMY_TYPES

    def test_contains_expected_cave_enemies(self):
        assert "goblin" in VALID_ENEMY_TYPES
        assert "troll" in VALID_ENEMY_TYPES

    def test_all_lowercase(self):
        for enemy in VALID_ENEMY_TYPES:
            assert enemy == enemy.lower()

class TestKillQuestValidation:
    """Tests for KILL quest target validation."""

    def test_valid_kill_target_accepted(self):
        # Mock response with valid target
        response = '{"name":"Hunt Wolves","description":"Kill wolves","objective_type":"kill","target":"Wolf","target_count":3,"gold_reward":50,"xp_reward":100}'
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Wolf"

    def test_invalid_kill_target_rejected(self):
        response = '{"name":"Hunt Dragons","description":"Kill dragons","objective_type":"kill","target":"Dragon","target_count":1,"gold_reward":50,"xp_reward":100}'
        service = AIService.__new__(AIService)
        with pytest.raises(AIGenerationError, match="Invalid KILL quest target"):
            service._parse_quest_response(response, "Test NPC")

    def test_non_kill_quest_target_not_validated(self):
        # EXPLORE quests should not be validated against enemy types
        response = '{"name":"Find Cave","description":"Explore cave","objective_type":"explore","target":"Hidden Cave","target_count":1,"gold_reward":50,"xp_reward":100}'
        service = AIService.__new__(AIService)
        result = service._parse_quest_response(response, "Test NPC")
        assert result["target"] == "Hidden Cave"
```

## Verification

```bash
# Run new tests
pytest tests/test_quest_validation.py -v

# Run existing quest tests to ensure no regressions
pytest tests/test_quest*.py -v

# Full test suite
pytest
```

## Files Modified

| File | Change |
|------|--------|
| `src/cli_rpg/combat.py` | Move `enemy_templates` to module level, add `VALID_ENEMY_TYPES` |
| `src/cli_rpg/ai_service.py` | Add KILL target validation in `_parse_quest_response()` |
| `tests/test_quest_validation.py` | New test file for target validation |
