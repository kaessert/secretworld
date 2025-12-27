# Terrain-Aware Random Encounters

## Summary
Make random encounters respect the current location's terrain type. Currently, `_handle_hostile_encounter` passes `location.category` to `spawn_enemy`, but Location also has a `terrain` field from WFC generation. This field should be preferred when present, with `category` as fallback, matching the pattern established by terrain-aware merchant shops.

## Spec
- Hostile random encounters should spawn enemies appropriate to the terrain
- Priority: `location.terrain` (WFC-generated) > `location.category` (semantic) > location name matching
- Terrain types (from `world_tiles.TerrainType`): forest, mountain, plains, water, desert, swamp, hills, beach, foothills
- Map terrains to existing ENEMY_TEMPLATES keys or add new templates as needed

## Changes

### 1. Extend ENEMY_TEMPLATES (combat.py, line ~33)
Add templates for terrains not yet covered:
```python
ENEMY_TEMPLATES = {
    "forest": ["Wolf", "Bear", "Wild Boar", "Giant Spider"],
    "cave": ["Bat", "Goblin", "Troll", "Cave Dweller"],
    "dungeon": ["Skeleton", "Zombie", "Ghost", "Dark Knight"],
    "mountain": ["Eagle", "Goat", "Mountain Lion", "Yeti"],
    "village": ["Bandit", "Thief", "Ruffian", "Outlaw"],
    # NEW terrain entries:
    "plains": ["Wild Dog", "Highwayman", "Giant Rat", "Roaming Boar"],
    "desert": ["Scorpion", "Sand Serpent", "Vulture", "Dust Bandit"],
    "swamp": ["Swamp Leech", "Marsh Troll", "Bog Hag", "Giant Frog"],
    "hills": ["Hill Giant", "Bandit Scout", "Wild Goat", "Hawk"],
    "beach": ["Giant Crab", "Sea Serpent", "Coastal Raider", "Seagull Swarm"],
    "foothills": ["Mountain Cat", "Rock Troll", "Foothill Bandit", "Wild Ram"],
    "default": ["Monster", "Creature", "Beast", "Fiend"]
}
```

### 2. Extend category_mappings in spawn_enemy (combat.py, line ~2176)
Add terrain type mappings:
```python
category_mappings = {
    # Existing semantic categories
    "wilderness": "forest",
    "ruins": "dungeon",
    "town": "village",
    "settlement": "village",
    # Direct matches (existing)
    "forest": "forest",
    "cave": "cave",
    "dungeon": "dungeon",
    "mountain": "mountain",
    "village": "village",
    # NEW terrain type mappings (direct matches)
    "plains": "plains",
    "desert": "desert",
    "swamp": "swamp",
    "hills": "hills",
    "beach": "beach",
    "foothills": "foothills",
    # Water is impassable, but include fallback
    "water": "beach",  # If somehow in water, beach-adjacent enemies
}
```

### 3. Update spawn_enemy signature (combat.py, line ~2156)
Add optional `terrain_type` parameter:
```python
def spawn_enemy(
    location_name: str,
    level: int,
    location_category: Optional[str] = None,
    terrain_type: Optional[str] = None,  # NEW
    distance: int = 0
) -> Enemy:
```

Update logic (after line ~2194):
```python
location_type = "default"

# Priority: terrain_type > location_category > name matching
if terrain_type and terrain_type.lower() in category_mappings:
    location_type = category_mappings[terrain_type.lower()]
elif location_category:
    location_type = category_mappings.get(location_category.lower(), "default")
else:
    # Fall back to name-based matching
    ...
```

### 4. Update _handle_hostile_encounter (random_encounters.py, line ~268)
Pass terrain to spawn_enemy:
```python
def _handle_hostile_encounter(game_state: "GameState") -> str:
    location = game_state.get_current_location()
    level = game_state.current_character.level

    enemy = spawn_enemy(
        location_name=location.name,
        level=level,
        location_category=location.category,
        terrain_type=location.terrain,  # NEW
    )
    ...
```

## Tests (tests/test_random_encounters.py)

### New test class: TestTerrainAwareEncounters
```python
class TestTerrainAwareEncounters:
    """Tests for terrain-aware random encounters."""

    @pytest.fixture
    def game_state_with_terrain(self, monkeypatch):
        """Create game state with terrain-typed location."""
        monkeypatch.setattr("cli_rpg.game_state.autosave", lambda gs: None)
        character = Character("Hero", strength=10, dexterity=10, intelligence=10)
        world = {
            "Desert": Location(
                "Sandy Wastes", "Hot desert",
                coordinates=(0, 0), terrain="desert"
            ),
        }
        return GameState(character, world, "Desert")

    def test_hostile_encounter_uses_terrain_for_enemy(self, game_state_with_terrain, monkeypatch):
        """Hostile encounters spawn terrain-appropriate enemies.

        Spec: When location.terrain is set, spawn_enemy should use it
        """
        # Mock to trigger hostile encounter
        random_values = [0.05, 0.30]
        mock_random = MagicMock(side_effect=random_values)
        monkeypatch.setattr("cli_rpg.random_encounters.random.random", mock_random)

        captured_args = {}
        def mock_spawn_enemy(location_name, level, location_category=None, terrain_type=None, distance=0):
            captured_args["terrain_type"] = terrain_type
            return Enemy(name="Scorpion", health=30, max_health=30, attack_power=5, defense=2, xp_reward=20)

        monkeypatch.setattr("cli_rpg.random_encounters.spawn_enemy", mock_spawn_enemy)
        check_for_random_encounter(game_state_with_terrain)

        assert captured_args.get("terrain_type") == "desert"

    def test_terrain_takes_priority_over_category(self, game_state_with_terrain, monkeypatch):
        """Terrain type should override location category.

        Spec: terrain_type > location_category in spawn_enemy
        """
        from cli_rpg.combat import spawn_enemy, ENEMY_TEMPLATES

        # Spawn with both terrain and category (terrain wins)
        enemy = spawn_enemy(
            location_name="Test",
            level=1,
            location_category="forest",
            terrain_type="desert",
        )
        # Desert enemies include Scorpion, Sand Serpent, etc. (not forest enemies)
        assert enemy.name in ENEMY_TEMPLATES["desert"]
```

### Update existing test
In `TestHostileEncounter.test_encounter_respects_location_category`, update mock to accept terrain_type:
```python
def mock_spawn_enemy(location_name, level, location_category=None, terrain_type=None, distance=0):
    captured_args["terrain_type"] = terrain_type
    ...
```

## Verification
Run tests:
```bash
pytest tests/test_random_encounters.py -v
pytest tests/test_combat.py -v -k spawn_enemy
```
