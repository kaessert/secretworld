# Implementation Plan: Complete Combat Validation Scenarios

## Summary
Add missing combat scenarios (abilities, stealth kills, companion combat) to complete the combat validation feature. The existing `basic_attack.yaml` and `flee_combat.yaml` scenarios only test basic commands - they don't exercise class-specific abilities or advanced combat mechanics.

## Current State
- 2 combat scenarios exist: `basic_attack.yaml` (seed 42003), `flee_combat.yaml` (seed 42004)
- Both scenarios randomly wander hoping to trigger combat, with minimal assertions
- **Missing coverage**:
  - Class abilities: `bash` (Warrior), `fireball`/`ice_bolt` (Mage), `sneak` (Rogue), `bless`/`smite` (Cleric)
  - Stealth kills: Rogue `sneak` → `attack` backstab mechanic
  - Companion combat: Ranger animal companion attacks during combat
- Demo mode (`demo_mode: true`) can use test world fixture which has a boss (`Giant Spider`) at known location

## Implementation Steps

### 1. Create `warrior_bash.yaml` scenario (seed: 42030)
**File**: `scripts/scenarios/combat/warrior_bash.yaml`
- Use `demo_mode: true` with Warrior character
- Navigate to Dark Cave SubGrid and find enemy
- Test `bash` command with assertions for:
  - COMMAND_VALID: bash is recognized
  - NARRATIVE_MATCH: output mentions "stun" or damage

### 2. Create `mage_spells.yaml` scenario (seed: 42031)
**File**: `scripts/scenarios/combat/mage_spells.yaml`
- Character creation for Mage class (class 2)
- Navigate to trigger combat
- Test `fireball` and `ice_bolt` commands with assertions for:
  - COMMAND_VALID: spells are recognized
  - STATE_RANGE: mana decreases after casting

### 3. Create `rogue_stealth.yaml` scenario (seed: 42032)
**File**: `scripts/scenarios/combat/rogue_stealth.yaml`
- Character creation for Rogue class (class 3)
- Navigate to trigger combat
- Test `sneak` → `attack` sequence with assertions for:
  - COMMAND_VALID: sneak is recognized
  - NARRATIVE_MATCH: output mentions "backstab" or "stealth"

### 4. Create `cleric_abilities.yaml` scenario (seed: 42033)
**File**: `scripts/scenarios/combat/cleric_abilities.yaml`
- Character creation for Cleric class (class 5)
- Navigate to trigger combat
- Test `bless` and `smite` commands with assertions for:
  - COMMAND_VALID: abilities are recognized
  - STATE_RANGE: mana decreases after casting

### 5. Create `demo_combat.yaml` scenario (seed: 42034)
**File**: `scripts/scenarios/combat/demo_combat.yaml`
- Use `demo_mode: true` to load test world
- Navigate to Dark Cave → Spider Den (boss location) at [-1, 1, 0]
- Path: go east (to Dark Cave) → enter → go north → go west
- Test combat against Giant Spider boss
- Assertions for complete combat flow (attack, damage, victory)

### 6. Update `test_scenario_files.py` to verify new scenarios
**File**: `tests/test_scenario_files.py`
- Update `test_combat_scenarios_exist` to expect 7 scenarios (not 2)
- Add specific checks for new scenario files

### 7. Update ISSUES.md combat checkbox
**File**: `ISSUES.md` (line 149)
- Change `[ ] Combat (attack, abilities, flee, stealth kills, companion combat)` to `[x] Combat ...`
- Add note about scenarios: `- 7 scenarios in scripts/scenarios/combat/ (seeds 42003-42004, 42030-42034)`

## Scenario Format Reference
```yaml
scenario:
  name: "Scenario Name"
  description: "Description"
  seed: 42030
  config:
    max_commands: 30
    timeout: 90
    demo_mode: true  # OR character_creation_inputs for class-specific
    character_creation_inputs:  # Only for non-demo mode
      - "CharacterName"
      - "2"  # Class: 1=Warrior, 2=Mage, 3=Rogue, 4=Ranger, 5=Cleric
      - "2"  # Random stats
      - "yes"
  setup:
    - "dump_state"
  steps:
    - command: "attack"
      assertions:
        - type: COMMAND_VALID
          field: ""
          value: true
          message: "Attack should be valid"
```

## Test Verification
```bash
# Run scenario file validation tests
pytest tests/test_scenario_files.py::TestCombatScenarios -v

# Run all scenario file tests
pytest tests/test_scenario_files.py -v

# Verify demo mode combat works
cli-rpg --demo
# Then: go east → enter → go north → go west → attack
```
