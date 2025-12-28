# Implementation Plan: Character Creation Validation Scenarios

## Goal
Add validation scenarios for character creation with all 5 classes to complete the "Scripted Playthrough for Feature Validation" checklist item in ISSUES.md.

## Analysis
- Current scenario system uses `GameSession` which starts with `--skip-character-creation` flag
- Character creation in JSON mode reads from stdin via `create_character_non_interactive()`
- Input sequence: name -> class (1-5) -> method (1=manual/2=random) -> [stats if manual] -> confirm (yes)
- State includes character class in `dump_state` output
- Existing unit tests in `tests/test_character_creation.py` cover functions, but no subprocess-level validation

## Approach
Create 5 YAML scenarios (one per class) that:
1. Use a new config option `skip_character_creation: false`
2. Use `character_creation_inputs` config to pipe character creation inputs via stdin
3. Validate resulting character state via `dump_state` assertions

## Implementation Steps

### 1. Extend GameSession to support character creation inputs
**File**: `scripts/ai_agent.py`

Modify `GameSession.start()` to accept optional `creation_inputs` parameter:
- When `skip_character_creation=False`, remove `--skip-character-creation` from cmd
- Send creation_inputs to stdin before entering main loop

```python
def start(self, skip_character_creation: bool = True, creation_inputs: list[str] = None) -> None:
    cmd = [sys.executable, "-u", "-m", "cli_rpg.main", "--json", f"--seed={self.seed}"]
    if skip_character_creation:
        cmd.append("--skip-character-creation")
    # After process starts, send creation_inputs to stdin
```

### 2. Extend ScenarioRunner to use new config
**File**: `scripts/validation/scenarios.py`

Modify `run_scenario()` to check config and call session.start() appropriately:
```python
skip_char = scenario.config.get("skip_character_creation", True)
creation_inputs = scenario.config.get("character_creation_inputs", [])
session.start(skip_character_creation=skip_char, creation_inputs=creation_inputs)
```

### 3. Create character creation scenarios directory
**Directory**: `scripts/scenarios/character_creation/`

Create `__init__.py` for package.

### 4. Create 5 class-specific scenarios
Seeds 42020-42024, each with random stats (method: 2) for simplicity.

**Files**:
- `warrior_creation.yaml` - class: 1, seed: 42020
- `mage_creation.yaml` - class: 2, seed: 42021
- `rogue_creation.yaml` - class: 3, seed: 42022
- `ranger_creation.yaml` - class: 4, seed: 42023
- `cleric_creation.yaml` - class: 5, seed: 42024

Example structure:
```yaml
scenario:
  name: "Warrior Character Creation"
  description: "Test creating a Warrior class character"
  seed: 42020
  config:
    max_commands: 10
    timeout: 60
    skip_character_creation: false
    character_creation_inputs:
      - "TestWarrior"
      - "1"
      - "2"
      - "yes"
  steps:
    - command: "status"
      assertions:
        - type: COMMAND_VALID
          value: true
        - type: NARRATIVE_MATCH
          field: "last_narrative"
          value: "Warrior"
```

### 5. Add tests for new scenarios
**File**: `tests/test_scenario_files.py`

Add "character_creation" to expected_dirs and add validation test.

### 6. Update ISSUES.md
Mark checkbox complete: `- [x] Character creation (all 5 classes)`

## Files to Create/Modify
1. `scripts/ai_agent.py` - Modify GameSession.start()
2. `scripts/validation/scenarios.py` - Handle new config options
3. `scripts/scenarios/character_creation/__init__.py` - New package
4. `scripts/scenarios/character_creation/warrior_creation.yaml`
5. `scripts/scenarios/character_creation/mage_creation.yaml`
6. `scripts/scenarios/character_creation/rogue_creation.yaml`
7. `scripts/scenarios/character_creation/ranger_creation.yaml`
8. `scripts/scenarios/character_creation/cleric_creation.yaml`
9. `tests/test_scenario_files.py` - Extend
10. `ISSUES.md` - Update checkbox

## Test Commands
```bash
pytest tests/test_scenario_files.py -v -k character_creation
pytest tests/test_character_creation.py -v  # Existing unit tests still pass
```
