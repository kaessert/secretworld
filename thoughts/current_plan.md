# Plan: Fix Health Potion Waste at Full Health

## Summary
Prevent health potions from being consumed when player is already at full health.

## Location
`src/cli_rpg/models/character.py`, `use_item()` method (lines 163-192)

## Implementation

### 1. Add test for full health rejection
**File:** `tests/test_character_inventory.py`

Add test after `test_use_health_potion_caps_at_max`:
```python
def test_use_health_potion_at_full_health(self):
    """Test: Cannot use health potion when at full health"""
    character = Character(
        name="Hero",
        strength=10,
        dexterity=10,
        intelligence=10
    )
    # Character starts at full health

    potion = Item(
        name="Health Potion",
        description="Restores health",
        item_type=ItemType.CONSUMABLE,
        heal_amount=30
    )
    character.inventory.add_item(potion)

    result, message = character.use_item(potion)

    assert result is False
    assert potion in character.inventory.items  # Potion should NOT be consumed
    assert "full health" in message.lower() or "already" in message.lower()
```

### 2. Update `use_item()` method
**File:** `src/cli_rpg/models/character.py`

In the `use_item()` method, add check before the heal logic (around line 183):

```python
# Apply effect
if item.heal_amount > 0:
    # Check if already at full health
    if self.health >= self.max_health:
        return (False, "You're already at full health!")
    old_health = self.health
    self.heal(item.heal_amount)
    healed = self.health - old_health
    self.inventory.remove_item(item)
    return (True, f"You used {item.name} and healed {healed} health!")
```

### 3. Verify
Run: `pytest tests/test_character_inventory.py -v`
