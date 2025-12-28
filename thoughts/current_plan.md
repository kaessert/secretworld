# Implementation Plan: Inventory Management YAML Scenarios

## Objective
Add comprehensive YAML validation scenarios for inventory management (equip, unequip, use, drop, armor restrictions, holy symbols) to expand scripted playthrough coverage.

## Current State
- Existing scenarios: `equip_unequip.yaml` and `use_item.yaml` are basic stubs that only check command validity
- Missing coverage: armor restrictions, holy symbols, drop command, actual equip/unequip state verification
- Demo world has: Iron Sword (weapon), Leather Armor (armor), Health Potions (consumable), Torch (misc)

## New Scenarios to Create

### 1. `scripts/scenarios/inventory/drop_item.yaml`
Test the drop command with state verification:
- Use demo mode with known items
- Check inventory count before drop
- Drop Health Potion
- Verify inventory count decreased
- Verify item no longer in inventory

### 2. `scripts/scenarios/inventory/equip_weapon.yaml`
Replace weak `equip_unequip.yaml` with proper weapon equip/unequip testing:
- Use demo mode (starts with Iron Sword equipped)
- Unequip weapon, verify in inventory
- Buy Steel Sword from shop
- Equip Steel Sword, verify equipped
- Equip Iron Sword (swap), verify Steel Sword back in inventory

### 3. `scripts/scenarios/inventory/equip_armor.yaml`
Test armor equip/unequip with state verification:
- Use demo mode (starts with Leather Armor equipped)
- Unequip armor, verify in inventory
- Equip armor again, verify equipped state

### 4. `scripts/scenarios/inventory/armor_restrictions.yaml`
Test class-based armor restrictions (Mage can only wear LIGHT):
- Create Mage character (class 2)
- Start with random light armor
- Attempt to equip HEAVY armor from shop - should fail
- Verify error message about armor weight

### 5. `scripts/scenarios/inventory/use_consumable.yaml`
Replace weak `use_item.yaml` with actual consumable testing:
- Use demo mode (starts with Health Potions)
- Take damage (enter combat, get hit)
- Record health
- Use Health Potion
- Verify health increased
- Verify potion removed from inventory

### 6. `scripts/scenarios/inventory/holy_symbol.yaml`
Test Cleric-only holy symbol equip restriction:
- Create Cleric character (class 5)
- Find/buy holy symbol
- Equip holy symbol - should succeed
- Verify equipped_holy_symbol in state

## Implementation Steps

1. **Create `drop_item.yaml`**
   - Seed: 42010
   - demo_mode: true
   - Steps: inventory → dump_state (count) → drop Health Potion → dump_state (verify count decreased)

2. **Replace `equip_unequip.yaml` with `equip_weapon.yaml`**
   - Seed: 42005 (keep same)
   - demo_mode: true
   - Steps: unequip weapon → verify in inventory → equip weapon → verify equipped

3. **Create `equip_armor.yaml`**
   - Seed: 42011
   - demo_mode: true
   - Steps: unequip armor → verify in inventory → equip armor → verify equipped

4. **Create `armor_restrictions.yaml`**
   - Seed: 42012
   - skip_character_creation: false
   - character_creation_inputs: ["TestMage", "2", "2", "yes"]
   - Steps: create mage → try equip heavy armor → verify rejection message

5. **Replace `use_item.yaml` with `use_consumable.yaml`**
   - Seed: 42006 (keep same)
   - demo_mode: true
   - Steps: take damage → record health → use potion → verify health increased

6. **Create `holy_symbol.yaml`**
   - Seed: 42013
   - skip_character_creation: false (need Cleric)
   - character_creation_inputs: ["TestCleric", "5", "2", "yes"]
   - More complex: need to explore/buy holy symbol, then equip

## Verification
- Run `pytest tests/test_scenario_files.py -v` to validate all scenarios parse correctly
- Scenarios use unique seeds (42010-42013 are available)
- All assertion types are valid (STATE_EQUALS, STATE_RANGE, NARRATIVE_MATCH, COMMAND_VALID, CONTENT_PRESENT)

## Files to Create/Modify
- `scripts/scenarios/inventory/drop_item.yaml` (new)
- `scripts/scenarios/inventory/equip_weapon.yaml` (replace equip_unequip.yaml)
- `scripts/scenarios/inventory/equip_armor.yaml` (new)
- `scripts/scenarios/inventory/armor_restrictions.yaml` (new)
- `scripts/scenarios/inventory/use_consumable.yaml` (replace use_item.yaml)
- `scripts/scenarios/inventory/holy_symbol.yaml` (new)

## Notes
- Demo mode provides deterministic test world with known items
- Holy symbol scenario is most complex - may need to navigate to shop or find one
- Armor restrictions require creating specific class character (Mage for testing heavy armor restriction)
