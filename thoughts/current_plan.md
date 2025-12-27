# Issue 18: AI-Generated Hidden Secrets Implementation Plan

## Problem
The `hidden_secrets` field on Location is never populated by AI generation, and `check_passive_detection()` in `secrets.py` is defined but never called. Players never automatically discover secrets in AI-generated areas.

## Implementation Steps

### 1. Add Secret Generation to `ai_world.py`

**Add constants and helper function after `TREASURE_CATEGORIES` (~line 322):**

```python
# Categories that should have secrets
SECRET_CATEGORIES = frozenset({"dungeon", "cave", "ruins", "temple", "forest"})

# Secret templates: (type, description, base_threshold)
SECRET_TEMPLATES: dict[str, list[tuple[str, str, int]]] = {
    "dungeon": [
        ("hidden_treasure", "A loose stone conceals a hidden cache.", 13),
        ("hidden_door", "Faint scratches on the floor suggest a secret passage.", 14),
        ("trap", "A pressure plate lurks beneath the dust.", 12),
        ("lore_hint", "Ancient writing on the wall tells of forgotten secrets.", 11),
    ],
    "cave": [
        ("hidden_treasure", "A glinting gemstone wedged in a crack.", 12),
        ("trap", "Unstable rocks threaten to fall.", 11),
        ("lore_hint", "Primitive drawings depict something deeper in the caves.", 10),
    ],
    "ruins": [
        ("hidden_treasure", "An ornate box buried beneath rubble.", 14),
        ("hidden_door", "A worn section of wall hints at a secret passage.", 15),
        ("lore_hint", "Faded inscriptions speak of the civilization that fell here.", 12),
    ],
    "temple": [
        ("hidden_treasure", "An offering hidden behind the altar.", 13),
        ("trap", "A divine ward protects this sacred place.", 14),
        ("lore_hint", "Sacred texts reveal the temple's true purpose.", 11),
    ],
    "forest": [
        ("hidden_treasure", "A hollow tree conceals a traveler's stash.", 11),
        ("hidden_door", "An overgrown path leads to a hidden clearing.", 13),
        ("trap", "A concealed snare lies among the leaves.", 12),
    ],
}

def _generate_secrets_for_location(category: str, distance: int = 0) -> list[dict]:
    """Generate 1-2 hidden secrets for a location.

    Args:
        category: Location category (dungeon, cave, etc.)
        distance: Distance from entry (affects threshold)

    Returns:
        List of secret dicts matching Location.hidden_secrets schema
    """
    if category not in SECRET_CATEGORIES:
        return []

    templates = SECRET_TEMPLATES.get(category, SECRET_TEMPLATES.get("dungeon", []))
    if not templates:
        return []

    num_secrets = random.randint(1, 2)
    selected = random.sample(templates, min(num_secrets, len(templates)))

    secrets = []
    for secret_type, description, base_threshold in selected:
        threshold = base_threshold + min(distance, 4)
        secret = {
            "type": secret_type,
            "description": description,
            "threshold": threshold,
            "discovered": False,
        }

        if secret_type == "hidden_treasure":
            secret["reward_gold"] = random.randint(10, 30) + (distance * 5)
        elif secret_type == "trap":
            secret["trap_damage"] = 5 + (distance * 2)
        elif secret_type == "hidden_door":
            secret["exit_direction"] = random.choice(["north", "south", "east", "west"])

        secrets.append(secret)

    return secrets
```

**Wire secrets into location creation (3 places):**

1. `generate_subgrid_for_location()` (~line 700, after creating `new_loc`):
   - Add secrets to non-entry rooms based on category

2. `expand_area()` (~line 1340, after creating `new_loc`):
   - Add secrets to non-entry rooms based on category

3. `expand_world()` (~line 1150, after creating `new_location`):
   - Add secrets to named locations with appropriate categories

### 2. Wire Passive Detection into `game_state.py`

**Add import (~line 42):**
```python
from cli_rpg.secrets import check_passive_detection
```

**Add helper method:**
```python
def _check_and_report_passive_secrets(self, location: Location) -> Optional[str]:
    """Check for passive secret detection and return message if found."""
    if not self.character:
        return None
    detected = check_passive_detection(self.character, location)
    if not detected:
        return None
    return "\n".join(f"You notice: {s['description']}" for s in detected)
```

**Call in `move()` (~line 720) and `enter()` (~line 975):**
- After location change, call `_check_and_report_passive_secrets()`
- Append result to return message if secrets found

### 3. Create Tests

**File:** `tests/test_ai_secrets.py`

- `test_secret_categories_defined` - Verify constant exists
- `test_secret_templates_for_each_category` - Each category has templates
- `test_generates_1_to_2_secrets` - Output count validation
- `test_secret_has_required_fields` - Schema validation
- `test_hidden_treasure_has_gold` - Type-specific field
- `test_trap_has_damage` - Type-specific field
- `test_hidden_door_has_direction` - Type-specific field
- `test_distance_scales_threshold` - Deeper = harder
- `test_non_secret_category_returns_empty` - Town/village returns []

## Files to Modify
- `src/cli_rpg/ai_world.py` - Add constants and `_generate_secrets_for_location()`, wire into 3 functions
- `src/cli_rpg/game_state.py` - Import and call `check_passive_detection()`

## Files to Create
- `tests/test_ai_secrets.py` - Tests for secret generation

## Verification
```bash
pytest tests/test_ai_secrets.py -v
pytest tests/test_perception.py -v  # Ensure existing secret tests pass
pytest  # Full suite
```
