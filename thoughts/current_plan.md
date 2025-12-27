# Issue 21: Location-Specific Random Encounters

## Spec

Create `encounter_tables.py` module with category-specific enemy tables and encounter configuration:
- **Category-specific enemies**: Different enemy pools for dungeon, cave, ruins, forest, temple
- **Category-specific merchants**: Merchants sell location-appropriate items
- **Variable encounter rates**: Different encounter chances per category

### Enemy Categories (from ISSUES.md acceptance criteria)
- **Dungeon**: undead, constructs, cultists
- **Cave**: beasts, spiders, giant bats
- **Ruins**: ghosts, treasure hunters, golems
- **Forest**: wolves, bandits, fey creatures
- **Temple**: dark priests, animated statues

## Files

- **Create**: `src/cli_rpg/encounter_tables.py`
- **Create**: `tests/test_encounter_tables.py`
- **Modify**: `src/cli_rpg/combat.py` - Import and use category tables
- **Modify**: `src/cli_rpg/random_encounters.py` - Use category-specific encounter rates and merchant inventories

## Tests (TDD)

### Category Enemy Tables (`test_encounter_tables.py`)
- `test_dungeon_enemies_exist` - CATEGORY_ENEMIES["dungeon"] has undead/construct enemies
- `test_cave_enemies_exist` - CATEGORY_ENEMIES["cave"] has beast/spider enemies
- `test_ruins_enemies_exist` - CATEGORY_ENEMIES["ruins"] has ghost/golem enemies
- `test_forest_enemies_exist` - CATEGORY_ENEMIES["forest"] has wolf/bandit/fey enemies
- `test_temple_enemies_exist` - CATEGORY_ENEMIES["temple"] has dark priest/animated statue enemies
- `test_each_category_has_minimum_enemies` - Each category has at least 4 enemy types
- `test_get_enemies_for_category_valid` - `get_enemies_for_category("dungeon")` returns enemy list
- `test_get_enemies_for_category_fallback` - Unknown category returns default enemies

### Category Encounter Rates
- `test_encounter_rates_exist` - CATEGORY_ENCOUNTER_RATES dict exists
- `test_dungeon_encounter_rate_higher` - Dungeon has higher rate than overworld
- `test_safe_categories_lower_rate` - Town/village have lower encounter rates
- `test_get_encounter_rate_valid` - `get_encounter_rate("dungeon")` returns correct rate
- `test_get_encounter_rate_default` - Unknown category returns default rate (0.15)

### Category Merchant Inventories
- `test_merchant_items_exist` - CATEGORY_MERCHANT_ITEMS dict exists
- `test_dungeon_merchant_sells_healing` - Dungeon merchants favor healing items
- `test_cave_merchant_sells_light` - Cave merchants sell torches/light items
- `test_get_merchant_items_valid` - `get_merchant_items("dungeon")` returns item templates
- `test_get_merchant_items_fallback` - Unknown category returns default items

### Integration Tests (`test_random_encounters.py` - extend existing)
- `test_hostile_encounter_uses_category_table` - Dungeon hostile spawns from dungeon table
- `test_encounter_rate_varies_by_category` - Dungeon triggers more encounters than forest
- `test_merchant_inventory_matches_category` - Dungeon merchant has category-specific items

## Implementation Steps

1. **Create test file** `tests/test_encounter_tables.py` with tests above

2. **Create `encounter_tables.py`** with:
   ```python
   CATEGORY_ENEMIES = {
       "dungeon": ["Skeleton Warrior", "Zombie", "Stone Construct", "Cultist", "Bone Golem", "Dark Acolyte"],
       "cave": ["Giant Spider", "Cave Bear", "Giant Bat", "Goblin", "Troll", "Cave Beetle"],
       "ruins": ["Restless Ghost", "Stone Golem", "Treasure Hunter", "Phantom", "Ancient Guardian", "Ruin Lurker"],
       "forest": ["Wolf", "Bandit", "Wild Boar", "Dryad", "Forest Spirit", "Giant Spider"],
       "temple": ["Dark Priest", "Animated Statue", "Temple Guardian", "Cultist Zealot", "Stone Sentinel", "Shadow Monk"],
   }

   CATEGORY_ENCOUNTER_RATES = {
       "dungeon": 0.25,  # Higher danger
       "cave": 0.20,
       "ruins": 0.20,
       "temple": 0.20,
       "forest": 0.15,  # Default overworld rate
       "town": 0.05,    # Safe zones
       "village": 0.05,
   }

   CATEGORY_MERCHANT_ITEMS = {
       "dungeon": ["healing_potion", "antidote", "torch"],
       "cave": ["torch", "rope", "healing_potion"],
       "ruins": ["lockpick", "healing_potion", "antidote"],
       "temple": ["holy_water", "healing_potion", "blessed_charm"],
       "forest": ["rations", "healing_potion", "rope"],
   }
   ```

3. **Add helper functions**:
   - `get_enemies_for_category(category: str) -> list[str]` - Returns enemy list or default
   - `get_encounter_rate(category: str) -> float` - Returns rate or default (0.15)
   - `get_merchant_items(category: str) -> list[str]` - Returns item templates or default

4. **Update `combat.py`**:
   - Import `CATEGORY_ENEMIES` from `encounter_tables`
   - Modify `spawn_enemy()` to check `CATEGORY_ENEMIES` before `ENEMY_TEMPLATES`
   - Priority: location_category in CATEGORY_ENEMIES > terrain_type > ENEMY_TEMPLATES

5. **Update `random_encounters.py`**:
   - Import `get_encounter_rate`, `get_merchant_items` from `encounter_tables`
   - Modify `check_for_random_encounter()` to use `get_encounter_rate(location.category)`
   - Modify `spawn_wandering_merchant()` to use `get_merchant_items(category)`

6. **Run tests** to verify all pass

7. **Update ISSUES.md** to mark Issue 21 as COMPLETED
