# AI-Generated Monsters/Enemies Implementation Plan

## Feature Spec

Add AI-powered enemy generation that creates contextual, themed enemies with descriptions, stats scaling, and encounter flavor text. When AI service is available, enemies are generated dynamically based on location context and theme. Graceful fallback to existing `spawn_enemy()` when AI is unavailable.

### New Capabilities
1. `AIService.generate_enemy()` - Generate enemy with name, description, stats, and attack_flavor text
2. `ai_spawn_enemy()` - Wrapper function that uses AI generation with fallback to static templates
3. Enemy model extended with optional `description` and `attack_flavor` fields

### Constraints
- Enemy name: 2-30 characters
- Enemy description: 10-150 characters
- Attack flavor: 10-100 characters
- Stats must be positive integers, scaled to player level
- Graceful fallback when AI unavailable

---

## Implementation Steps

### Step 1: Extend Enemy model
**File:** `src/cli_rpg/models/enemy.py`

Add optional fields:
```python
description: str = ""  # e.g., "A snarling beast with glowing red eyes"
attack_flavor: str = ""  # e.g., "lunges with razor-sharp claws"
```

Update `to_dict()` and `from_dict()` to serialize/deserialize these fields.

### Step 2: Add prompt template to AIConfig
**File:** `src/cli_rpg/ai_config.py`

Add `DEFAULT_ENEMY_GENERATION_PROMPT` constant and `enemy_generation_prompt` field to AIConfig dataclass:
```python
DEFAULT_ENEMY_GENERATION_PROMPT = """Generate an enemy for a {theme} RPG.
Location: {location_name}
Player Level: {player_level}
...
Respond with JSON: {{"name": "...", "description": "...", "attack_flavor": "...", "health": N, "attack_power": N, "defense": N, "xp_reward": N}}
"""
```

Update `to_dict()`, `from_dict()` to include the new prompt.

### Step 3: Add generate_enemy() to AIService
**File:** `src/cli_rpg/ai_service.py`

Add method:
```python
def generate_enemy(
    self,
    theme: str,
    location_name: str,
    player_level: int
) -> dict:
    """Generate an enemy with AI.

    Returns dict with: name, description, attack_flavor, health,
    attack_power, defense, xp_reward, level
    """
```

Add `_build_enemy_prompt()` and `_parse_enemy_response()` helper methods with validation similar to location generation.

### Step 4: Add ai_spawn_enemy() to combat.py
**File:** `src/cli_rpg/combat.py`

Add function that wraps AI generation with fallback:
```python
def ai_spawn_enemy(
    location_name: str,
    player_level: int,
    ai_service: Optional[AIService] = None,
    theme: str = "fantasy"
) -> Enemy:
    """Spawn enemy using AI generation with fallback to templates."""
```

### Step 5: Integrate into GameState.trigger_encounter()
**File:** `src/cli_rpg/game_state.py`

Modify `trigger_encounter()` to use `ai_spawn_enemy()` when `self.ai_service` is available, passing the theme and current location context.

### Step 6: Use attack_flavor in combat messages
**File:** `src/cli_rpg/combat.py`

Update `enemy_turn()` to use `enemy.attack_flavor` when available:
```python
if self.enemy.attack_flavor:
    message = f"{self.enemy.name} {self.enemy.attack_flavor}! You take {dmg} damage!"
else:
    message = f"{self.enemy.name} attacks you for {dmg} damage!"
```

---

## Test Plan

### Unit Tests (create `tests/test_ai_enemy_generation.py`)

1. **Enemy model tests:**
   - `test_enemy_description_serializes_correctly` - to_dict/from_dict includes description
   - `test_enemy_attack_flavor_serializes_correctly` - to_dict/from_dict includes attack_flavor
   - `test_enemy_default_description_empty` - description defaults to empty string

2. **AIConfig tests:**
   - `test_ai_config_has_enemy_prompt` - enemy_generation_prompt field exists
   - `test_ai_config_enemy_prompt_serialization` - to_dict/from_dict handles prompt

3. **AIService.generate_enemy() tests:**
   - `test_generate_enemy_returns_valid_structure` - Returns dict with all required fields
   - `test_generate_enemy_validates_name_length` - Rejects names <2 or >30 chars
   - `test_generate_enemy_validates_description_length` - Rejects descriptions <10 or >150 chars
   - `test_generate_enemy_validates_positive_stats` - Rejects negative health/attack/defense
   - `test_generate_enemy_uses_context` - Prompt includes location_name and player_level
   - `test_generate_enemy_handles_api_error` - Raises AIServiceError on failure

4. **ai_spawn_enemy() tests:**
   - `test_ai_spawn_enemy_uses_ai_service` - Calls AIService when provided
   - `test_ai_spawn_enemy_fallback_on_error` - Falls back to spawn_enemy() on AI failure
   - `test_ai_spawn_enemy_fallback_when_no_service` - Falls back when ai_service=None
   - `test_ai_spawn_enemy_returns_valid_enemy` - Returns Enemy instance with correct fields

5. **Combat integration tests:**
   - `test_enemy_turn_uses_attack_flavor` - Message includes attack_flavor when present
   - `test_enemy_turn_default_message_without_flavor` - Uses default message when no flavor

6. **GameState integration tests:**
   - `test_trigger_encounter_uses_ai_when_available` - Uses ai_spawn_enemy with service
   - `test_trigger_encounter_works_without_ai` - Works correctly without AI service
