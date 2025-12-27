# Enhanced NPC Generation: Shop Inventories, Quest Hooks, and Factions

## Summary

MEDIUM task completing the NPC generation enhancements. The basic infrastructure exists (factions, shops, region contexts, NPC parsing); this work adds proper item stats to shops, generates quest hooks for quest_givers, and makes faction affiliations functional.

## What's Already Done (ec111b1)
- ✅ NPC prompt requests 3-5 NPCs with 6 roles
- ✅ Shop inventory parsing from AI response
- ✅ Faction field on NPC model with serialization
- ✅ AI-generated shop items created as MISC type

## Remaining Gaps (This Plan)
1. **Shop items are MISC type only** - no weapons, armor, consumables with stats
2. **Quest givers have no quests** - `is_quest_giver=True` but `offered_quests=[]`
3. **Factions are stored but unused** - only Merchant Guild has price effects

---

## Step 1: Add Item Stats to AI Shop Inventory Parsing

**File**: `src/cli_rpg/ai_config.py` (lines 341-363)

Update shop_inventory example in `DEFAULT_NPC_PROMPT_MINIMAL`:
```
5. Merchants should include shop_inventory with 3-6 items:
   - Each item: {"name": "...", "price": N, "item_type": "weapon|armor|consumable|misc"}
   - Weapons: add "damage_bonus": 1-10
   - Armor: add "defense_bonus": 1-8
   - Consumables: add "heal_amount": 10-50 or "stamina_restore": 10-30
```

**File**: `src/cli_rpg/ai_world.py` (lines 77-107)

Modify `_create_shop_from_ai_inventory()`:
- Parse optional `item_type` field (default to MISC)
- Parse optional stat fields: `damage_bonus`, `defense_bonus`, `heal_amount`, `stamina_restore`
- Create Item with appropriate ItemType and stats

```python
def _create_shop_from_ai_inventory(shop_inventory: list[dict], shop_name: str) -> Optional[Shop]:
    shop_items = []
    for item_data in shop_inventory:
        try:
            # Determine item type
            type_str = item_data.get("item_type", "misc").lower()
            item_type = {
                "weapon": ItemType.WEAPON,
                "armor": ItemType.ARMOR,
                "consumable": ItemType.CONSUMABLE,
            }.get(type_str, ItemType.MISC)

            item = Item(
                name=item_data["name"],
                description=f"A {item_data['name'].lower()} available for purchase.",
                item_type=item_type,
                damage_bonus=item_data.get("damage_bonus", 0),
                defense_bonus=item_data.get("defense_bonus", 0),
                heal_amount=item_data.get("heal_amount", 0),
                stamina_restore=item_data.get("stamina_restore", 0),
            )
            shop_items.append(ShopItem(item=item, buy_price=item_data["price"]))
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to create shop item: {e}")
    ...
```

---

## Step 2: Generate Quest Hooks for Quest Giver NPCs

**File**: `src/cli_rpg/ai_world.py`

Add function `_generate_quest_for_npc()`:
```python
def _generate_quest_for_npc(
    ai_service: AIService,
    npc_name: str,
    location_name: str,
    region_context: Optional[RegionContext],
    world_context: Optional[WorldContext],
    valid_locations: set[str],
    valid_npcs: set[str],
) -> Optional[Quest]:
    """Generate a quest for a quest_giver NPC.

    Uses region landmarks for EXPLORE targets, region theme for coherence.
    """
    if not ai_service:
        return None

    try:
        # Add region landmarks to valid locations for EXPLORE quests
        if region_context:
            valid_locations = valid_locations | set(l.lower() for l in region_context.landmarks)

        quest_data = ai_service.generate_quest(
            theme=world_context.theme if world_context else "fantasy",
            npc_name=npc_name,
            player_level=1,  # Default level, scales rewards
            location_name=location_name,
            valid_locations=valid_locations,
            valid_npcs=valid_npcs,
        )

        return Quest(
            name=quest_data["name"],
            description=quest_data["description"],
            objective_type=ObjectiveType(quest_data["objective_type"]),
            target=quest_data["target"],
            target_count=quest_data["target_count"],
            gold_reward=quest_data["gold_reward"],
            xp_reward=quest_data["xp_reward"],
            quest_giver=npc_name,
        )
    except Exception as e:
        logger.warning(f"Failed to generate quest for {npc_name}: {e}")
        return None
```

Modify `_create_npcs_from_data()` signature to accept context:
```python
def _create_npcs_from_data(
    npcs_data: list[dict],
    ai_service: Optional[AIService] = None,
    location_name: str = "",
    region_context: Optional[RegionContext] = None,
    world_context: Optional[WorldContext] = None,
    valid_locations: Optional[set[str]] = None,
    valid_npcs: Optional[set[str]] = None,
) -> list[NPC]:
```

Add quest generation after NPC creation:
```python
if is_quest_giver and ai_service:
    quest = _generate_quest_for_npc(
        ai_service, npc.name, location_name,
        region_context, world_context,
        valid_locations or set(), valid_npcs or set()
    )
    if quest:
        npc.offered_quests.append(quest)
```

**File**: `src/cli_rpg/ai_world.py` - `expand_world()` and `expand_area()`

Update calls to `_create_npcs_from_data()` to pass contexts:
```python
npcs = _create_npcs_from_data(
    npcs_data,
    ai_service=ai_service,
    location_name=location_data["name"],
    region_context=region_context,
    world_context=world_context,
    valid_locations={loc.lower() for loc in world.keys()},
    valid_npcs={n.name.lower() for loc in world.values() for n in loc.npcs},
)
```

---

## Step 3: Default Faction Assignments by Role

**File**: `src/cli_rpg/ai_world.py` - `_create_npcs_from_data()`

After faction extraction, add role-based defaults:
```python
faction = npc_data.get("faction")

# Default factions by role if not specified
if not faction:
    if role == "merchant":
        faction = "Merchant Guild"
    elif role == "guard":
        faction = "Town Watch"
    elif role == "quest_giver":
        faction = "Adventurer's Guild"
```

This ensures merchants get Merchant Guild price modifiers from `faction_shop.py`.

---

## Tests

**File**: `tests/test_shop_item_stats.py` (NEW)

```python
def test_ai_shop_inventory_with_weapon_stats():
    """Verify weapon items get damage_bonus from AI data."""
    inventory = [{"name": "Iron Sword", "price": 100, "item_type": "weapon", "damage_bonus": 5}]
    shop = _create_shop_from_ai_inventory(inventory, "Test Shop")
    assert shop.inventory[0].item.item_type == ItemType.WEAPON
    assert shop.inventory[0].item.damage_bonus == 5

def test_ai_shop_inventory_with_consumable_stats():
    """Verify consumables get heal_amount from AI data."""
    inventory = [{"name": "Health Potion", "price": 50, "item_type": "consumable", "heal_amount": 30}]
    shop = _create_shop_from_ai_inventory(inventory, "Test Shop")
    assert shop.inventory[0].item.item_type == ItemType.CONSUMABLE
    assert shop.inventory[0].item.heal_amount == 30

def test_ai_shop_inventory_defaults_to_misc():
    """Verify missing item_type defaults to MISC."""
    inventory = [{"name": "Trinket", "price": 25}]
    shop = _create_shop_from_ai_inventory(inventory, "Test Shop")
    assert shop.inventory[0].item.item_type == ItemType.MISC
```

**File**: `tests/test_quest_hook_generation.py` (NEW)

```python
def test_quest_giver_receives_offered_quest():
    """Verify quest_giver NPCs have offered_quests populated."""
    # Mock AI service returning quest data
    ...
    npcs = _create_npcs_from_data(
        [{"name": "Elder Sage", "description": "...", "dialogue": "...", "role": "quest_giver"}],
        ai_service=mock_ai_service,
        location_name="Town Square",
        ...
    )
    assert len(npcs[0].offered_quests) == 1

def test_quest_uses_region_landmarks():
    """Verify EXPLORE quests can target region landmarks."""
    region_context = RegionContext(
        name="Test", theme="ruins", danger_level="moderate",
        landmarks=["Ancient Temple"], coordinates=(0, 0)
    )
    # Quest generation should include "ancient temple" in valid_locations
    ...
```

**File**: `tests/test_faction_role_defaults.py` (NEW)

```python
def test_merchant_defaults_to_merchant_guild():
    """Verify merchants without faction get Merchant Guild."""
    npcs = _create_npcs_from_data([
        {"name": "Trader Bob", "description": "...", "dialogue": "...", "role": "merchant"}
    ])
    assert npcs[0].faction == "Merchant Guild"

def test_guard_defaults_to_town_watch():
    """Verify guards without faction get Town Watch."""
    npcs = _create_npcs_from_data([
        {"name": "Guard Helm", "description": "...", "dialogue": "...", "role": "guard"}
    ])
    assert npcs[0].faction == "Town Watch"

def test_explicit_faction_not_overridden():
    """Verify AI-provided faction is preserved."""
    npcs = _create_npcs_from_data([
        {"name": "Dark Trader", "description": "...", "dialogue": "...",
         "role": "merchant", "faction": "Thieves Guild"}
    ])
    assert npcs[0].faction == "Thieves Guild"
```

---

## Files Changed

| File | Change |
|------|--------|
| `ai_config.py` | Update prompt for item stats |
| `ai_world.py` | Add `_generate_quest_for_npc()`, enhance `_create_shop_from_ai_inventory()`, update `_create_npcs_from_data()` |
| `tests/test_shop_item_stats.py` | NEW - 3 tests |
| `tests/test_quest_hook_generation.py` | NEW - 2 tests |
| `tests/test_faction_role_defaults.py` | NEW - 3 tests |
