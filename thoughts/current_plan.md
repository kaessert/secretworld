# Implementation Plan: Light Sources to Reduce Dread Buildup

## Feature Spec

Light source items are consumable items that reduce dread buildup when entering dark areas. When a light source is active:
- Dread increases from location category are reduced by 50%
- Night dread bonus is negated
- Light sources last for a limited number of moves (e.g., 5 moves)
- Multiple light sources stack by extending duration (not multiplying effect)

## Design Decisions

1. **Item representation**: Add `light_duration` field to Item model (0 = not a light source, >0 = moves of light)
2. **Tracking active light**: Add `light_remaining` field to Character model (counts down on each move)
3. **Effect application**: Modify `_update_dread_on_move()` in `game_state.py` to check for active light

---

## Tests (TDD) - `tests/test_light_source.py`

### Item light_duration Tests
1. `test_item_light_duration_default_zero` - Item defaults to light_duration=0
2. `test_item_light_duration_positive` - Item can have light_duration > 0
3. `test_item_light_duration_negative_rejected` - Negative light_duration raises ValueError
4. `test_item_light_duration_serialization` - to_dict/from_dict preserves light_duration
5. `test_item_str_shows_light_info` - String includes "X moves of light" for light sources

### Character light_remaining Tests
6. `test_character_light_remaining_default_zero` - Character starts with light_remaining=0
7. `test_character_use_light_source` - Using light item sets light_remaining
8. `test_character_light_source_stacks` - Using light when already lit extends duration
9. `test_character_tick_light_decrements` - tick_light() decrements light_remaining
10. `test_character_tick_light_expires_message` - tick_light() returns message when expires
11. `test_character_tick_light_no_message_when_active` - No message when light still active
12. `test_character_light_serialization` - to_dict/from_dict preserves light_remaining

### Use Item Activation Tests
13. `test_use_light_source_activates_light` - Using torch activates light
14. `test_use_light_source_message` - Message indicates light activation
15. `test_use_light_source_removes_item` - Item removed from inventory after use

### Dread Reduction Integration Tests (add to `tests/test_dread_integration.py`)
16. `test_light_halves_category_dread` - Active light halves dread from location category
17. `test_light_negates_night_bonus` - Active light removes DREAD_NIGHT_BONUS
18. `test_light_ticks_down_on_move` - Light decrements after each move
19. `test_light_expires_after_duration` - Light reaches 0 after correct moves
20. `test_light_expiration_message_in_move` - Move output includes "light fades" message
21. `test_dread_normal_after_light_expires` - Full dread returns when light gone
22. `test_light_does_not_affect_town_reduction` - Town dread reduction unchanged

---

## Implementation Steps

### Step 1: Extend Item Model with light_duration
**File**: `src/cli_rpg/models/item.py`

```python
# Add to Item dataclass:
light_duration: int = 0

# In __post_init__, add validation:
if self.light_duration < 0:
    raise ValueError("light_duration cannot be negative")

# Update to_dict():
"light_duration": self.light_duration

# Update from_dict():
light_duration=data.get("light_duration", 0)

# Update __str__() - after heal_amount check:
if self.light_duration > 0:
    stat_parts.append(f"{self.light_duration} moves of light")
```

### Step 2: Add light_remaining to Character Model
**File**: `src/cli_rpg/models/character.py`

```python
# Add field:
light_remaining: int = 0

# Add methods:
def use_light_source(self, duration: int) -> None:
    """Activate or extend light source duration."""
    self.light_remaining += duration

def tick_light(self) -> Optional[str]:
    """Tick down light remaining. Returns message if light expires."""
    if self.light_remaining > 0:
        self.light_remaining -= 1
        if self.light_remaining == 0:
            return "Your light source fades into darkness..."
    return None

def has_active_light(self) -> bool:
    """Check if character has an active light source."""
    return self.light_remaining > 0

# Update to_dict():
"light_remaining": self.light_remaining

# Update from_dict():
character.light_remaining = data.get("light_remaining", 0)
```

### Step 3: Modify use_item() for Light Sources
**File**: `src/cli_rpg/models/character.py`

In `use_item()` method, after the heal_amount check, add:

```python
# Handle light source items
if item.light_duration > 0:
    self.use_light_source(item.light_duration)
    self.inventory.remove_item(item)
    if self.light_remaining == item.light_duration:
        message = f"You light the {item.name}. It illuminates your surroundings."
    else:
        message = f"You add the {item.name} to your light. Your light will last longer."
    quest_messages = self.record_use(item.name)
    if quest_messages:
        message += "\n" + "\n".join(quest_messages)
    return (True, message)
```

### Step 4: Apply Light Effect in Dread Calculation
**File**: `src/cli_rpg/game_state.py`

Modify `_update_dread_on_move()`:

```python
def _update_dread_on_move(self, location: Location) -> Optional[str]:
    category = location.category or "default"
    dread_meter = self.current_character.dread_meter
    has_light = self.current_character.has_active_light()

    # Towns reduce dread (unaffected by light)
    if category == "town":
        if dread_meter.dread > 0:
            dread_meter.reduce_dread(DREAD_TOWN_REDUCTION)
        return None

    # Calculate dread increase based on category
    dread_increase = DREAD_BY_CATEGORY.get(category, 5)

    # Light reduces category dread by 50%
    if has_light:
        dread_increase = dread_increase // 2

    # Night adds extra dread (negated by light)
    if self.game_time.is_night() and not has_light:
        dread_increase += DREAD_NIGHT_BONUS

    # ... rest of weather/health dread modifiers unchanged ...

    # Add dread
    dread_message = dread_meter.add_dread(dread_increase)

    # Tick light and check for expiration
    light_message = self.current_character.tick_light()

    # Combine messages
    if dread_message and light_message:
        return f"{dread_message}\n{light_message}"
    return dread_message or light_message
```

### Step 5: Add Torch to Default Shop
**File**: `src/cli_rpg/world.py`

In the default shop inventory section (in `create_default_town_square()` or equivalent):

```python
Item(
    name="Torch",
    description="A wooden torch that provides light in dark places",
    item_type=ItemType.CONSUMABLE,
    light_duration=5
)
# Add to ShopItem with appropriate price (e.g., 15 gold)
```

---

## File Changes Summary

| File | Change Type |
|------|-------------|
| `src/cli_rpg/models/item.py` | Modify - add light_duration field |
| `src/cli_rpg/models/character.py` | Modify - add light tracking |
| `src/cli_rpg/game_state.py` | Modify - apply light effect to dread |
| `src/cli_rpg/world.py` | Modify - add Torch to shop |
| `tests/test_light_source.py` | **New** - light source tests |
| `tests/test_dread_integration.py` | Modify - add light+dread tests |
