# Implementation Plan: Create Initial YAML Validation Scenarios

## Task Summary
Create initial YAML validation scenarios for core game features (Phase 3, Step 5 of the Validation Framework).

## Scope
MEDIUM task - creating YAML scenario files using the existing ScenarioRunner infrastructure.

## Directory Structure
```
scripts/scenarios/
├── movement/
│   ├── basic_navigation.yaml
│   └── subgrid_entry_exit.yaml
├── combat/
│   ├── basic_attack.yaml
│   └── flee_combat.yaml
├── inventory/
│   ├── equip_unequip.yaml
│   └── use_item.yaml
├── npc/
│   ├── talk_dialogue.yaml
│   └── shop_browse.yaml
├── exploration/
│   └── look_map.yaml
└── rest/
    └── basic_rest.yaml
```

## Implementation Steps

### 1. Create directory structure
```bash
mkdir -p scripts/scenarios/{movement,combat,inventory,npc,exploration,rest}
touch scripts/scenarios/__init__.py
```

### 2. Create movement/basic_navigation.yaml
- Test `look` command, `go <direction>` changes location
- Seed: 42001

### 3. Create movement/subgrid_entry_exit.yaml
- Test `enter` and `exit` for sub-locations
- Seed: 42002

### 4. Create combat/basic_attack.yaml
- Test `attack` enters combat, tracks enemy health
- Seed: 42003

### 5. Create combat/flee_combat.yaml
- Test `flee` exits combat
- Seed: 42004

### 6. Create inventory/equip_unequip.yaml
- Test `equip` and `unequip` commands
- Seed: 42005

### 7. Create inventory/use_item.yaml
- Test `use` command for consumables
- Seed: 42006

### 8. Create npc/talk_dialogue.yaml
- Test `talk` command with NPCs
- Seed: 42007

### 9. Create npc/shop_browse.yaml
- Test `shop` and `browse` commands
- Seed: 42008

### 10. Create exploration/look_map.yaml
- Test `look` and `map` commands
- Seed: 42009

### 11. Create rest/basic_rest.yaml
- Test `rest` command
- Seed: 42010

### 12. Create tests/test_scenario_files.py
- Test all YAML files parse without errors
- Test each scenario has valid assertion types
- Test seeds are unique across scenarios

## Files to Create
1. `scripts/scenarios/__init__.py`
2. `scripts/scenarios/movement/basic_navigation.yaml`
3. `scripts/scenarios/movement/subgrid_entry_exit.yaml`
4. `scripts/scenarios/combat/basic_attack.yaml`
5. `scripts/scenarios/combat/flee_combat.yaml`
6. `scripts/scenarios/inventory/equip_unequip.yaml`
7. `scripts/scenarios/inventory/use_item.yaml`
8. `scripts/scenarios/npc/talk_dialogue.yaml`
9. `scripts/scenarios/npc/shop_browse.yaml`
10. `scripts/scenarios/exploration/look_map.yaml`
11. `scripts/scenarios/rest/basic_rest.yaml`
12. `tests/test_scenario_files.py`

## Verification
```bash
pytest tests/test_scenario_files.py -v
```
