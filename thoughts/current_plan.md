# Implementation Plan: Armor Class Restrictions

## Spec

Add armor weight categories to differentiate class equipment choices:
- **ArmorWeight enum**: `LIGHT`, `MEDIUM`, `HEAVY`
- **Class restrictions**:
  - Mage: Can only equip `LIGHT` armor
  - Rogue: Can only equip `LIGHT` or `MEDIUM` armor
  - Warrior: Can equip all armor weights (only class for `HEAVY`)
  - Ranger: Can only equip `LIGHT` or `MEDIUM` armor
  - Cleric: Can only equip `LIGHT` or `MEDIUM` armor
- **Backward compatibility**: Existing armor items (no weight) default to `LIGHT`

## Implementation Steps

### 1. Add ArmorWeight enum to Item model
**File:** `src/cli_rpg/models/item.py`
- Add `ArmorWeight` enum with `LIGHT`, `MEDIUM`, `HEAVY` values
- Add optional `armor_weight: Optional[ArmorWeight] = None` field to `Item` dataclass
- Update `to_dict()` to serialize armor_weight
- Update `from_dict()` to deserialize armor_weight (default `None` for backward compat)
- Update `__str__()` to display weight for armor items

### 2. Add class armor restrictions to Character model
**File:** `src/cli_rpg/models/character.py`
- Add `CLASS_ARMOR_RESTRICTIONS` dict mapping `CharacterClass` to allowed `ArmorWeight` list
- Add `can_equip_armor(armor: Item) -> bool` method that checks weight restrictions
- Modify `equip_item()` to check `can_equip_armor()` before delegating to inventory

### 3. Update Inventory.equip() to accept class-based validation
**File:** `src/cli_rpg/models/inventory.py`
- Add optional `character_class` parameter to `equip()` method
- When provided, validate armor weight against class restrictions
- Return descriptive error information for UI feedback

### 4. Update main.py equip command
**File:** `src/cli_rpg/main.py`
- Update equip command handler to pass character class to equip validation
- Add descriptive error message when armor is too heavy for class

### 5. Update fallback content with armor weights
**File:** `src/cli_rpg/fallback_content.py`
- Update armor item templates to include `armor_weight` field
- Light armor: Robes, cloaks, leather
- Medium armor: Chainmail, scale
- Heavy armor: Plate, full plate

## Test Plan

### Test file: `tests/test_armor_restrictions.py`

```python
class TestArmorWeightEnum:
    def test_armor_weight_has_three_values()
    def test_armor_weight_values()

class TestItemArmorWeight:
    def test_item_armor_defaults_to_none()
    def test_item_armor_with_weight()
    def test_item_serialization_with_weight()
    def test_item_serialization_without_weight_backward_compat()

class TestCharacterArmorRestrictions:
    def test_mage_can_equip_light_armor()
    def test_mage_cannot_equip_medium_armor()
    def test_mage_cannot_equip_heavy_armor()
    def test_warrior_can_equip_all_armor()
    def test_rogue_can_equip_light_and_medium()
    def test_ranger_can_equip_light_and_medium()
    def test_cleric_can_equip_light_and_medium()
    def test_no_class_can_equip_any_armor()  # backward compat
    def test_armor_without_weight_can_be_equipped()  # backward compat

class TestEquipCommand:
    def test_equip_restricted_armor_shows_error_message()
```
