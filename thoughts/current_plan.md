# Implementation Plan: Ironhold City

## Spec
Add **Ironhold City** as a new safe zone overworld landmark with 4 sub-locations at coordinates (0, -1) (south of Town Square):

- **Ironhold City** (overworld landmark, safe zone)
  - **Ironhold Market** - entry point, contains a wealthy Merchant NPC
  - **Castle Ward** - noble district with a Captain of the Guard NPC
  - **Slums** - contains a Beggar NPC (recruitable)
  - **Temple Quarter** - contains a Priest NPC

## Tests First
Add to `tests/test_world.py`:

1. `test_default_world_ironhold_city_exists` - verify location exists
2. `test_default_world_ironhold_city_is_overworld` - verify is_overworld=True, is_safe_zone=True, 4 sub-locations, entry_point="Ironhold Market"
3. `test_default_world_ironhold_city_sub_locations_exist` - all 4 sub-locations in world dict
4. `test_default_world_ironhold_city_sub_locations_have_parent` - parent_location="Ironhold City", is_safe_zone=True
5. `test_default_world_ironhold_city_sub_locations_no_cardinal_exits` - no cardinal connections
6. `test_default_world_ironhold_city_connections` - north->Town Square
7. `test_default_world_town_square_has_south_connection` - south->Ironhold City
8. `test_default_world_merchant_in_ironhold_market` - wealthy Merchant NPC in Ironhold Market
9. `test_default_world_captain_in_castle_ward` - Captain of the Guard in Castle Ward
10. `test_default_world_beggar_in_slums` - Beggar NPC in Slums, is_recruitable=True
11. `test_default_world_priest_in_temple_quarter` - Priest NPC in Temple Quarter

Update `test_default_world_location_count_with_sublocations` to expect 23 locations (18 + 1 overworld + 4 sub-locations).

## Implementation
In `src/cli_rpg/world.py` `create_default_world()`:

1. **Create Ironhold City overworld location** after Abandoned Mines (~line 192):
   ```python
   ironhold_city = Location(
       name="Ironhold City",
       description="A massive walled city of stone and steel. Towers rise above fortified walls, and the streets bustle with merchants, soldiers, and citizens from across the realm.",
       is_overworld=True,
       is_safe_zone=True,
       sub_locations=["Ironhold Market", "Castle Ward", "Slums", "Temple Quarter"],
       entry_point="Ironhold Market"
   )
   ```

2. **Add to grid** at (0, -1) south of Town Square (~line 208):
   ```python
   grid.add_location(ironhold_city, 0, -1)
   ```

3. **Create 4 NPCs** with appropriate dialogue (~after line 438):
   - Wealthy Merchant (is_merchant=True with luxury shop)
   - Captain of the Guard
   - Beggar (is_recruitable=True)
   - Priest

4. **Create luxury shop** for wealthy merchant with high-tier items:
   - Greater Health Potion (50 HP, 100 gold)
   - Steel Sword (10 damage, 200 gold)
   - Plate Armor (10 defense, 350 gold)

5. **Create 4 sub-locations** with parent="Ironhold City", is_safe_zone=True:
   - Ironhold Market (with Wealthy Merchant)
   - Castle Ward (with Captain)
   - Slums (with Beggar)
   - Temple Quarter (with Priest)

6. **Add sub-locations to world dict** (~after line 496):
   ```python
   world["Ironhold Market"] = ironhold_market
   world["Castle Ward"] = castle_ward
   world["Slums"] = slums
   world["Temple Quarter"] = temple_quarter
   ```

## Files to Modify
- `tests/test_world.py` - add 11 new tests, update location count test (18 → 23)
- `src/cli_rpg/world.py` - add Ironhold City and 4 sub-locations with NPCs
