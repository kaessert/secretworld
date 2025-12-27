# Implementation Plan: Quest World/Region Context Integration

## Objective
Integrate `WorldContext` and `RegionContext` into quest generation so AI-generated quests feel cohesive with the world rather than generic/disconnected.

## Spec

**Current behavior**: `generate_quest()` receives only `theme`, `npc_name`, `player_level`, and `location_name`. The prompt lacks world essence, naming style, tone, and region theme - producing generic quests.

**Target behavior**: Pass `world_context` and `region_context` to quest generation. The prompt includes:
- Theme essence (e.g., "dark supernatural horror with creeping dread")
- Region theme (e.g., "crumbling stone, forgotten history, decay")
- Region danger level (for reward scaling hints)

This mirrors the existing layered architecture used for location/NPC generation.

## Tests (write first)

### File: `tests/test_quest_context_integration.py`

1. **test_generate_quest_accepts_world_context** - `generate_quest()` accepts optional `world_context` param
2. **test_generate_quest_accepts_region_context** - `generate_quest()` accepts optional `region_context` param
3. **test_prompt_includes_theme_essence** - When `world_context` provided, prompt contains `theme_essence`
4. **test_prompt_includes_region_theme** - When `region_context` provided, prompt contains region `theme`
5. **test_prompt_includes_danger_level** - When `region_context` provided, prompt contains `danger_level`
6. **test_context_params_are_optional** - Quest generation works without context (backward compatible)
7. **test_main_passes_context_to_generate_quest** - Integration test: `main.py` passes both contexts to `generate_quest()`

## Implementation Steps

### Step 1: Update `DEFAULT_QUEST_GENERATION_PROMPT` in `ai_config.py`
Add world/region context section to prompt template:
```python
DEFAULT_QUEST_GENERATION_PROMPT = """Generate a quest for a {theme} RPG.

World Context:
- Theme Essence: {theme_essence}
- Tone: {tone}

Region Context:
- Region Theme: {region_theme}
- Danger Level: {danger_level}

NPC Quest Giver: {npc_name}
Location: {location_name}
Player Level: {player_level}
...
"""
```

### Step 2: Update `generate_quest()` signature in `ai_service.py`
Add optional parameters:
```python
def generate_quest(
    self,
    theme: str,
    npc_name: str,
    player_level: int,
    location_name: str = "",
    valid_locations: Optional[set[str]] = None,
    valid_npcs: Optional[set[str]] = None,
    world_context: Optional[WorldContext] = None,  # NEW
    region_context: Optional[RegionContext] = None  # NEW
) -> dict:
```

### Step 3: Update `_build_quest_prompt()` in `ai_service.py`
Extract context values with fallbacks:
```python
def _build_quest_prompt(
    self,
    theme: str,
    npc_name: str,
    player_level: int,
    location_name: str = "",
    world_context: Optional[WorldContext] = None,
    region_context: Optional[RegionContext] = None
) -> str:
    theme_essence = world_context.theme_essence if world_context else theme
    tone = world_context.tone if world_context else "adventurous"
    region_theme = region_context.theme if region_context else "unexplored lands"
    danger_level = region_context.danger_level if region_context else "moderate"

    return self.config.quest_generation_prompt.format(
        theme=theme,
        theme_essence=theme_essence,
        tone=tone,
        region_theme=region_theme,
        danger_level=danger_level,
        npc_name=npc_name,
        player_level=player_level,
        location_name=location_name or "unknown location"
    )
```

### Step 4: Update call site in `main.py`
Pass contexts from `game_state`:
```python
# Get world and region context
world_ctx = game_state.get_or_create_world_context()
current_loc = game_state.world.get(game_state.current_location)
region_ctx = None
if current_loc and current_loc.coordinates:
    region_ctx = game_state.get_or_create_region_context(current_loc.coordinates)

quest_data = game_state.ai_service.generate_quest(
    theme=game_state.theme,
    npc_name=npc.name,
    player_level=game_state.current_character.level,
    location_name=game_state.current_location,
    valid_locations=valid_locations,
    valid_npcs=valid_npcs,
    world_context=world_ctx,  # NEW
    region_context=region_ctx  # NEW
)
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli_rpg/ai_config.py` | Update `DEFAULT_QUEST_GENERATION_PROMPT` with context placeholders |
| `src/cli_rpg/ai_service.py` | Add `world_context`, `region_context` params to `generate_quest()` and `_build_quest_prompt()` |
| `src/cli_rpg/main.py` | Pass `world_context` and `region_context` to `generate_quest()` call |
| `tests/test_quest_context_integration.py` | NEW - 7 tests |
