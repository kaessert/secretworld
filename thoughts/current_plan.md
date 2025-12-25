# Distance-Based Enemy Difficulty Scaling - Implementation Plan

## Spec

Scale enemy stats based on Manhattan distance from origin (0,0). Formula: `base_stat * (1 + distance * 0.15)`. Rewards (XP, gold) scale proportionally.

**Distance tiers:**
- Near (0-3): Easy (multiplier 1.0-1.45)
- Mid (4-7): Moderate (multiplier 1.6-2.05)
- Far (8-12): Challenging (multiplier 2.2-2.8)
- Deep (13+): Dangerous (multiplier 2.95+)

## Implementation

### 1. Add distance calculation utility

**File:** `src/cli_rpg/combat.py`

Add function to calculate Manhattan distance from origin:
```python
def calculate_distance_from_origin(coordinates: tuple[int, int] | None) -> int:
    """Calculate Manhattan distance from origin (0,0)."""
    if coordinates is None:
        return 0
    return abs(coordinates[0]) + abs(coordinates[1])

def get_distance_multiplier(distance: int) -> float:
    """Get stat scaling multiplier based on distance from origin."""
    return 1.0 + distance * 0.15
```

### 2. Update spawn_enemy to accept distance parameter

**File:** `src/cli_rpg/combat.py`

Modify `spawn_enemy()` signature and stat calculation:
```python
def spawn_enemy(
    location_name: str,
    level: int,
    location_category: Optional[str] = None,
    distance: int = 0  # NEW: distance from origin
) -> Enemy:
    ...
    # Apply distance multiplier to base stats
    multiplier = get_distance_multiplier(distance)
    base_health = int((20 + (level * 10)) * multiplier)
    base_attack = int((3 + (level * 2)) * multiplier)
    base_defense = int((1 + level) * multiplier)
    base_xp = int((20 + (level * 10)) * multiplier)  # XP scales too
```

### 3. Update spawn_enemies to pass distance

**File:** `src/cli_rpg/combat.py`

Add distance parameter to `spawn_enemies()`:
```python
def spawn_enemies(
    location_name: str,
    level: int,
    count: Optional[int] = None,
    location_category: Optional[str] = None,
    distance: int = 0  # NEW
) -> list[Enemy]:
    ...
    enemy = spawn_enemy(location_name, level, location_category, distance)
```

### 4. Update ai_spawn_enemy for distance-based scaling

**File:** `src/cli_rpg/combat.py`

Modify `ai_spawn_enemy()` to accept and pass distance:
```python
def ai_spawn_enemy(
    location_name: str,
    player_level: int,
    ai_service: Optional["AIService"] = None,
    theme: str = "fantasy",
    distance: int = 0  # NEW
) -> Enemy:
```

For AI-generated enemies, apply distance multiplier to returned stats before creating Enemy.

### 5. Update trigger_encounter in GameState

**File:** `src/cli_rpg/game_state.py`

Calculate distance from current location and pass to spawn functions:
```python
def trigger_encounter(self, location_name: str) -> Optional[str]:
    from cli_rpg.combat import calculate_distance_from_origin

    # Get current location's coordinates for distance calculation
    location = self.world.get(location_name)
    coords = location.coordinates if location else None
    distance = calculate_distance_from_origin(coords)

    if self.ai_service is not None:
        enemy = ai_spawn_enemy(..., distance=distance)
    else:
        enemies = spawn_enemies(..., distance=distance)
```

### 6. Update AI enemy generation prompt (optional enhancement)

**File:** `src/cli_rpg/ai_config.py`

Add distance context to enemy generation prompt so AI can generate thematically harder enemies at greater distances. Update `DEFAULT_ENEMY_GENERATION_PROMPT` to include `{distance}` placeholder.

## Tests

**File:** `tests/test_distance_scaling.py`

```python
class TestDistanceCalculation:
    def test_distance_from_origin_at_origin(self):
        """Distance at (0,0) should be 0."""
        assert calculate_distance_from_origin((0, 0)) == 0

    def test_distance_from_origin_manhattan(self):
        """Distance should be |x| + |y|."""
        assert calculate_distance_from_origin((3, 4)) == 7
        assert calculate_distance_from_origin((-2, 5)) == 7

    def test_distance_from_origin_none(self):
        """None coordinates should return 0."""
        assert calculate_distance_from_origin(None) == 0

class TestDistanceMultiplier:
    def test_multiplier_at_origin(self):
        """At distance 0, multiplier is 1.0."""
        assert get_distance_multiplier(0) == 1.0

    def test_multiplier_scales(self):
        """Multiplier = 1 + distance * 0.15"""
        assert get_distance_multiplier(10) == 2.5

class TestEnemyDistanceScaling:
    def test_spawn_enemy_stats_scale_with_distance(self):
        """Enemies at greater distance have higher stats."""
        near = spawn_enemy("forest", level=1, distance=0)
        far = spawn_enemy("forest", level=1, distance=10)

        # At distance 10, multiplier is 2.5
        assert far.max_health > near.max_health
        assert far.attack_power > near.attack_power
        assert far.xp_reward > near.xp_reward

    def test_spawn_enemy_distance_zero_unchanged(self):
        """At distance 0, stats match original formulas."""
        enemy = spawn_enemy("forest", level=3, distance=0)
        assert enemy.max_health == 20 + (3 * 10)  # 50
        assert enemy.attack_power == 3 + (3 * 2)  # 9

class TestGameStateEncounterDistance:
    def test_trigger_encounter_uses_location_coordinates(self):
        """Encounters should spawn enemies scaled by location distance."""
        # Create world with location at (5, 5) = distance 10
        location = Location(name="Far Forest", description="...", coordinates=(5, 5))
        # Mock or test that spawned enemies have scaled stats
```

## Files Changed

1. `src/cli_rpg/combat.py` - Add distance utilities, update spawn functions
2. `src/cli_rpg/game_state.py` - Pass distance to spawn functions
3. `src/cli_rpg/ai_config.py` - Update prompt (optional)
4. `tests/test_distance_scaling.py` - New test file
