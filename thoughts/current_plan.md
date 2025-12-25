# AI-Generated Item Catalogue Implementation Plan

## Feature Spec

Add `AIService.generate_item()` method that creates contextual, themed items (weapons, armor, consumables) for shops and loot. Items are generated based on world theme, location context, and optional item type hints.

### Input Parameters
- `theme: str` - World theme (e.g., "fantasy", "sci-fi")
- `location_name: str` - Location context for thematic consistency
- `item_type: Optional[ItemType]` - Optional constraint (WEAPON, ARMOR, CONSUMABLE, MISC)
- `player_level: int` - For stat scaling

### Output Dictionary
```python
{
    "name": str,           # 2-30 chars
    "description": str,    # 1-200 chars
    "item_type": str,      # "weapon", "armor", "consumable", "misc"
    "damage_bonus": int,   # For weapons (scaled to level)
    "defense_bonus": int,  # For armor (scaled to level)
    "heal_amount": int,    # For consumables (scaled to level)
    "suggested_price": int # For shop integration
}
```

### Validation Rules
- Name: 2-30 characters (matches `Item.MIN_NAME_LENGTH`, `Item.MAX_NAME_LENGTH`)
- Description: 1-200 characters (matches `Item.MIN_DESC_LENGTH`, `Item.MAX_DESC_LENGTH`)
- Stat bonuses: Must be non-negative integers
- Only appropriate bonus for item type (weapons get damage, armor gets defense, consumables get heal)

---

## Implementation Steps

### Step 1: Add prompt template to `ai_config.py`
- Add `DEFAULT_ITEM_GENERATION_PROMPT` constant with placeholders: `{theme}`, `{location_name}`, `{item_type_hint}`, `{player_level}`
- Add `item_generation_prompt: str` field to `AIConfig` dataclass
- Update `to_dict()` and `from_dict()` to serialize/deserialize the new field

### Step 2: Add `generate_item()` method to `ai_service.py`
- Add `generate_item(theme, location_name, player_level, item_type=None) -> dict`
- Add `_build_item_prompt()` helper method
- Add `_parse_item_response()` with validation:
  - Name length (2-30 chars)
  - Description length (1-200 chars)
  - Valid item_type enum value
  - Non-negative stat bonuses
  - Stat appropriateness (only relevant bonus for item type)
  - suggested_price must be positive integer

### Step 3: Add helper function to `ai_world.py` (optional integration)
- Add `generate_shop_inventory()` function that generates multiple items
- Uses `generate_item()` to populate merchant shops with themed items

---

## Test Plan (`tests/test_ai_item_generation.py`)

### AIConfig Tests
- `test_ai_config_has_item_prompt()` - Verify `item_generation_prompt` field exists
- `test_ai_config_item_prompt_serialization()` - Verify `to_dict`/`from_dict` roundtrip
- `test_default_item_prompt_contains_placeholders()` - Verify required placeholders exist

### AIService.generate_item() Tests
- `test_generate_item_returns_valid_structure()` - All required fields present
- `test_generate_item_validates_name_length()` - Rejects names <2 or >30 chars
- `test_generate_item_validates_description_length()` - Rejects descriptions <1 or >200 chars
- `test_generate_item_validates_item_type()` - Rejects invalid item types
- `test_generate_item_validates_non_negative_stats()` - Rejects negative bonuses
- `test_generate_item_validates_positive_price()` - Rejects zero/negative price
- `test_generate_item_respects_type_constraint()` - Returns requested item type when provided
- `test_generate_item_uses_context()` - Prompt includes theme, location, level
- `test_generate_item_handles_api_error()` - Raises `AIServiceError` on failure

### Integration Tests
- `test_generate_item_can_create_valid_item_instance()` - Result can construct `Item` model
- `test_generate_item_weapon_has_damage_bonus()` - Weapons have appropriate stats
- `test_generate_item_armor_has_defense_bonus()` - Armor has appropriate stats
- `test_generate_item_consumable_has_heal_amount()` - Consumables have appropriate stats

---

## Files to Modify
1. `src/cli_rpg/ai_config.py` - Add prompt template and field
2. `src/cli_rpg/ai_service.py` - Add `generate_item()` method
3. `tests/test_ai_item_generation.py` - New test file (following `test_ai_enemy_generation.py` pattern)

## Files Unchanged
- `src/cli_rpg/models/item.py` - Already has all needed fields and validation
- `src/cli_rpg/models/shop.py` - Already supports Item integration
