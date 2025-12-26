# Fix: Shop command fails with AI-generated merchants in SubGrid locations

## Summary
AI-generated NPCs with "Merchant" in their name don't work with the `shop` command because they lack `is_merchant=True` and a `Shop` object.

## Root Cause

**The Problem Flow:**
1. AI generates NPC data: `{"name": "Tech Merchant", "description": "...", "role": "villager"}`
2. `_create_npcs_from_data()` in `ai_world.py` creates NPC with `is_merchant=False` (because role != "merchant")
3. Player uses `shop` command
4. `main.py` line 1304: `merchant = next((npc for npc in location.npcs if npc.is_merchant and npc.shop), None)`
5. Returns `None` because NPC has `is_merchant=False` and no `shop` object
6. User sees "There's no merchant here."

**Root Causes:**
1. AI may not always return `"role": "merchant"` for NPCs with merchant-like names
2. Even when `role="merchant"` is set, no `Shop` object is created for the NPC
3. `_create_npcs_from_data()` only sets `is_merchant=True` but doesn't create a Shop

## Solution

Two-part fix:
1. **Infer role from name**: If NPC name contains merchant-related keywords, set `role="merchant"`
2. **Create default shop for merchants**: When `is_merchant=True`, create a basic shop if none provided

## Implementation Steps

### 1. Add merchant name inference in `_create_npcs_from_data()` (ai_world.py)

After extracting role from NPC data (line 51), add name-based inference:

```python
# Infer merchant role from name if not explicitly set
if role == "villager":  # Only override default role
    name_lower = npc_data["name"].lower()
    merchant_keywords = {"merchant", "trader", "vendor", "shopkeeper", "seller", "dealer"}
    if any(keyword in name_lower for keyword in merchant_keywords):
        role = "merchant"
```

### 2. Create default shop for AI-generated merchants (ai_world.py)

When creating merchant NPCs, generate a basic shop:

```python
# Create shop for merchant NPCs without one
shop = None
if is_merchant:
    shop = _create_default_merchant_shop()
```

Add helper function:

```python
def _create_default_merchant_shop() -> Shop:
    """Create a default shop for AI-generated merchant NPCs."""
    from cli_rpg.models.item import Item, ItemType

    potion = Item(
        name="Health Potion",
        description="Restores 25 HP",
        item_type=ItemType.CONSUMABLE,
        heal_amount=25
    )
    antidote = Item(
        name="Antidote",
        description="Cures poison",
        item_type=ItemType.CONSUMABLE,
    )
    rations = Item(
        name="Travel Rations",
        description="Sustaining food for journeys",
        item_type=ItemType.CONSUMABLE,
        heal_amount=10
    )

    return Shop(
        name="Traveling Wares",
        inventory=[
            ShopItem(item=potion, buy_price=50),
            ShopItem(item=antidote, buy_price=40),
            ShopItem(item=rations, buy_price=20),
        ]
    )
```

### 3. Update NPC creation to use the shop (ai_world.py line 55-61)

```python
npc = NPC(
    name=npc_data["name"],
    description=npc_data["description"],
    dialogue=npc_data.get("dialogue", "Hello, traveler."),
    is_merchant=is_merchant,
    is_quest_giver=is_quest_giver,
    shop=shop  # Add this
)
```

## Test Plan

### New test file: `tests/test_ai_merchant_detection.py`

1. **test_merchant_role_inferred_from_name**: NPC with "Merchant" in name gets `is_merchant=True`
2. **test_trader_role_inferred_from_name**: NPC with "Trader" in name gets `is_merchant=True`
3. **test_vendor_role_inferred_from_name**: NPC with "Vendor" in name gets `is_merchant=True`
4. **test_explicit_merchant_role_preserved**: NPC with `role="merchant"` works regardless of name
5. **test_non_merchant_names_stay_villager**: NPC named "Guard" stays `is_merchant=False`
6. **test_ai_merchant_has_default_shop**: Inferred merchant gets a Shop object
7. **test_ai_merchant_shop_has_items**: Default shop contains buyable items
8. **test_shop_command_works_with_ai_merchant**: Integration test with full command flow

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_world.py` | Add `_create_default_merchant_shop()`, update `_create_npcs_from_data()` |
| `tests/test_ai_merchant_detection.py` | NEW - test merchant name inference and shop creation |
