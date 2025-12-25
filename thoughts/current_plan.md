# Implementation Plan: Increase Test Coverage Beyond 95.01%

## Objective
Increase test coverage from 95.01% to ~96%+ by adding targeted tests for uncovered lines in the lowest-coverage modules.

## Coverage Gap Analysis (by impact)

| Module | Current | Missing Lines | Priority |
|--------|---------|---------------|----------|
| ai_service.py | 92% | 34 lines | HIGH |
| world.py | 92% | 4 lines | HIGH |
| persistence.py | 93% | 8 lines | HIGH |
| ai_config.py | 93% | 6 lines | MEDIUM |
| ai_world.py | 94% | 11 lines | MEDIUM |
| main.py | 94% | 38 lines | MEDIUM |

## Implementation Steps

### 1. Create `tests/test_coverage_gaps.py`

#### ai_service.py gaps
- Test Anthropic import fallback when package unavailable (lines 18-21)
- Test authentication error handling in `_call_openai` (line 241)
- Test fallback error after retries exhausted (line 252)
- Test JSON decode error in `_parse_enemy_response` (lines 892-893)
- Test missing required field in enemy response (line 900)
- Test description too long validation (line 920)
- Test attack_flavor too short/long validation (lines 927, 931)
- Test JSON decode error in `_parse_item_response` (lines 1043-1044)
- Test missing required field in item response (line 1051)
- Test cache hit path for quest generation (lines 1202-1206, 1216)
- Test JSON decode error in `_parse_quest_response` (lines 1261-1262)
- Test missing required field in quest response (line 1269)
- Test xp_reward validation (line 1320)

#### world.py gaps (lines 18-21)
- Test AI import fallback when ai_service unavailable

#### persistence.py gaps (lines 9, 33, 162-163, 233, 267-268, 310)
- Test filename truncation for long names (line 33)
- Test fallback filename format parsing (lines 162-163)
- Test delete_save FileNotFoundError path (line 233)
- Test save_game_state OSError/PermissionError (lines 267-268)
- Test load_game_state ValueError re-raise (line 310)

#### ai_config.py gaps (lines 296-299, 302, 306)
- Test AI_PROVIDER=anthropic with missing ANTHROPIC_API_KEY
- Test AI_PROVIDER=openai with missing OPENAI_API_KEY
- Test invalid AI_PROVIDER value

#### ai_world.py gaps (lines 39, 146, 150-151, 292-294, 434, 436-437, 469)
- Test invalid direction to get_opposite_direction (line 39)
- Test skipping duplicate location names (line 146)
- Test skipping non-grid directions (lines 150-151)

### 2. Create `tests/test_main_additional_coverage.py`

#### main.py gaps (lines 157-159, 250-251, 294-295, 327-328, 490-491, 609-610, 617, 805, 857-858, 909, 959-961, 964-968, 1028, 1032, 1097-1100)
- Test load failure exception handling (lines 157-159)
- Test autosave IOError during combat victory (lines 250-251)
- Test autosave IOError during flee (lines 294-295)
- Test autosave IOError during cast victory (lines 327-328)
- Test AI dialogue generation exception fallback (lines 490-491)
- Test buy command with quest progress messages (lines 609-610)
- Test sell command without args (line 617)
- Test quests command edge case - no active quests message (line 805)
- Test quit command save flow (lines 857-858)
- Test rest command outside combat (line 909)
- Test game loop combat status display (lines 959-961)
- Test game loop conversation mode routing (lines 964-968)
- Test start_game empty world validation (line 1028)
- Test start_game missing starting location validation (line 1032)
- Test AI initialization exception fallback (lines 1097-1100)

### 3. Create `tests/test_model_coverage_gaps.py`

#### character.py gaps (lines 204-210, 665-668)
- Test use_item on generic consumable without heal (lines 204-210)
- Test display colored health at different thresholds (lines 665-668)

#### inventory.py gaps (lines 143-146, 151, 246)
- Test unequip armor when inventory is full (lines 143-146)
- Test unequip invalid slot returns False (line 151)
- Test display with equipped armor (line 246)

#### world_grid.py gaps (lines 137, 218, 226, 318, 330)
- Test get_neighbor with invalid direction (line 137)
- Test __iter__ method (line 218)
- Test values() method (line 226)
- Test ensure_dangling_exits with no coordinates (line 318)
- Test ensure_dangling_exits returns False when no candidates (line 330)

## Verification
```bash
source venv/bin/activate && pytest --cov=src/cli_rpg --cov-report=term-missing
# Target: Coverage should increase from 95.01% to 96%+
```
