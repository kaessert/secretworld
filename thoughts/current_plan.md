# Terrain-Aware Default Merchant Shops

## Summary
Modify `_create_default_merchant_shop()` in `ai_world.py` to accept optional terrain/region parameters and return thematically appropriate inventory instead of hardcoded generic items.

## Spec

**Current behavior:** `_create_default_merchant_shop()` returns identical shop (Health Potion, Antidote, Travel Rations) regardless of where merchant is located.

**Target behavior:** Default merchant shops should have terrain-appropriate inventory:
- Mountain merchants: climbing gear, cold-weather items, pickaxes
- Swamp merchants: antidotes, insect repellent, waterproof gear
- Desert merchants: water skins, sun protection, heat-resistant items
- Forest merchants: trail rations, rope, camping supplies
- Beach/coastal: fishing gear, rope, water-related items
- Default/plains: standard consumables (current behavior)

## Tests (add to `tests/test_ai_merchant_detection.py`)

```python
class TestTerrainAwareMerchantShops:
    """Tests for terrain-based default shop inventories."""

    def test_default_shop_no_terrain_has_standard_items(self):
        """Default shop without terrain has standard consumables."""
        shop = _create_default_merchant_shop()
        assert shop.find_item_by_name("Health Potion") is not None

    def test_mountain_terrain_shop_has_climbing_gear(self):
        """Mountain terrain shop includes mountain-appropriate items."""
        shop = _create_default_merchant_shop(terrain_type="mountain")
        item_names = [si.item.name for si in shop.inventory]
        assert any("pick" in name.lower() or "climbing" in name.lower()
                   or "warm" in name.lower() for name in item_names)

    def test_swamp_terrain_shop_has_antidotes(self):
        """Swamp terrain shop emphasizes poison cures."""
        shop = _create_default_merchant_shop(terrain_type="swamp")
        antidote = shop.find_item_by_name("Antidote")
        assert antidote is not None

    def test_desert_terrain_shop_has_water(self):
        """Desert terrain shop includes water/hydration items."""
        shop = _create_default_merchant_shop(terrain_type="desert")
        item_names = [si.item.name for si in shop.inventory]
        assert any("water" in name.lower() for name in item_names)

    def test_forest_terrain_shop_has_trail_supplies(self):
        """Forest terrain shop has trail/camping supplies."""
        shop = _create_default_merchant_shop(terrain_type="forest")
        item_names = [si.item.name for si in shop.inventory]
        assert any("ration" in name.lower() or "rope" in name.lower()
                   for name in item_names)

    def test_beach_terrain_shop_has_fishing_gear(self):
        """Beach/coastal terrain shop has fishing/water items."""
        shop = _create_default_merchant_shop(terrain_type="beach")
        item_names = [si.item.name for si in shop.inventory]
        assert any("fish" in name.lower() or "rope" in name.lower()
                   for name in item_names)

    def test_all_terrain_shops_have_health_potion(self):
        """All terrain shops should include health potion as baseline."""
        for terrain in ["mountain", "swamp", "desert", "forest", "beach", "plains"]:
            shop = _create_default_merchant_shop(terrain_type=terrain)
            assert shop.find_item_by_name("Health Potion") is not None
```

## Implementation Steps

### 1. Add terrain-specific inventory definitions in `ai_world.py`

Add after line 75 (after `MERCHANT_KEYWORDS`):

```python
# Terrain-specific default shop inventories
# Each terrain has thematic items plus a base Health Potion
TERRAIN_SHOP_ITEMS: dict[str, list[tuple[str, str, ItemType, int, dict]]] = {
    # (name, description, item_type, price, stats_dict)
    "mountain": [
        ("Climbing Pick", "Essential for scaling rocky terrain", ItemType.MISC, 45, {}),
        ("Warm Cloak", "Protection against mountain cold", ItemType.ARMOR, 60, {"defense_bonus": 2}),
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
    ],
    "swamp": [
        ("Antidote", "Cures poison", ItemType.CONSUMABLE, 40, {}),
        ("Insect Repellent", "Wards off swamp insects", ItemType.CONSUMABLE, 25, {}),
        ("Wading Boots", "Keeps feet dry in marshland", ItemType.ARMOR, 55, {"defense_bonus": 1}),
    ],
    "desert": [
        ("Water Skin", "Precious water for desert travel", ItemType.CONSUMABLE, 30, {"stamina_restore": 15}),
        ("Sun Cloak", "Protection from harsh desert sun", ItemType.ARMOR, 50, {"defense_bonus": 1}),
        ("Antidote", "Cures poison from desert creatures", ItemType.CONSUMABLE, 40, {}),
    ],
    "forest": [
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Hemp Rope", "Sturdy rope for woodland travel", ItemType.MISC, 25, {}),
        ("Herbalist's Kit", "Basic healing herbs", ItemType.CONSUMABLE, 35, {"heal_amount": 15}),
    ],
    "beach": [
        ("Fishing Net", "For catching coastal fish", ItemType.MISC, 30, {}),
        ("Sturdy Rope", "Sea-worthy rope", ItemType.MISC, 25, {}),
        ("Dried Fish", "Preserved seafood", ItemType.CONSUMABLE, 15, {"heal_amount": 8}),
    ],
    "foothills": [
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Climbing Rope", "For ascending rocky terrain", ItemType.MISC, 35, {}),
        ("Warm Blanket", "Comfort in cool mountain nights", ItemType.MISC, 25, {}),
    ],
    "hills": [
        ("Trail Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Walking Staff", "Aids travel over hilly terrain", ItemType.WEAPON, 40, {"damage_bonus": 2}),
        ("Antidote", "Cures poison", ItemType.CONSUMABLE, 40, {}),
    ],
    "plains": [
        ("Travel Rations", "Sustaining food for journeys", ItemType.CONSUMABLE, 20, {"heal_amount": 10}),
        ("Antidote", "Cures poison", ItemType.CONSUMABLE, 40, {}),
    ],
}

# Terrain-specific shop names for immersion
TERRAIN_SHOP_NAMES: dict[str, str] = {
    "mountain": "Mountain Supplies",
    "swamp": "Swampland Wares",
    "desert": "Desert Provisions",
    "forest": "Woodland Goods",
    "beach": "Coastal Trading Post",
    "foothills": "Hillside Supplies",
    "hills": "Hilltop Wares",
    "plains": "Traveling Wares",
}
```

### 2. Modify `_create_default_merchant_shop()` signature and body

Change lines 40-71:

```python
def _create_default_merchant_shop(
    terrain_type: Optional[str] = None,
) -> Shop:
    """Create a default shop for AI-generated merchant NPCs.

    Args:
        terrain_type: Optional terrain type for thematic inventory

    Returns:
        Shop with terrain-appropriate items (always includes Health Potion)
    """
    # Health Potion is always included as baseline
    potion = Item(
        name="Health Potion",
        description="Restores 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25
    )
    shop_items = [ShopItem(item=potion, buy_price=50)]

    # Get terrain-specific items
    terrain_key = terrain_type.lower() if terrain_type else "plains"
    terrain_items = TERRAIN_SHOP_ITEMS.get(terrain_key, TERRAIN_SHOP_ITEMS["plains"])

    for name, desc, itype, price, stats in terrain_items:
        item = Item(
            name=name,
            description=desc,
            item_type=itype,
            **stats
        )
        shop_items.append(ShopItem(item=item, buy_price=price))

    shop_name = TERRAIN_SHOP_NAMES.get(terrain_key, "Traveling Wares")
    return Shop(name=shop_name, inventory=shop_items)
```

### 3. Update `_create_npcs_from_data()` signature

Add terrain_type parameter at line 189:

```python
def _create_npcs_from_data(
    npcs_data: list[dict],
    ai_service: Optional[AIService] = None,
    location_name: str = "",
    region_context: Optional[RegionContext] = None,
    world_context: Optional[WorldContext] = None,
    valid_locations: Optional[set[str]] = None,
    valid_npcs: Optional[set[str]] = None,
    terrain_type: Optional[str] = None,  # NEW
) -> list[NPC]:
```

Update line 237 call:
```python
shop = _create_default_merchant_shop(terrain_type=terrain_type)
```

### 4. Update callers to pass terrain_type

**Line 453 (`create_ai_world` starting location):** No terrain info available, use default (plains):
```python
ai_npcs = _create_npcs_from_data(starting_data.get("npcs", []))
```
(No change needed - terrain_type=None defaults to plains)

**Line 519 (`create_ai_world` expansion):** No terrain info available:
```python
location_npcs = _create_npcs_from_data(location_data.get("npcs", []))
```
(No change needed)

**Line 681 (`expand_world`):** terrain_type parameter available:
```python
location_npcs = _create_npcs_from_data(
    location_data.get("npcs", []),
    terrain_type=terrain_type,
)
```

**Line 851 (`expand_area`):** Extract terrain from loc_data if available:
```python
location_npcs = _create_npcs_from_data(
    loc_data.get("npcs", []),
    terrain_type=terrain_type,  # from expand_area parameter
)
```

## Files to Modify
1. `src/cli_rpg/ai_world.py` - Add TERRAIN_SHOP_ITEMS, update _create_default_merchant_shop, update _create_npcs_from_data
2. `tests/test_ai_merchant_detection.py` - Add TestTerrainAwareMerchantShops class

## Verification
```bash
pytest tests/test_ai_merchant_detection.py -v
pytest tests/test_ai_world_generation.py -v
pytest --cov=src/cli_rpg/ai_world
```
