# Tiredness Stat for Realistic Sleep/Rest Mechanics

## Spec

Add a **Tiredness** stat (0-100) that tracks player fatigue, replacing random sleep/dream triggers with behavior-driven mechanics. High tiredness causes gameplay penalties; rest reduces tiredness based on sleep quality.

**Core Mechanics:**
- Range: 0-100 (0 = fully rested, 100 = exhausted)
- Tiredness < 30: Cannot sleep (too alert), no dreams
- Tiredness 30-60: May sleep (low chance), light rest
- Tiredness 60-80: Normal sleep, standard recovery
- Tiredness 80+: Deep sleep guaranteed, vivid dreams more likely
- Tiredness 100: Forced collapse (vulnerability)

**Gameplay Effects at High Tiredness (80+):**
- -10% attack power (mirrors dread penalty pattern)
- -10% perception (miss secrets more often)
- Movement warning messages at 60+/80+/100

## Tests First

### `tests/test_tiredness.py` (new file)

```python
# Tiredness model tests
- test_tiredness_defaults_to_zero
- test_tiredness_increase_clamps_at_100
- test_tiredness_decrease_clamps_at_zero
- test_tiredness_increase_returns_warning_at_60
- test_tiredness_increase_returns_warning_at_80
- test_tiredness_increase_returns_exhausted_warning_at_100
- test_can_sleep_false_below_30
- test_can_sleep_true_at_30
- test_can_sleep_true_at_100
- test_sleep_quality_light_below_60
- test_sleep_quality_normal_60_to_79
- test_sleep_quality_deep_80_plus
- test_get_attack_penalty_none_below_80
- test_get_attack_penalty_0_9_at_80_plus
- test_to_dict_serialization
- test_from_dict_deserialization

# Character integration tests
- test_character_has_tiredness_attribute
- test_character_to_dict_includes_tiredness
- test_character_from_dict_restores_tiredness
- test_character_from_dict_defaults_tiredness_zero  # backward compat
- test_character_get_attack_power_applies_tiredness_penalty

# GameState integration tests
- test_move_increases_tiredness
- test_combat_increases_tiredness
- test_ability_use_increases_tiredness
- test_rest_decreases_tiredness_based_on_quality
- test_camp_decreases_tiredness_more_than_rest
- test_consumable_food_decreases_tiredness

# Dream integration tests
- test_dream_blocked_when_tiredness_below_30
- test_dream_chance_modified_by_tiredness
- test_deep_sleep_increases_vivid_dream_chance
```

## Implementation Steps

### Step 1: Create `src/cli_rpg/models/tiredness.py`

```python
from dataclasses import dataclass
from typing import Optional
from cli_rpg import colors

TIREDNESS_THRESHOLDS = {
    60: "You're feeling tired...",
    80: "You're exhausted and should rest soon.",
    100: "You can barely keep your eyes open!",
}

@dataclass
class Tiredness:
    """Tracks player fatigue level (0-100)."""

    current: int = 0

    def increase(self, amount: int) -> Optional[str]:
        """Increase tiredness, return warning if threshold crossed."""
        old = self.current
        self.current = min(100, self.current + amount)
        for threshold, message in sorted(TIREDNESS_THRESHOLDS.items()):
            if old < threshold <= self.current:
                return message
        return None

    def decrease(self, amount: int) -> None:
        """Decrease tiredness (clamped to 0)."""
        self.current = max(0, self.current - amount)

    def can_sleep(self) -> bool:
        """Check if tired enough to sleep (30+)."""
        return self.current >= 30

    def sleep_quality(self) -> str:
        """Get sleep quality based on tiredness."""
        if self.current >= 80:
            return "deep"
        elif self.current >= 60:
            return "normal"
        return "light"

    def get_attack_penalty(self) -> float:
        """Get attack modifier (1.0 normal, 0.9 at 80+ tiredness)."""
        return 0.9 if self.current >= 80 else 1.0

    def get_perception_penalty(self) -> float:
        """Get perception modifier (1.0 normal, 0.9 at 80+ tiredness)."""
        return 0.9 if self.current >= 80 else 1.0

    def get_display(self) -> str:
        """Get visual bar representation."""
        bar_width = 16
        filled = round(bar_width * self.current / 100)
        empty = bar_width - filled
        bar = "█" * filled + "░" * empty
        if self.current >= 80:
            colored_bar = colors.damage(bar)
        elif self.current >= 60:
            colored_bar = colors.gold(bar)
        else:
            colored_bar = bar
        return f"TIREDNESS: {colored_bar} {self.current}%"

    def to_dict(self) -> dict:
        return {"current": self.current}

    @classmethod
    def from_dict(cls, data: dict) -> "Tiredness":
        return cls(current=data.get("current", 0))
```

### Step 2: Integrate into `Character` model

In `src/cli_rpg/models/character.py`:

1. Import `Tiredness` from `cli_rpg.models.tiredness`
2. Add field: `tiredness: Tiredness = field(default_factory=Tiredness)`
3. Update `get_attack_power()` to apply tiredness penalty:
   ```python
   return int(base_attack * modifier * dread_penalty * self.tiredness.get_attack_penalty())
   ```
4. Add method `get_effective_perception()`:
   ```python
   def get_effective_perception(self) -> int:
       return int(self.perception * self.tiredness.get_perception_penalty())
   ```
5. Update `to_dict()`: add `"tiredness": self.tiredness.to_dict()`
6. Update `from_dict()`: restore tiredness with backward compat

### Step 3: Add tiredness increases in `GameState`

In `src/cli_rpg/game_state.py`:

1. In `move()` method after successful move:
   ```python
   tiredness_msg = self.current_character.tiredness.increase(3)
   if tiredness_msg:
       message += f"\n{tiredness_msg}"
   ```

2. In combat start (when `current_combat` is created):
   ```python
   # Combat exhaustion (added at end of combat in combat.py)
   ```

### Step 4: Add tiredness increases in `combat.py`

In `CombatEncounter.execute_player_action()` or victory/flee:
```python
# After combat ends (victory or flee)
tiredness_increase = 5 + (rounds * 1)  # 5 base + 1 per round
player.tiredness.increase(tiredness_increase)
```

### Step 5: Update `dreams.py` to use tiredness

Replace random dream chance with tiredness-based system:

```python
def maybe_trigger_dream(
    ...
    tiredness: Optional[int] = None,  # NEW parameter
    ...
) -> Optional[str]:
    # Block dreams if not tired enough
    if tiredness is not None and tiredness < 30:
        return None

    # Adjust dream chance based on tiredness
    if tiredness is not None:
        if tiredness >= 80:
            chance = 0.40  # Deep sleep: 40% dream chance
        elif tiredness >= 60:
            chance = 0.20  # Normal sleep: 20%
        else:
            chance = 0.05  # Light sleep: 5%
    else:
        chance = dream_chance if dream_chance is not None else DREAM_CHANCE

    # ... rest of existing logic
```

### Step 6: Update rest/camp recovery

In `main.py` rest handler:
```python
# Calculate tiredness reduction based on sleep quality
quality = char.tiredness.sleep_quality()
if quality == "deep":
    tiredness_reduction = 80
elif quality == "normal":
    tiredness_reduction = 50
else:  # light
    tiredness_reduction = 25

char.tiredness.decrease(tiredness_reduction)
messages.append(f"Tiredness reduced by {tiredness_reduction}%.")
```

In `camping.py` camp handler:
```python
# Camping provides moderate tiredness reduction
tiredness_reduction = 40
if has_campfire:
    tiredness_reduction += 10  # Campfire bonus
char.tiredness.decrease(tiredness_reduction)
```

### Step 7: Add tiredness to status display

In `Character.__str__()` or status command:
```python
# Add tiredness bar to status output
tiredness_display = self.tiredness.get_display()
```

### Step 8: Optional - Food items reduce tiredness

In `Character.use_item()` for consumables:
```python
# Check for stamina_restore items reducing tiredness
if item.stamina_restore > 0:
    tiredness_reduction = item.stamina_restore // 3
    self.tiredness.decrease(tiredness_reduction)
```

## Files Modified

| File | Changes |
|------|---------|
| `src/cli_rpg/models/tiredness.py` | NEW - Tiredness model |
| `src/cli_rpg/models/character.py` | Add tiredness field, integrate into attack/perception |
| `src/cli_rpg/game_state.py` | Increase tiredness on move |
| `src/cli_rpg/combat.py` | Increase tiredness after combat |
| `src/cli_rpg/dreams.py` | Use tiredness for dream triggers |
| `src/cli_rpg/main.py` | Rest tiredness reduction, status display |
| `src/cli_rpg/camping.py` | Camp tiredness reduction |
| `tests/test_tiredness.py` | NEW - ~25 tests |
