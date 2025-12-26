## Active Issues

---
---
---

# ⚠️⚠️⚠️ BLOCKING CRITICAL ⚠️⚠️⚠️
# SUB-LOCATION GRID SYSTEM & WFC OVERWORLD
# THIS IS THE MOST IMPORTANT ISSUE - DROP EVERYTHING ELSE

---
---
---

**Status**: 🚨 CRITICAL - MUST FIX IMMEDIATELY 🚨
**Priority**: P0 - BLOCKS ALL OTHER WORK
**Impact**: Game is fundamentally broken without this fix

> **ALL OTHER ISSUES IN THIS FILE ARE LOWER PRIORITY THAN THIS ONE.**
> **DO NOT WORK ON ANYTHING ELSE UNTIL THIS IS RESOLVED.**

---

## The Problem: Sub-locations are BROKEN

AI-generated areas place sub-locations on the SAME grid as overworld locations. This is a **fundamental architectural bug** in `ai_world.py:667-668`.

### What's happening:

```python
# ai_world.py line 667-668 - THE BUG
for name, data in placed_locations.items():
    world[name] = data["location"]  # ALL locations added to same grid!
```

### Observed symptoms:

1. **`worldmap` shows only ONE location** when player is in AI-generated world
2. **Sub-locations have grid coordinates** when they shouldn't
3. **Cardinal movement bypasses enter/exit** - players can `go north` between what should be interior rooms
4. **Complete confusion** between overworld and interior navigation

### Evidence from actual gameplay:

```
> wm
=== WORLD MAP ===
┌────────────────────────────────────────┐
│  6                █   @   █            │  ← ONLY ONE LOCATION!
└────────────────────────────────────────┘
Legend:
  @ = You (Waveswept Beach)    ← Where are all the other locations?!
  █ = Blocked/Wall
Exits: north, south

> m
=== MAP ===
┌────────────────────────────────────────┐
│  8                █   F   C   █        │
│  7                █   @   █            │  ← 7 LOCATIONS on same grid!
│  6                █   E   █            │
│  5                █   A   █            │
│  4                █   B   █            │
│  3                █   D   █            │
└────────────────────────────────────────┘
Legend:
  D = Sunken Shipwreck
  B = Kelp Forest
  A = Crystal Caverns         ← These should be INTERIOR locations!
  E = Waveswept Beach
  @ = You (Mistral Cliffs)    ← This is a SUB-LOCATION with coords!
  F = Whispering Coves
  C = Sunken Grotto

> exit
You exit to Waveswept Beach.
Enter: Mistral Cliffs, Whispering Coves, Sunken Grotto  ← They're sub-locations!
```

**This makes the game unplayable for exploration.**

---

## The Solution: Separate Sub-Location Grids

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         OVERWORLD GRID                              │
│   Infinite, expandable, uses WFC for terrain generation            │
│                                                                     │
│   ┌───────────┐     ┌───────────┐     ┌───────────┐                │
│   │  Forest   │─────│   Town    │─────│  Mountain │                │
│   │  (0, 1)   │     │  (0, 0)   │     │  (1, 0)   │                │
│   └─────┬─────┘     └─────┬─────┘     └─────┬─────┘                │
│         │                 │                 │                       │
│         │ enter           │ enter           │ enter                 │
│         ▼                 ▼                 ▼                       │
│   ┌───────────┐     ┌───────────┐     ┌───────────┐                │
│   │ SUB-GRID  │     │ SUB-GRID  │     │ SUB-GRID  │                │
│   │  Forest   │     │   Town    │     │   Cave    │                │
│   │ Interior  │     │ Interior  │     │ Interior  │                │
│   │           │     │           │     │           │                │
│   │ Bounded   │     │ Bounded   │     │ Bounded   │                │
│   │ Finite    │     │ Finite    │     │ Finite    │                │
│   │ Own (0,0) │     │ Own (0,0) │     │ Own (0,0) │                │
│   └───────────┘     └───────────┘     └───────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sub-location coordinates | Own (0,0) system | Entry point at origin, not polluting overworld |
| Sub-location size | Finite, bounded | Not infinite like overworld - dungeons have walls |
| Exit mechanism | Specific exit rooms | Only `is_exit_point=True` rooms allow `exit` command |
| Map display | Context-aware | `map` shows current grid (overworld OR interior) |
| Overworld display | Always available | `worldmap` always shows overworld, even from inside |
| Overworld generation | Wave Function Collapse | Coherent terrain, infinite expansion via chunks |

---

## Implementation Plan

### Part 1: SubGrid Class (`src/cli_rpg/world_grid.py`)

Create a new `SubGrid` dataclass for bounded interior grids:

```python
@dataclass
class SubGrid:
    """Bounded grid for sub-location interiors.

    Unlike WorldGrid which is infinite, SubGrid has defined bounds.
    Entry is always at (0, 0).
    """

    _grid: Dict[Tuple[int, int], Location] = field(default_factory=dict)
    _by_name: Dict[str, Location] = field(default_factory=dict)
    bounds: Tuple[int, int, int, int] = (-2, 2, -2, 2)  # 5x5 default
    parent_name: str = ""

    def add_location(self, location: Location, x: int, y: int) -> None:
        """Add location within bounds. Raises ValueError if outside."""
        min_x, max_x, min_y, max_y = self.bounds
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            raise ValueError(f"Coordinates ({x}, {y}) outside bounds {self.bounds}")

        location.coordinates = (x, y)
        location.parent_location = self.parent_name
        self._grid[(x, y)] = location
        self._by_name[location.name] = location
        self._create_connections(location, x, y)

    def get_by_coordinates(self, x: int, y: int) -> Optional[Location]
    def get_by_name(self, name: str) -> Optional[Location]
    def is_within_bounds(self, x: int, y: int) -> bool
    def to_dict(self) -> dict  # Serialization
    def from_dict(cls, data: dict) -> "SubGrid"  # Deserialization
```

### Part 2: Location Model Updates (`src/cli_rpg/models/location.py`)

Add two new fields:

```python
@dataclass
class Location:
    # ... existing fields ...

    # NEW: Exit point marker
    is_exit_point: bool = False  # Only these rooms allow 'exit' command

    # NEW: Interior grid for landmarks
    sub_grid: Optional["SubGrid"] = None  # Interior grid (overworld only)
```

Update `to_dict()` and `from_dict()` for serialization.

### Part 3: GameState Updates (`src/cli_rpg/game_state.py`)

Add sub-location tracking:

```python
class GameState:
    def __init__(self, ...):
        # ... existing init ...
        self.in_sub_location: bool = False
        self.current_sub_grid: Optional[SubGrid] = None
```

Update navigation methods:

**`enter()` method (~line 665)**:
```python
def enter(self, target_name: Optional[str] = None) -> tuple[bool, str]:
    current = self.get_current_location()

    if current.sub_grid is not None:
        # Use sub_grid-based entry
        self.in_sub_location = True
        self.current_sub_grid = current.sub_grid

        # Entry point is at (0, 0) or use target_name
        if target_name:
            entry_loc = current.sub_grid.get_by_name(target_name)
        else:
            entry_loc = current.sub_grid.get_by_coordinates(0, 0)

        self.current_location = entry_loc.name
        # ... boss encounter check, etc.
```

**`exit_location()` method (~line 734)**:
```python
def exit_location(self) -> tuple[bool, str]:
    current = self.get_current_location()

    # CHECK: Must be at an exit point!
    if self.in_sub_location and not current.is_exit_point:
        return (False, "You cannot exit from here. Find an exit point.")

    self.current_location = current.parent_location
    self.in_sub_location = False
    self.current_sub_grid = None
```

**`move()` method (~line 426)**:
```python
def move(self, direction: str) -> tuple[bool, str]:
    current = self.get_current_location()

    # Handle movement inside sub-location grid
    if self.in_sub_location and self.current_sub_grid is not None:
        return self._move_in_sub_grid(direction, current)

    # ... existing overworld movement ...
```

### Part 4: Map Renderer Updates (`src/cli_rpg/map_renderer.py`)

Add interior map rendering:

```python
def render_map(
    world: dict[str, Location],
    current_location: str,
    sub_grid: Optional["SubGrid"] = None  # NEW parameter
) -> str:
    if sub_grid is not None:
        return _render_sub_grid_map(sub_grid, current_location)
    # ... existing overworld rendering ...

def _render_sub_grid_map(sub_grid: "SubGrid", current_location: str) -> str:
    """Render bounded interior map with exit markers."""
    # Header: "=== INTERIOR MAP ==="
    # Show bounded grid with E markers for exit points
    # Legend includes exit point indicator
```

### Part 5: Fix AI World Generation (`src/cli_rpg/ai_world.py`)

**FIX `expand_area()` (~line 472)**:

```python
def expand_area(...):
    # Generate the area
    area_data = ai_service.generate_area(...)

    # Create SubGrid for interior - NOT on overworld!
    sub_grid = SubGrid()
    sub_grid.parent_name = from_location
    sub_grid.bounds = (-3, 3, -3, 3)  # 7x7 for dungeons

    for loc_data in area_data:
        rel_x, rel_y = loc_data["relative_coords"]
        is_entry = (rel_x == 0 and rel_y == 0)

        if is_entry:
            # Entry location goes on OVERWORLD at target_coords
            entry_loc = Location(...)
            entry_loc.is_exit_point = True
            world[entry_loc.name] = entry_loc  # Only entry on overworld!
        else:
            # Interior locations go in sub_grid ONLY
            interior_loc = Location(...)
            interior_loc.is_exit_point = False
            sub_grid.add_location(interior_loc, rel_x, rel_y)

    # Attach sub_grid to entry
    entry_loc.sub_grid = sub_grid
```

### Part 6: Convert Default World (`src/cli_rpg/world.py`)

Convert existing sub-locations to use SubGrid:

```python
# Town Square interior
town_square_grid = SubGrid()
town_square_grid.parent_name = "Town Square"
town_square_grid.bounds = (-1, 1, -1, 1)  # 3x3

market_district = Location(name="Market District", ..., is_exit_point=True)
town_square_grid.add_location(market_district, 0, 0)

guard_post = Location(name="Guard Post", ..., is_exit_point=False)
town_square_grid.add_location(guard_post, 1, 0)

town_well = Location(name="Town Well", ..., is_exit_point=True)
town_square_grid.add_location(town_well, 0, 1)

town_square.sub_grid = town_square_grid
```

---

## Part 2: Wave Function Collapse Overworld

### New Files to Create

| File | Purpose |
|------|---------|
| `src/cli_rpg/wfc.py` | Core WFC algorithm |
| `src/cli_rpg/world_tiles.py` | Tile definitions and adjacency rules |
| `src/cli_rpg/wfc_chunks.py` | Chunk manager for infinite world |

### Tile Definitions (`world_tiles.py`)

```python
TERRAIN_TYPES = [
    "forest", "mountain", "plains", "water",
    "desert", "swamp", "hills", "beach", "foothills"
]

ADJACENCY_RULES = {
    "forest": {"forest", "plains", "hills", "swamp"},
    "mountain": {"mountain", "hills", "foothills"},
    "plains": {"plains", "forest", "hills", "desert", "beach"},
    "water": {"water", "beach", "swamp"},
    "desert": {"desert", "plains", "hills"},
    "swamp": {"swamp", "forest", "water"},
    "hills": {"hills", "forest", "plains", "mountain", "foothills"},
    "beach": {"beach", "water", "plains", "forest"},
    "foothills": {"foothills", "hills", "mountain", "plains"},
}

TERRAIN_TO_LOCATIONS = {
    "forest": ["ruins", "grove", "hermit_hut", "bandit_camp"],
    "mountain": ["cave", "mine", "peak", "monastery"],
    "plains": ["village", "farm", "crossroads", "tower"],
    "water": [],  # Impassable
    "desert": ["oasis", "tomb", "abandoned_outpost"],
    "swamp": ["witch_hut", "sunken_ruins", "fishing_village"],
    "hills": ["watchtower", "shepherd_camp", "ancient_stones"],
    "beach": ["dock", "shipwreck", "lighthouse"],
    "foothills": ["pass", "inn", "mining_camp"],
}
```

### WFC Algorithm (`wfc.py`)

```python
@dataclass
class WFCCell:
    coords: Tuple[int, int]
    possible_tiles: Set[str]  # Starts with ALL tiles
    collapsed: bool = False
    tile: Optional[str] = None

class WFCGenerator:
    def __init__(self, tile_registry: TileRegistry, seed: int):
        self.tiles = tile_registry
        self.rng = random.Random(seed)

    def generate_chunk(self, origin: Tuple[int, int]) -> Dict[Tuple[int,int], str]:
        """Generate 8x8 chunk of terrain tiles."""
        # 1. Initialize all cells with all possible tiles
        # 2. While uncollapsed cells exist:
        #    a. Find cell with minimum entropy (fewest options)
        #    b. Collapse it (pick random tile weighted by frequency)
        #    c. Propagate constraints to neighbors
        #    d. If contradiction, backtrack or restart
        # 3. Return collapsed grid

    def _calculate_entropy(self, cell: WFCCell) -> float:
        """Shannon entropy for cell selection."""

    def _collapse_cell(self, cell: WFCCell) -> str:
        """Pick tile from possibilities using weighted random."""

    def _propagate(self, chunk, collapsed_cell) -> bool:
        """Remove invalid options from neighbors. Returns False on contradiction."""
```

### Chunk Manager (`wfc_chunks.py`)

```python
@dataclass
class ChunkManager:
    chunk_size: int = 8  # 8x8 tiles per chunk
    chunks: Dict[Tuple[int, int], Dict] = field(default_factory=dict)
    generator: WFCGenerator = None
    world_seed: int = 0

    def get_or_generate_chunk(self, chunk_x: int, chunk_y: int) -> Dict:
        """Get cached chunk or generate new one."""
        key = (chunk_x, chunk_y)
        if key not in self.chunks:
            # Derive deterministic seed from world seed + chunk coords
            chunk_seed = hash((self.world_seed, chunk_x, chunk_y)) & 0xFFFFFFFF
            self.chunks[key] = self.generator.generate_chunk(key)
        return self.chunks[key]

    def get_tile_at(self, world_x: int, world_y: int) -> str:
        """Get terrain tile at world coordinates."""
        chunk_x = world_x // self.chunk_size
        chunk_y = world_y // self.chunk_size
        local_x = world_x % self.chunk_size
        local_y = world_y % self.chunk_size
        chunk = self.get_or_generate_chunk(chunk_x, chunk_y)
        return chunk[(local_x, local_y)]

    def _apply_boundary_constraints(self, new_chunk, neighbors):
        """Constrain edge cells based on adjacent chunks."""
```

---

## Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `src/cli_rpg/world_grid.py` | MODIFY | Add `SubGrid` class |
| `src/cli_rpg/models/location.py` | MODIFY | Add `sub_grid`, `is_exit_point` fields |
| `src/cli_rpg/game_state.py` | MODIFY | Track sub-location state, update navigation |
| `src/cli_rpg/map_renderer.py` | MODIFY | Add interior map rendering |
| `src/cli_rpg/ai_world.py` | MODIFY | Fix `expand_area()` to use SubGrid |
| `src/cli_rpg/world.py` | MODIFY | Convert default world to use SubGrid |
| `src/cli_rpg/persistence.py` | MODIFY | Serialize SubGrid and WFC state |
| `src/cli_rpg/wfc.py` | ✅ CREATED | Core WFC algorithm |
| `src/cli_rpg/world_tiles.py` | ✅ CREATED | Tile definitions and adjacency rules |
| `src/cli_rpg/wfc_chunks.py` | ✅ CREATED | Chunk manager for infinite world |
| `tests/test_sub_grid.py` | ✅ CREATED | SubGrid unit tests |
| `tests/test_exit_points.py` | CREATE | Exit command restriction tests |
| `tests/test_wfc.py` | ✅ CREATED | WFC algorithm tests |
| `tests/test_wfc_chunks.py` | ✅ CREATED | Chunk boundary tests |
| `tests/test_wfc_integration.py` | CREATE | Full integration tests |

---

## Implementation Order

### Phase 1: Sub-Location Grids (PRIORITY - fixes the bug)

1. ✅ Create `SubGrid` class in `world_grid.py` - **DONE** (90 lines, 23 tests)
2. ✅ Add `is_exit_point` and `sub_grid` to Location model - **DONE** (16 tests in `tests/test_exit_points.py`)
3. ✅ Update GameState `enter()`, `exit_location()`, `move()`, `get_current_location()` - **DONE** (21 tests in `tests/test_subgrid_navigation.py`)
4. ✅ Update map renderer for interior maps - **DONE** (12 tests in `tests/test_map_renderer.py::TestSubGridMapRendering`)
5. ✅ Fix `ai_world.py` `expand_area()` to use SubGrid - **DONE** (11 tests in `tests/test_ai_world_subgrid.py`)
6. ✅ Convert default world sub-locations to use SubGrid - **DONE** (34 tests in `tests/test_default_world_subgrid.py`)
7. ✅ SubGrid persistence serialization - **DONE** (6 tests in `tests/test_persistence_game_state.py::TestSubGridPersistence`)
8. Write tests

### Phase 2: WFC Overworld (Enhancement)

1. ✅ Create `wfc.py` with core algorithm - **DONE** (WFCCell dataclass, WFCGenerator class with Shannon entropy, weighted tile selection, constraint propagation, contradiction recovery)
2. ✅ Create `world_tiles.py` with tile/adjacency definitions - **DONE** (TileRegistry with 9 terrain types, ADJACENCY_RULES, terrain weights)
3. ✅ Create `wfc_chunks.py` with chunk manager - **DONE** (ChunkManager class with deterministic seeding, boundary constraint propagation, serialization)
4. ✅ Integrate with GameState movement - **DONE** (GameState.move() checks terrain passability, generates fallback locations with terrain type)
5. ✅ Add terrain-aware location generation - **DONE** (TERRAIN_TEMPLATES in world.py, generate_fallback_location() accepts terrain param)
6. ✅ Add persistence for WFC state - **DONE** (ChunkManager.to_dict()/from_dict(), GameState serialization includes chunk_manager)
7. ✅ Add `--wfc` flag for optional enablement - **DONE** (main.py --wfc flag, wired through use_wfc parameter)
8. ✅ Write tests - **DONE** (17 tests in `tests/test_wfc.py`, 17 tests in `tests/test_wfc_chunks.py`, 10 tests in `tests/test_wfc_integration.py`)

---

## Tests to Create

### `tests/test_sub_grid.py` ✅ CREATED (23 tests)
- ✅ SubGrid creation with bounds
- ✅ Adding locations within bounds
- ✅ Rejecting locations outside bounds
- ✅ Bidirectional connections created
- ✅ Serialization/deserialization
- ✅ Entry point at (0, 0)

### `tests/test_exit_points.py` ✅ CREATED (16 tests)
- ✅ Default value for `is_exit_point` field
- ✅ Setting `is_exit_point=True` value
- ✅ `is_exit_point` serialization/deserialization
- ✅ Default value for `sub_grid` field
- ✅ Setting `sub_grid` with SubGrid instance
- ✅ `sub_grid` serialization/deserialization
- ✅ Backward compatibility (old saves without new fields)
- ✅ Round-trip serialization preserves all data

### `tests/test_ai_world_subgrid.py` ✅ CREATED (11 tests)
- ✅ Entry location has sub_grid attached
- ✅ Sub-locations not in world dict
- ✅ Sub-locations accessible via SubGrid
- ✅ Entry marked as exit point
- ✅ First sub-location marked as exit point
- ✅ Relative coordinates preserved in SubGrid placement

### `tests/test_wfc.py` ✅ CREATED (17 tests)
- ✅ WFCCell dataclass creation and defaults
- ✅ WFCGenerator initialization and deterministic seeding
- ✅ Shannon entropy calculation (single and multiple options)
- ✅ Minimum entropy cell selection
- ✅ Cell collapse with weighted random selection
- ✅ Constraint propagation with chain reactions
- ✅ Contradiction detection
- ✅ Full chunk generation with adjacency validation
- ✅ Contradiction handling/recovery

### `tests/test_wfc_chunks.py` ✅ CREATED (17 tests)
- ✅ ChunkManager creation and initialization
- ✅ Deterministic chunk generation from seed
- ✅ Chunk caching works correctly
- ✅ Coordinate conversion (positive/negative)
- ✅ Boundary constraint propagation (horizontal and vertical)
- ✅ Large area traversal (21x21 area across 9 chunks)
- ✅ Serialization/deserialization

### `tests/test_wfc_integration.py` ✅ CREATED (10 tests)
- ✅ GameState with/without chunk_manager initialization
- ✅ Move triggers chunk generation
- ✅ Terrain stored on location
- ✅ Water blocks movement with impassable message
- ✅ Fallback uses terrain type for location theming
- ✅ Location category derived from terrain type
- ✅ Save includes chunk_manager data
- ✅ Load restores chunk_manager state
- ✅ Load without chunk_manager works (backward compatibility)

### Known WFC Issue: Chunk Boundary Adjacency

**Status**: LOW PRIORITY (does not affect gameplay)

**Problem**: `test_wfc_chunks.py::test_large_area_traversal` occasionally fails due to inconsistent adjacency across chunk boundaries. The WFC boundary constraint algorithm sometimes produces terrain that violates adjacency rules at chunk seams.

**Impact**: Minor visual inconsistency in terrain generation (e.g., water next to volcanic without transition). Does not affect movement blocking or gameplay mechanics.

**Note**: This is a pre-existing algorithmic issue with the WFC boundary constraint propagation, not related to the GameState integration.

---
---
---

### AI Location Generation Failures - JSON Parsing & Token Limits
**Status**: HIGH PRIORITY

**Problem**: AI location generation frequently fails with JSON parsing errors:

```
Failed to generate location: Failed to parse response as JSON: Expecting ',' delimiter: line 13 column 7 (char 474)
Failed to generate location: Failed to parse response as JSON: Expecting ',' delimiter: line 13 column 7 (char 502)
```

This causes world generation to fall back to templates, breaking immersion and AI-generated coherence.

**Root Causes to Investigate**:

1. **Token limits too restrictive**: Complex prompts with context may exceed response token budget
2. **Prompts too large**: Single prompts try to generate too much at once (location + NPCs + connections + description)
3. **No JSON validation/repair**: Truncated or malformed JSON crashes instead of recovering

**Proposed Solution: Layered Query Architecture**

Instead of one monolithic prompt, use a hierarchical generation system:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: World Context (cached, reused)                    │
│  ─────────────────────────────────────────────────────────  │
│  • Theme essence: "cyberpunk noir with neon-lit streets"    │
│  • Naming conventions: "Tech-inspired, Japanese influence"  │
│  • Tone: "Gritty, mysterious, morally ambiguous"            │
│  • Generated ONCE at world creation, stored in game state   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: Region Context (per area cluster)                 │
│  ─────────────────────────────────────────────────────────  │
│  • Region theme: "Industrial district, factory smoke"       │
│  • Danger level: "Moderate - gang territory"                │
│  • Key landmarks: ["Rust Tower", "The Vats"]                │
│  • Generated when entering new region, cached per region    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: Location Details (per location, small prompt)     │
│  ─────────────────────────────────────────────────────────  │
│  INPUT: World context + Region context + direction          │
│  OUTPUT: Just { name, description, category, connections }  │
│  • Small, focused prompt = reliable JSON                    │
│  • No NPCs in this query (separate layer)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: NPC Generation (optional, per location)           │
│  ─────────────────────────────────────────────────────────  │
│  INPUT: Location name + description + region context        │
│  OUTPUT: Just { npcs: [{name, description, role}] }         │
│  • Only called for locations that should have NPCs          │
│  • Separate small prompt = reliable JSON                    │
└─────────────────────────────────────────────────────────────┘
```

**Benefits of Layered Approach**:

| Benefit | Description |
|---------|-------------|
| **Smaller prompts** | Each layer generates less = fits in token budget |
| **Better coherence** | World/region context ensures consistency |
| **Faster generation** | Layer 1-2 cached, only Layer 3-4 called per location |
| **Easier debugging** | Know exactly which layer failed |
| **Graceful degradation** | If NPC layer fails, location still works |

**Implementation Steps**:

1. **Audit current prompts** (`ai_config.py`):
   - Measure token counts for each prompt type
   - Identify which prompts are too large
   - Document current `max_tokens` settings vs actual needs

2. **Add JSON repair utilities** (`ai_service.py`):
   - Extract JSON from markdown code blocks
   - Attempt to close truncated arrays/objects
   - Validate against expected schema before use

3. **Create WorldContext model** (`models/world_context.py`):
   ```python
   @dataclass
   class WorldContext:
       theme: str
       theme_essence: str  # AI-generated theme summary
       naming_style: str   # How to name things
       tone: str           # Narrative tone
       generated_at: datetime
   ```

4. **Create RegionContext model** (`models/region_context.py`):
   ```python
   @dataclass
   class RegionContext:
       name: str
       theme: str          # Sub-theme for this region
       danger_level: str   # safe/moderate/dangerous
       landmarks: list[str]
       parent_world: str
   ```

5. **Split generation prompts** (`ai_config.py`):
   - `WORLD_CONTEXT_PROMPT`: Generate theme essence (once)
   - `REGION_CONTEXT_PROMPT`: Generate region details (per area)
   - `LOCATION_PROMPT_MINIMAL`: Just name/desc/category (per location)
   - `NPC_PROMPT_MINIMAL`: Just NPC list (optional per location)

6. **Update AIService** (`ai_service.py`):
   - Add `generate_world_context()` method
   - Add `generate_region_context()` method
   - Refactor `generate_location()` to use layered contexts
   - Add `generate_npcs_for_location()` as separate call

7. **Cache contexts in GameState**:
   - Store WorldContext at game creation
   - Store RegionContexts as player explores
   - Pass relevant context to generation calls

**Files to modify**:
- `src/cli_rpg/ai_config.py`: Split prompts, adjust token limits
- `src/cli_rpg/ai_service.py`: Add layered generation methods, JSON repair
- `src/cli_rpg/models/world_context.py`: NEW - WorldContext model
- `src/cli_rpg/models/region_context.py`: NEW - RegionContext model
- `src/cli_rpg/game_state.py`: Cache contexts, pass to generation
- `src/cli_rpg/ai_world.py`: Use layered generation

**Quick Wins (do first)**:
1. Increase `max_tokens` for location generation (current: 2000, try: 3000)
2. Add JSON extraction from markdown code blocks
3. Add try/except with JSON repair for truncated responses
4. Log full AI responses on parse failure for debugging

---

### AI Area Generation - Coordinates Outside SubGrid Bounds
**Status**: HIGH PRIORITY

**Problem**: AI area generation fails when generated locations have coordinates outside SubGrid bounds:

```
AI area generation failed: Coordinates (0, 4) outside bounds (-3, 3, -3, 3)
```

The SubGrid has bounds of (-3, 3, -3, 3) = 7x7 grid, but AI is generating locations at y=4 which is outside.

**Root Cause**:

In `ai_world.py:expand_area()`, the AI generates relative coordinates for sub-locations, but:
1. The prompt doesn't specify coordinate bounds to the AI
2. SubGrid enforces bounds strictly, causing placement to fail
3. One failed placement crashes the entire area generation

**Current Code** (`ai_world.py`):
```python
sub_grid.bounds = (-3, 3, -3, 3)  # 7x7 grid

for loc_data in area_data:
    rel_x, rel_y = loc_data["relative_coords"]
    # AI might return (0, 4) which is outside bounds!
    sub_grid.add_location(interior_loc, rel_x, rel_y)  # CRASH
```

**Fix Options**:

1. **Clamp coordinates to bounds** (quick fix):
   ```python
   min_x, max_x, min_y, max_y = sub_grid.bounds
   rel_x = max(min_x, min(max_x, rel_x))  # Clamp to bounds
   rel_y = max(min_y, min(max_y, rel_y))
   ```

2. **Expand bounds dynamically** (flexible):
   ```python
   # Auto-expand bounds to fit all locations
   sub_grid.expand_bounds_to_fit(rel_x, rel_y)
   ```

3. **Skip out-of-bounds locations** (graceful degradation):
   ```python
   if not sub_grid.is_within_bounds(rel_x, rel_y):
       logger.warning(f"Skipping {loc_data['name']}: coords ({rel_x}, {rel_y}) outside bounds")
       continue
   ```

4. **Update AI prompt** (proper fix):
   - Tell AI the coordinate bounds in the prompt
   - Request coordinates within (-3, 3) range
   - Add to `DEFAULT_AREA_GENERATION_PROMPT` in `ai_config.py`

**Recommended Approach**: Combine options 3 and 4:
- Update prompt to specify bounds (reduces failures)
- Skip out-of-bounds as fallback (handles edge cases)
- Log warnings for debugging

**Files to modify**:
- `src/cli_rpg/ai_world.py`: Add bounds checking/clamping in `expand_area()`
- `src/cli_rpg/ai_config.py`: Update area generation prompt with coordinate constraints

---

### VISION: Transformative Features for a Mesmerizing Experience
**Status**: ACTIVE (VISION)

These features would elevate the game from "good CLI RPG" to "unforgettable experience":

---

#### 1. THE WHISPER SYSTEM - Ambient Narrative Layer
**Impact**: Creates atmosphere and wonder
**Status**: MVP IMPLEMENTED

The world *speaks* to observant players through subtle environmental cues:

```
You enter the Forgotten Chapel...

    ╔═══════════════════════════════════╗
    ║  The candles flicker as you enter ║
    ║  ...almost as if greeting you     ║
    ╚═══════════════════════════════════╝

[Whisper]: "The stones here remember a prayer never finished..."
```

**MVP Implemented**:
- ✅ **Ambient whispers** appear randomly (30% chance) when entering locations
- ✅ **Category-based whispers**: Themed text based on location type (town, dungeon, wilderness, ruins, cave, forest)
- ✅ **Player-specific**: Whispers reference player history (high gold, high level, low health, many kills)
- ✅ No whispers during combat

**Future Enhancements**:
- **Hidden lore fragments** revealed to players who `look` multiple times or `wait`
- **Foreshadowing**: Whispers hint at dangers ahead, secrets nearby, or story beats
- ✅ **AI-generated whispers**: Dynamic whisper content via AI service - MVP IMPLEMENTED (context-aware whispers generated using world theme and location category; graceful fallback to template whispers on error)

---

#### 2. ECHO CHOICES - Decisions That Haunt You
**Impact**: Emotional weight, replayability
**Status**: MVP IMPLEMENTED

Every significant choice creates an "echo" that reverberates through the game:

```
The wounded bandit begs for mercy...

  [1] Spare him     - "Perhaps redemption exists for all"
  [2] Execute him   - "Justice must be swift"
  [3] Recruit him   - "Every sword has its use"

Your choice will echo...
```

**MVP Implemented**:
- ✅ **Reputation tracking**: Player choices (fleeing combat, killing enemies) are tracked in `game_state.choices`
- ✅ **NPC reputation awareness**: NPCs reference player's "cautious" reputation (3+ flees) or "aggressive" reputation (10+ kills)
- ✅ Reputation-aware greetings with 3 variants each for "cautious" and "aggressive" players

**Future Enhancements**:
- Spare the bandit → He becomes an informant, or betrays you later, or saves you in Act 3
- A town you helped prospers; one you ignored falls to ruin (visible on return)
- NPCs reference your reputation: "You're the one who burned the witch... or was it saved her?"
- **Companion memories**: "I still remember what you did in Thornwood. I've never forgotten."

---

#### 3. THE DARKNESS METER - Psychological Horror Element
**Impact**: Tension, resource management, atmosphere
**Status**: MVP IMPLEMENTED

Exploring dangerous areas builds **Dread**:

```
═══════════════════════════════════════
  DREAD: ████████░░░░░░░░ 53%

  The shadows seem to lean toward you...
  You hear footsteps that aren't your own.
═══════════════════════════════════════
```

**MVP Implemented**:
- ✅ **DreadMeter model** with 0-100% tracking and visual bar display
- ✅ **Dread triggers**: Dungeons (+15), caves (+12), ruins (+10), wilderness (+5), forest (+3), night movement (+5 bonus), low health (+5), combat (+10)
- ✅ **Dread reduction**: Towns (-15), resting (-20), talking to NPCs (-5)
- ✅ **Milestone messages**: At 25%, 50%, 75%, and 100% thresholds
- ✅ **High dread effects**: Paranoid whispers at 50%+, -10% attack penalty at 75%+
- ✅ **Status display**: Dread meter shown in `status` command
- ✅ **Persistence**: Dread saved/loaded with game state (backward compatible)

**Future Enhancements**:
- ✅ **At 100%**: Shadow creature attacks - MVP IMPLEMENTED (Shadow of Dread manifests and attacks; defeating it reduces dread by 50%)
- ✅ **Hallucinations**: Fake enemies at high dread - MVP IMPLEMENTED (At 75-99% dread, 30% chance per move to encounter spectral enemies that dissipate when attacked, reducing dread by 5 with no XP/loot rewards)
- ✅ **Light sources**: Items that reduce dread buildup - MVP IMPLEMENTED (Torches reduce dread buildup by 50%, negate night bonus, consumable with limited duration)
- ✅ **Brave player rewards**: Best secrets in high-dread areas - MVP IMPLEMENTED (Dread Treasures: 30% chance to discover powerful items when looking at 75%+ dread; includes Shadow Essence, Veil of Courage, Dread Blade, Darklight Torch)

---

#### 4. LIVING WORLD EVENTS - The World Moves Without You
**Impact**: Immersion, urgency, emergent stories
**Status**: MVP IMPLEMENTED

The world has a heartbeat. Events happen whether you're there or not:

```
╔════════════════════════════════════════════╗
║  WORLD EVENT: The Crimson Plague spreads   ║
║                                            ║
║  Millbrook Village is infected.            ║
║  Estimated time until collapse: 3 days     ║
║                                            ║
║  [Rumor]: An herbalist in Shadowfen knows  ║
║           of a cure...                     ║
╚════════════════════════════════════════════╝
```

**MVP Implemented**:
- ✅ **WorldEvent model** with event types, affected locations, duration, and time tracking
- ✅ **Event types**: Caravan, plague, and invasion events with unique consequences
- ✅ **Timed events**: Events have duration and expire after a set number of game hours
- ✅ **Event spawn**: 5% chance to spawn a new event on each move (max 3 active)
- ✅ **Consequences**: Expired events apply negative effects (health loss, gold loss, dread increase)
- ✅ **Location warnings**: Players warned when entering affected locations
- ✅ **`events` command**: View all active events with time remaining
- ✅ **Persistence**: Events saved/loaded with game state

**Future Enhancements**:
- **Spreading events**: Plagues, wars, monster migrations, seasons changing
- **Cascading effects**: Saved village → thriving trade → better shop inventory
- **Rival adventurers**: NPCs who complete quests you ignore, becoming allies or enemies
- ✅ **Event resolution**: Player actions to resolve events before they expire - MVP IMPLEMENTED (`resolve` command for plagues/invasions, auto-resolution for caravans on purchase; cure items drop from loot)

---

#### 5. DREAM SEQUENCES - Surreal Narrative Moments
**Impact**: Storytelling, foreshadowing, emotional depth
**Status**: MVP IMPLEMENTED

When you rest, sometimes you dream:

```
You drift into an uneasy sleep...

    ═══════════════════════════════════

    You stand in a field of white flowers.
    A child's voice asks: "Why did you
    choose the sword over the words?"

    A mountain crumbles in the distance.
    You recognize it as a place you've
    never been...

    ═══════════════════════════════════

You wake with a strange sense of purpose.
[Gained insight: "The Mountain's Secret"]
```

**MVP Implemented**:
- ✅ **25% trigger rate** on rest command
- ✅ **Prophetic dreams** hint at future events and locations
- ✅ **Atmospheric dreams** with surreal mood-setting content
- ✅ **Nightmare sequences** at 50%+ dread (psychological horror)
- ✅ **Choice-based personalization**: Dreams reflect player behavior (3+ flees → flee-themed, 10+ kills → combat-themed)
- ✅ **Formatted output** with decorative borders and intro/outro text

**Future Enhancements**:
- **Memory dreams** replay key moments with new perspective
- **Character dreams** reveal companion backstories
- **Dream items** that manifest in reality
- ✅ **AI-generated dreams** for dynamic content - MVP IMPLEMENTED (AI generates context-aware dreams based on theme, dread level, player choices, and location; graceful fallback to template dreams on error)

---

#### 6. COMBO COMBAT SYSTEM - Fluid, Strategic Fighting
**Impact**: Combat depth, mastery satisfaction
**Status**: MVP IMPLEMENTED

Chain attacks for devastating effects:

```
Combat Round 3:

  Your last 2 actions: [ATTACK] → [DEFEND]

  COMBO AVAILABLE: "Counter Strike"
    → On next attack, deal 2x damage if enemy attacked you

  What will you do?
  > [A]ttack (triggers Counter Strike!)
  > [D]efend (breaks combo)
  > [C]ast   (chains to "Arcane Counter")
```

**MVP Implemented**:
- ✅ **Action history tracking**: Last 3 player actions tracked and displayed in combat status
- ✅ **Frenzy combo** (Attack→Attack→Attack): Triple hit dealing ~1.5x total damage
- ✅ **Revenge combo** (Defend→Defend→Attack): Counter-attack dealing damage equal to damage taken while defending
- ✅ **Arcane Burst combo** (Cast→Cast→Cast): Empowered spell dealing 2x magic damage
- ✅ **Combo notifications**: "COMBO AVAILABLE" message when pattern is ready
- ✅ **Flee breaks chain**: Attempting to flee clears action history

**Future Enhancements**:
- **Hybrid moves**: Defend→Cast→Attack = "Calculated Strike" (guaranteed crit)
- **Enemy patterns**: Bosses telegraph moves, allowing counter-play
- **More combos**: Additional combo patterns for variety

---

#### 7. THE BOND SYSTEM - Companions Who Matter
**Impact**: Emotional investment, tactical depth
**Status**: MVP IMPLEMENTED

Companions aren't just stat bonuses—they're people:

```
KIRA THE SCOUT
  ════════════════════════════════════
  Bond Level: ████████░░ Trusted

  "I've been watching you. You fight like
   someone who's lost things. I know that
   feeling."

  [Memory]: She opened up about her sister
  [Memory]: You chose mercy when she wanted blood
  [Memory]: She saved you in the Shadow Caves
  ════════════════════════════════════

  Bond Ability: "Flanking Strike" (unlocked at Trust)
  Next unlock at "Devoted": "Last Stand"
```

**MVP Implemented**:
- ✅ **Companion model** with name, description, recruitment location, and bond points (0-100)
- ✅ **BondLevel enum**: STRANGER (0-24), ACQUAINTANCE (25-49), TRUSTED (50-74), DEVOTED (75-100)
- ✅ **Bond tracking**: `add_bond(amount)` adds points (capped at 100), returns level-up message if threshold crossed
- ✅ **Visual bond display**: Unicode bar (█░) with color-coded levels (green=DEVOTED, yellow=TRUSTED/ACQUAINTANCE)
- ✅ **`companions` command**: View party members with bond levels and descriptions
- ✅ **`recruit <npc>` command**: Recruit NPCs marked as `is_recruitable=True` to your party
- ✅ **NPC recruitability**: Added `is_recruitable` field to NPC model
- ✅ **Persistence**: Companions saved/loaded with game state (backward compatible)

**Future Enhancements**:
- **Bond levels** through choices, gifts, and shared experiences
- **Companion quests** that explore their past and resolve their arc
- ✅ **Combat synergies** unlock at higher bond levels - MVP IMPLEMENTED (passive attack damage bonuses: STRANGER 0%, ACQUAINTANCE +3%, TRUSTED +5%, DEVOTED +10%)
- **Companions react** to your choices (approval/disapproval affects bond)
- **Permadeath option**: Companions can die, with devastating consequences
- **Betrayal possibility**: Wrong choices can turn companions against you

---

#### 8. ENVIRONMENTAL STORYTELLING - The World as Narrator
**Impact**: Discovery, atmosphere, lore depth
**Status**: MVP IMPLEMENTED

Locations tell stories through details:

```
You enter the Abandoned Manor...

Upon closer inspection, you notice:
  - Claw marks on the walls, going upward
  - A child's toy near the cold fireplace
  - A journal, its last entry unfinished
  - The dining table set for guests who never arrived

[Examine journal?] > yes

  "Day 12 - The scratching in the walls has stopped.
   I tell myself this is good news, but Martha
   won't come out of the cellar. She says she
   saw something in the mirror that wasn't he"

   The entry ends mid-word. The pen is still here.
```

- **Multi-layered examination**: Look once = surface. Look again = details. Look three times = secrets ✅ IMPLEMENTED
- **Collectible lore**: Journals, letters, inscriptions that piece together larger stories
- **Environmental puzzles**: "The painting's eyes follow the candlestick..."
- **Tragic histories**: Every ruin was once alive. Find out what happened.
- **Hidden messages**: Some text only appears under certain conditions (night, high INT, specific items)

---

#### 9. THE WEIGHT OF GOLD - Meaningful Economy
**Impact**: Strategic decisions, world immersion

Money matters because scarcity creates drama:

```
Your pouch: 47 gold

The merchant eyes your equipment...
  "That sword you carry—fine craftsmanship.
   I'd give you 200 gold for it. Enough to
   buy passage on the ship leaving tonight."

But without the sword, how will you fight?

The ship leaves in 2 hours. The dungeon
with the cure is 3 hours away on foot.

What do you do?
```

- **Meaningful prices**: Good equipment is expensive. Choices feel real.
- **Multiple currencies**: Gold for common goods, ancient coins for artifacts, favors for services
- **Economic consequences**: Spend lavishly → prices rise. Flood market → crash.
- **Bribery and corruption**: Some problems can be solved with gold. At a cost.
- **Gambling**: High-risk games of chance in taverns
- **Investment**: Fund a merchant and get returns later

---

#### 10. TEMPORAL ECHOES - Time-Based Secrets
**Impact**: Replayability, discovery, world depth
**Status**: MVP IMPLEMENTED

The world changes based on time:

```
You return to the Old Well at midnight...

Unlike during the day, the well glows faintly.
A voice rises from the depths:

  "You came at the hour. Few do.
   Ask your question, and I shall answer.
   But truth always has a price..."

[Ask about the Forgotten King]
[Ask about your father's fate]
[Ask about the coming darkness]
[Leave - some truths are too heavy]
```

**MVP Implemented**:
- ✅ **Day/night cycle**: Time tracked as hour (0-23), advances on movement (+1hr) and rest (+4hrs)
- ✅ **Night whispers**: Eerie atmospheric whispers appear at night (40% chance)
- ✅ **NPC availability**: NPCs can be marked as unavailable at night (shops close)
- ✅ **Status display**: Current time shown in status command (e.g., "14:00 (Day)")
- ✅ **Persistence**: Time saved/loaded with game state (backward compatible)

**Future Enhancements**:
- **Moon phases** affect magic power and unlock hidden areas
- ✅ **Seasonal events**: Winter festivals, harvest celebrations, summer dangers - MVP IMPLEMENTED (see `seasons.py`)
- **Anniversary triggers**: Return to a location one "year" later for special events
- **Time-locked content**: Some doors only open at specific times

---

#### 11. THE LEGACY SYSTEM - Death Has Meaning
**Impact**: Tension, long-term investment, emergent stories

When you die, the story continues:

```
Your vision fades... but this is not the end.

╔══════════════════════════════════════════════╗
║         LEGACY CONTINUES                     ║
║                                              ║
║  20 years later, a new adventurer finds      ║
║  your journal in the ruins of Thornkeep...   ║
║                                              ║
║  INHERITED:                                  ║
║    - Your map (partial)                      ║
║    - Knowledge: "Beware the third chamber"   ║
║    - Reputation: "Child of the Fallen Hero"  ║
║    - Your unfinished quest                   ║
║                                              ║
║  The world remembers. Will you succeed       ║
║  where your predecessor failed?              ║
╚══════════════════════════════════════════════╝
```

- **Death is a chapter break**, not game over
- **Inheritors** start with partial knowledge of the world
- **Your grave** becomes a location in the world (can be found, looted, honored)
- **Legend grows**: Die heroically → NPCs speak of you. Die shamefully → your name is cursed.
- **Unfinished business**: Your ghost might appear to your successor
- **Cumulative progress**: Each generation can contribute to a greater goal

---

#### IMPLEMENTATION PRIORITY

**Phase 1 - Atmosphere** (Transform the feel):
1. Whisper System - Adds soul to every location
2. Environmental Storytelling - Makes exploration magical
3. Temporal Echoes - Adds depth and mystery

**Phase 2 - Consequence** (Make choices matter):
4. Echo Choices - Every decision resonates
5. ~~Living World Events~~ ✅ MVP IMPLEMENTED - Urgency and stakes
6. The Weight of Gold - Meaningful economy

**Phase 3 - Depth** (Mastery and investment):
7. ~~Combo Combat~~ ✅ MVP IMPLEMENTED - Satisfying combat loop
8. Bond System - Emotional investment
9. ~~Darkness Meter~~ ✅ MVP IMPLEMENTED - Psychological tension

**Phase 4 - Transcendence** (Truly unique):
10. ~~Dream Sequences~~ ✅ MVP IMPLEMENTED - Surreal storytelling
11. Legacy System - Death becomes narrative

---

### OVERWORLD & SUB-LOCATION REWORK - Hierarchical World System
**Status**: IN PROGRESS (Core Infrastructure Complete, Dungeon Hierarchy Validated)

**Problem**: The current flat world grid doesn't support meaningful world structure. Players wander an endless grid with random combat everywhere. There's no sense of safe havens, no cities to explore internally, no dungeons with depth.

**Progress**:
- ✅ **Location model fields** (IMPLEMENTED): Added 5 hierarchy fields to `Location` dataclass
  - `is_overworld: bool` - True for overworld landmarks
  - `parent_location: Optional[str]` - Parent landmark for sub-locations
  - `sub_locations: List[str]` - Child locations for landmarks
  - `is_safe_zone: bool` - No random encounters if True
  - `entry_point: Optional[str]` - Default sub-location when entering
- ✅ Serialization: `to_dict()` and `from_dict()` updated with backward compatibility
- ✅ Tests: 22 comprehensive tests for hierarchy fields
- ✅ **Town Square hierarchical structure** (IMPLEMENTED): Default world now includes:
  - Town Square as overworld landmark with `is_overworld=True`, `is_safe_zone=True`
  - 3 sub-locations: Market District (with Merchant), Guard Post (with Guard), Town Well
  - All sub-locations have `parent_location="Town Square"` and `is_safe_zone=True`
  - `enter`/`exit` commands work with actual content
- ✅ **Forest hierarchical structure** (IMPLEMENTED): Forest expanded to overworld landmark:
  - Forest as overworld landmark with `is_overworld=True`, `is_safe_zone=False` (danger zone)
  - 3 sub-locations: Forest Edge, Deep Woods, Ancient Grove
  - All sub-locations have `parent_location="Forest"`, `is_safe_zone=False`, `category="forest"`
  - Hermit NPC in Ancient Grove (`is_recruitable=True`)
- ✅ **Abandoned Mines dungeon** (IMPLEMENTED): First dungeon with hierarchical sub-locations:
  - Abandoned Mines at (1, 1) with `is_overworld=True`, `is_safe_zone=False`, `category="dungeon"`
  - 4 sub-locations: Mine Entrance (entry point), Upper Tunnels, Flooded Level, Boss Chamber
  - All sub-locations have `parent_location="Abandoned Mines"`, `is_safe_zone=False`, `category="dungeon"`
  - Old Miner NPC in Mine Entrance (quest giver)
  - Connected south to Cave, west to Forest via grid system

**🚧 FUTURE ENHANCEMENTS**:

1. ~~**BLOCKER: AI World Generation Ignores Hierarchy (CRITICAL)**~~ ✅ RESOLVED
   - **File**: `src/cli_rpg/ai_world.py`
   - **Resolution**: Updated `create_ai_world()`, `expand_world()`, and `expand_area()` to set hierarchy fields based on location category
   - **Implementation**:
     - Added `SAFE_ZONE_CATEGORIES` constant defining safe location categories (town, village, settlement)
     - Added `_infer_hierarchy_from_category()` helper function that maps categories to hierarchy fields
     - All AI-generated locations now get `is_overworld=True` and appropriate `is_safe_zone` based on category
     - `expand_area()` properly sets parent-child relationships for sub-locations
   - **Tests**: 26 tests in `tests/test_ai_world_hierarchy.py`

2. **ENHANCEMENT: Vertical Dungeon Navigation (DESIGN GAP)**
   - **Problem**: No `up`/`down` commands for multi-floor vertical dungeons
   - **Current state**: Dungeons work with horizontal sub-location hierarchy (Abandoned Mines implemented with 4 sub-locations using `enter`/`exit`)
   - **Future enhancement**: Add `depth` field to Location, implement `up`/`down` navigation for vertical dungeons
   - **Effort**: 8-12 hours (future milestone)
   - **Status**: Deferred - horizontal hierarchy sufficient for current content

**Remaining Architecture**:

```
OVERWORLD (macro map)
  │
  ├── ✅ 🏠 Town Square (SAFE) - IMPLEMENTED
  │     ├── Market District (with Merchant)
  │     ├── Guard Post (with Guard)
  │     └── Town Well
  │
  ├── ✅ 🌲 Forest (DANGEROUS) - IMPLEMENTED
  │     ├── Forest Edge
  │     ├── Deep Woods
  │     └── Ancient Grove (with Hermit)
  │
  ├── ✅ 🏠 Millbrook Village (SAFE) - IMPLEMENTED
  │     ├── Village Square (with Elder NPC)
  │     ├── Inn (with Innkeeper NPC, recruitable)
  │     └── Blacksmith (with Blacksmith NPC, merchant)
  │
  ├── ✅ 🏰 Ironhold City (SAFE) - IMPLEMENTED
  │     ├── Ironhold Market (with Wealthy Merchant)
  │     ├── Castle Ward (with Captain of the Guard)
  │     ├── Slums (with Beggar, recruitable)
  │     └── Temple Quarter (with Priest)
  │
  └── ✅ ⛏️ Abandoned Mines (DUNGEON) - IMPLEMENTED
        ├── Mine Entrance (with Old Miner NPC)
        ├── Upper Tunnels
        ├── Flooded Level
        └── Boss Chamber
```

**Core Concepts**:

1. **Overworld**: Large-scale map of landmarks (cities, dungeons, forests, mountains)
   - Travel between landmarks (possibly with travel time/random encounters)
   - Each landmark is an entry point to a sub-location
   - ✅ `worldmap` command shows overworld - IMPLEMENTED

2. **Sub-locations**: Internal areas within each landmark
   - Cities contain: districts, shops, taverns, castles
   - Dungeons contain: floors, rooms, boss chambers
   - Forests contain: clearings, caves, ruins
   - Each has its own local grid/map
   - `map` command shows current sub-location

3. **Safety Zones** (NO random encounters):
   - Towns and cities = SAFE
   - Villages = SAFE
   - Inns/taverns = SAFE
   - Shops = SAFE
   - Temple interiors = SAFE

4. **Danger Zones** (random encounters enabled):
   - Wilderness areas
   - Dungeons
   - Caves
   - Ruins
   - Roads between landmarks (overworld travel)

5. **Navigation**:
   - ✅ `enter <landmark>` - Enter a city/dungeon from overworld - IMPLEMENTED
   - ✅ `exit` / `leave` - Return to overworld - IMPLEMENTED
   - `n/s/e/w` - Move within current sub-location
   - `travel <landmark>` - Fast travel on overworld (if discovered)

**Location Model Changes**: ✅ IMPLEMENTED (see Progress section above)

**Enter/Exit Commands**: ✅ IMPLEMENTED
- `enter <location>` supports partial, case-insensitive matching for sub-location names
- Uses `entry_point` as default when no argument provided
- Both commands blocked during NPC conversation
- 11 comprehensive tests in `tests/test_game_state.py`

**Backwards Compatibility**: Implemented with full backward compatibility - old saves load correctly with default values.

**Benefits**:
- Logical world organization
- Safe towns for shopping/questing without combat interruption
- Dungeons feel like dungeons (contained, dangerous)
- Cities feel like cities (explorable, safe, populated)
- Clear distinction between travel and exploration
- Natural quest hubs vs adventure zones

**Files to modify**:
- ✅ `src/cli_rpg/models/location.py`: Add hierarchy fields - DONE
- ✅ `src/cli_rpg/random_encounters.py`: Check `is_safe_zone` before triggering encounters - DONE
- ✅ `src/cli_rpg/game_state.py`: Enter/exit commands - DONE
- ✅ `src/cli_rpg/world.py`: Default hierarchical world structure - DONE
- ✅ `src/cli_rpg/map_renderer.py`: Separate overworld and local map rendering - DONE
- ✅ `src/cli_rpg/ai_world.py`: AI generates landmarks with sub-locations - DONE
- ✅ `src/cli_rpg/game_state.py`: trigger_encounter() safe zone check - DONE

### Non-interactive mode bugs
**Status**: ACTIVE

Issues discovered while playtesting `--non-interactive` mode:

1. ~~**Character creation broken in non-interactive mode**~~ (RESOLVED)
   - Fixed: Added `create_character_non_interactive()` function that reads character creation inputs from stdin
   - New `--skip-character-creation` flag to use default "Agent" character (backward compatible)
   - Validates all inputs immediately and returns errors for invalid input
   - Supports manual stat allocation (name, method "1", str, dex, int, confirmation) and random stats (name, method "2", confirmation)

2. ~~**Shop command requires prior NPC interaction**~~ (RESOLVED)
   - Fixed: `shop` command now auto-detects merchant NPCs in the current location
   - No need to `talk Merchant` first - just use `shop` when a merchant is present
   - If multiple merchants exist, uses the first one found

3. ~~**NPC conversation responses are generic**~~ (RESOLVED with AI service)
   - When AI is enabled, NPCs respond intelligently to player input
   - Without AI, NPCs fall back to "nods thoughtfully" responses

4. ~~**Enemy attack text duplicates name**~~ (RESOLVED)
   - AI-generated attack flavor text included enemy name, but combat code also prefixed it
   - Result was: "Frostbite Yeti The Frostbite Yeti unleashes a chilling roar..."
   - Fixed: Added `strip_leading_name()` helper in `combat.py` that removes redundant name prefix from attack flavor text

5. **Non-interactive mode skipped AI initialization** (RESOLVED)
   - `run_non_interactive()` and `run_json_mode()` hardcoded `ai_service=None`
   - Fixed: Now loads AI config from environment variables like interactive mode

### Map System Bugs (Discovered via Playtesting)
**Status**: ACTIVE
**Date Discovered**: 2025-12-26

Issues discovered through comprehensive map system playtesting in non-interactive mode:

1. **CRITICAL: Map command fails inside SubGrid locations**
   - **File**: `src/cli_rpg/main.py`, line 1639
   - **Problem**: `render_map()` is called WITHOUT the `sub_grid` parameter, even when player is inside a sub-location
   - **Current code**:
     ```python
     elif command == "map":
         map_output = render_map(game_state.world, game_state.current_location)
         return (True, f"\n{map_output}")
     ```
   - **Impact**: When player enters a dungeon/building interior, running `map` shows "No map available - current location does not have coordinates" instead of the interior map
   - **Root cause**: Sub-locations are stored in `SubGrid`, not in `game_state.world`. The `render_map()` function HAS correct SubGrid rendering (via `_render_sub_grid_map()`), but main.py never passes the `sub_grid` parameter
   - **Fix**: Pass `game_state.current_sub_grid` as third argument:
     ```python
     map_output = render_map(game_state.world, game_state.current_location, game_state.current_sub_grid)
     ```
   - **Priority**: P1 - Core feature completely broken for dungeons/interiors

2. **MEDIUM: Worldmap command fails inside SubGrid locations**
   - **File**: `src/cli_rpg/main.py`, line 1643
   - **Problem**: `render_worldmap()` looks up current location in `world` dict, but SubGrid locations aren't stored there
   - **Current behavior**: Returns "No overworld map available - current location not found."
   - **Expected behavior**: Show overworld map centered on parent location with message "(You are inside [Parent Location])"
   - **Fix in main.py** (preferred):
     ```python
     elif command == "worldmap":
         worldmap_location = game_state.current_location
         if game_state.in_sub_location:
             current_loc = game_state.get_current_location()
             if current_loc.parent_location:
                 worldmap_location = current_loc.parent_location
         worldmap_output = render_worldmap(game_state.world, worldmap_location)
         return (True, f"\n{worldmap_output}")
     ```
   - **Priority**: P2 - Inconvenient but workaround exists (use `exit` first)

**Note**: The `render_map()` function in `map_renderer.py` already has full SubGrid rendering support (`_render_sub_grid_map()` with 13 passing tests). The infrastructure is complete - only the main.py integration is missing.

### Non-interactive mode enhancements
**Status**: ACTIVE

The basic `--non-interactive` mode has been implemented. The following enhancements would improve automated playtesting further:

1. ~~**Structured output for AI parsing**~~ (DONE - see "JSON output mode" in Resolved Issues)

2. ~~**Comprehensive gameplay logging**~~ (DONE - `--log-file` option implemented)
   - ~~Full session transcript with timestamps~~
   - ~~Log file output (e.g., `--log-file gameplay.log`)~~
   - ~~Record: commands issued, game responses, state changes~~
   - Future: Include RNG seeds for reproducibility
   - Future: Log AI-generated content for review

3. ~~**Session state export**~~ (DONE - `dump-state` command implemented)
   - ~~Dump full game state as JSON on demand or at intervals~~
   - ~~Include: player stats, inventory, location, quest progress, world state~~
   - Future: Enable session replay from logged state

4. ~~**Additional automation features**~~ (DONE)
   - ~~Configurable delays/timeouts~~ (DONE - `--delay` option implemented)
   - ~~Deterministic mode option (fixed RNG seed)~~ (DONE - `--seed` option implemented)

### Long-running AI simulation test suite
**Status**: ✅ RESOLVED

AI agent player and simulation framework have been implemented.

**Implemented Components** (in `scripts/` directory):

1. **`scripts/state_parser.py`** - JSON output parsing utilities
   - `AgentState` dataclass for tracking game state (location, health, gold, inventory, dread, quests, combat status)
   - Parses all JSON message types: `state`, `combat`, `actions`, `dump_state`

2. **`scripts/ai_agent.py`** - Heuristic-based agent implementation
   - `SessionStats` dataclass for collecting simulation statistics
   - `Agent` class with priority-based decision engine:
     - Combat: Flee at <25% HP, use potion at <50% HP, attack otherwise
     - Exploration: Rest if HP <50% or dread >60%, buy potions, complete quests, explore exits
   - `GameSession` class for subprocess management with threaded I/O

3. **`scripts/run_simulation.py`** - CLI entry point
   - Args: `--seed`, `--max-commands`, `--timeout`, `--output`, `--verbose`
   - Outputs summary statistics and optional JSON report

4. **`tests/test_ai_agent.py`** - Comprehensive test suite (31 tests)
   - Unit tests for state parsing and agent decisions
   - Integration tests running 50-100 commands

**Usage**:
```bash
# Run simulation with default settings (1000 commands)
python -m scripts.run_simulation

# Run with specific seed and command limit
python -m scripts.run_simulation --seed=42 --max-commands=100 --verbose

# Save JSON report
python -m scripts.run_simulation --output=report.json
```

**Future Enhancements** (moved to backlog):
- Scheduled CI/cron runs for periodic testing
- LLM-based agent variant for more dynamic playstyles
- Regression test corpus from successful runs

### Overworld map with cities and sub-locations
**Status**: ACTIVE

Players want a more sophisticated map system with hierarchical locations - an overworld containing cities, dungeons, and other points of interest that can be entered to explore sub-locations.

**Desired structure**:

1. **Overworld layer**
   - Large-scale map showing major landmarks (cities, forests, mountains, dungeons)
   - Travel between landmarks (possibly with travel time or random encounters)
   - Each landmark is an entry point to a sub-location

2. **Sub-location layer**
   - Cities contain: market district, tavern, castle, slums, etc.
   - Dungeons contain: multiple floors/rooms to explore
   - Forests contain: clearings, caves, ruins
   - Each sub-location has its own local map

3. **Navigation**
   - `enter <location>` to go into a city/dungeon
   - `exit` or `leave` to return to overworld
   - Local movement within sub-locations (current n/s/e/w system)
   - Fast travel between discovered overworld locations

4. **Map display**
   - Overworld map showing discovered landmarks
   - Local map when inside a sub-location
   - ✅ `map` command shows current layer, `worldmap` shows overworld - IMPLEMENTED

**Benefits**:
- More organized world structure
- Logical grouping of related areas
- Clearer sense of scale and progression
- Natural quest hubs (cities) vs adventure zones (dungeons/wilderness)

### Unique AI-generated ASCII art per entity
**Status**: ACTIVE

ASCII art should be unique and AI-generated for each distinct monster type, NPC, and location - not reused templates.

**Current problem**:
- Fallback template art is used when AI generation fails
- Same monster type (e.g., "Goblin") may get different art each encounter
- Art is not persisted, regenerated each time

**Requirements**:

1. **Unique per entity type**
   - Each monster kind gets ONE consistent ASCII art (all Goblins look the same)
   - Each NPC gets unique art matching their description
   - Each location gets unique art matching its theme

2. **AI-generated, not templates**
   - All art should be AI-generated based on entity name/description
   - Fallback templates only as last resort (API failure)
   - Art should reflect entity characteristics (menacing monsters, friendly merchants, etc.)

3. **Persistence**
   - Generated art stored with entity data
   - Art saved/loaded with game state
   - ✅ Monster art stored in bestiary by monster name - IMPLEMENTED
   - NPC art stored with NPC data in location

4. **Art cache/bestiary**
   - ✅ First encounter generates and caches art in bestiary - IMPLEMENTED
   - ✅ Subsequent encounters reuse cached art - IMPLEMENTED
   - ✅ `bestiary` command displays discovered monster art - IMPLEMENTED

### Meaningful choices and consequences
**Status**: ACTIVE (Partial)

Player decisions should have lasting impact on the world and story.

**Implemented**:
- ✅ NPCs reference player's combat flee history ("cautious" reputation if 3+ flees)
- ✅ NPCs reference player's combat kill history ("aggressive" reputation if 10+ kills)
- ✅ Player choices tracked in `game_state.choices` list

**Remaining features**:
- Dialogue choices that affect NPC relationships and quest outcomes
- Moral dilemmas with no clear "right" answer
- Branching quest paths based on player decisions
- World state changes based on completed quests (e.g., saving a village makes it thrive, ignoring it leads to ruin)
- Additional reputation types (e.g., heroic, wealthy)

### Character classes with unique playstyles
**Status**: ACTIVE (Base System Implemented)

**Implemented**:
- ✅ CharacterClass enum with 5 classes: Warrior, Mage, Rogue, Ranger, Cleric
- ✅ Class selection during character creation (by number or name)
- ✅ Stat bonuses per class:
  - **Warrior**: +3 STR, +1 DEX
  - **Mage**: +3 INT, +1 DEX
  - **Rogue**: +3 DEX, +1 STR
  - **Ranger**: +2 DEX, +1 STR, +1 INT
  - **Cleric**: +2 INT, +1 STR
- ✅ Class displayed in character status
- ✅ Class persistence in save/load (backward compatible)

**Future enhancements** (class-specific abilities):
- **Warrior**: ✅ `bash` command MVP IMPLEMENTED (shield bash costs 15 stamina, deals 0.75x damage, stuns target for 1 turn); Future: unlocks heavy armor
- **Mage**: ✅ `fireball` command MVP IMPLEMENTED (costs 20 mana, INT × 2.5 damage ignores defense, 25% Burn chance); ✅ `ice_bolt` command MVP IMPLEMENTED (costs 15 mana, INT × 2.0 damage ignores defense, 30% Freeze chance); ✅ `heal` command MVP IMPLEMENTED (costs 25 mana, restores INT × 2 HP); Future: weak armor restrictions
- **Rogue**: ✅ `sneak` command MVP IMPLEMENTED (stealth mode in combat, 1.5x backstab damage, DEX-based dodge while stealthed); ✅ `sneak` exploration MVP IMPLEMENTED (avoid random encounters, costs 10 stamina, success based on DEX/armor/light); ✅ `pick` command MVP IMPLEMENTED (lockpicking for treasure chests)
- **Ranger**: ✅ `track` command MVP IMPLEMENTED (costs 10 stamina, detects enemies in adjacent locations, success rate 50% + 3% per PER); ✅ wilderness damage bonus MVP IMPLEMENTED (+15% attack damage in forest/wilderness locations); Future: animal companion
- **Cleric**: ✅ `bless` command MVP IMPLEMENTED (costs 20 mana, +25% attack buff for 3 turns to player and companions); ✅ `smite` command MVP IMPLEMENTED (costs 15 mana, INT×2.5 damage ignores defense, INT×5.0 vs undead, 30% stun chance on undead); Future: holy symbols

### Charisma stat & social skills
**Status**: ✅ RESOLVED

**Implemented**:
- ✅ **Charisma (CHA) stat** added to Character model (1-20 range, default 10)
- ✅ **Class bonuses**: Cleric +2 CHA, Rogue +1 CHA
- ✅ **CHA price modifiers**: ±1% per CHA from 10 on buy/sell prices
- ✅ **`persuade` command**: 30% + (CHA × 3%) success, grants 20% shop discount
- ✅ **`intimidate` command**: 20% + (CHA × 2%) + (kills × 5%) success, affected by NPC willpower
- ✅ **`bribe <amount>` command**: Threshold 50 - (CHA × 2) gold, min 10 gold
- ✅ **NPC social attributes**: willpower (1-10), bribeable (bool), persuaded (bool)
- ✅ **Persistence**: All stats save/load with backward compatibility
- ✅ **Level up**: CHA +1 on level up like other stats

**Future Enhancements** (moved to backlog):
- High CHA unlocks special dialogue options marked with [CHA]
- Some quests can be resolved through talking instead of fighting

### Stealth & sneaking
**Status**: ACTIVE (Partial)

Let players avoid combat through cunning.

**Implemented**:
- ✅ `sneak` command for Rogues to enter stealth mode in combat (costs 10 stamina, 1.5x backstab damage, DEX-based dodge)
- ✅ `hide` command in combat to become untargetable for 1 turn (costs 10 stamina, available to all classes)
- ✅ `sneak` command for exploration (Rogue only, costs 10 stamina): Chance to avoid random encounters on next move. Success formula: 50% + (DEX × 2%) - (armor defense × 5%) - (15% if lit), capped 10-90%. Effect consumed on move.

**Remaining features**:
- Enemies have perception stats - some are blind, some have keen senses
- Stealth kills grant bonus XP ("clean kill" bonus)

### Perception & secret discovery
**Status**: ✅ RESOLVED

Reward observant players with hidden content.

**Implemented**:
- ✅ **Perception (PER) stat** added to Character model (1-20 range, default 10)
- ✅ **Class bonuses**: Rogue +2 PER, Ranger +1 PER
- ✅ **`search` command** (alias: `sr`) for active searching with +5 PER bonus (+2 with light source)
- ✅ **Hidden secrets on locations**: `hidden_secrets` field with type, description, threshold, discovered status
- ✅ **Secret types**: HIDDEN_DOOR, HIDDEN_TREASURE, TRAP, LORE_HINT
- ✅ **Passive detection**: Auto-detect secrets when PER >= threshold
- ✅ **Active search**: Manual search for harder-to-find secrets
- ✅ **Persistence**: All stats save/load with backward compatibility
- ✅ **Level up**: PER +1 on level up like other stats

**Future Enhancements** (moved to backlog):
- Traps can be spotted before triggering (PER check)
- Some NPC lies can be detected ("You sense they're not being truthful...")
- Secret passages between locations (shortcuts)

### Haggling at shops
**Status**: ✅ RESOLVED

Make shopping more interactive.

**Implemented**:
- ✅ `haggle` command negotiates better buy/sell prices at shops
- ✅ **Success formula**: 25% base + (CHA × 2%) + 15% if NPC is persuaded, max 85%
- ✅ **Success**: 15% discount on next buy OR 15% bonus on next sell
- ✅ **Critical success** (roll ≤ 10% of success chance): 25% discount + merchant hints at rare item
- ✅ **Failure**: No effect, can try again
- ✅ **Critical failure** (roll ≥ 95): Merchant refuses to trade for 3 turns (cooldown)
- ✅ **NPC attributes**: `haggleable: bool = True`, `haggle_cooldown: int = 0`
- ✅ **GameState tracking**: `haggle_bonus: float = 0.0` (reset after one transaction)
- ✅ Cooldown decrements on each exploration command
- ✅ Haggle bonus applied to both buy and sell prices
- ✅ Persistence: All fields save/load with backward compatibility

**Future Enhancements** (moved to backlog):
- Reputation affects starting prices (hero = discount, villain = markup)

### Luck stat affecting outcomes
**Status**: ✅ RESOLVED

**Implemented**:
- ✅ **Luck (LCK) stat** added to Character model (1-20 range, default 10)
- ✅ **Class bonuses**: Rogue +2 LCK, Ranger +1 LCK
- ✅ **Crit chance modifier**: ±0.5% per LCK point from baseline 10
- ✅ **Loot drop rate**: Base 50% ± 2% per LCK point from 10
- ✅ **Loot quality**: Weapon/armor bonuses gain +1 per 5 LCK above 10
- ✅ **Gold rewards**: ±5% per LCK point from 10
- ✅ **Level up**: LCK +1 on level up like other stats
- ✅ **Persistence**: Full save/load support with backward compatibility

**Future Enhancements** (moved to backlog):
- `pray` at temples to temporarily boost luck
- Cursed items reduce luck, blessed items increase it
- Some events are pure luck checks ("The bridge looks unstable...")

### Camping & wilderness survival
**Status**: ✅ RESOLVED

**Implemented**:
- ✅ `camp` command in wilderness to set up camp (uses Camping Supplies item)
- ✅ Camping heals 50% HP, reduces dread by 30 (40 with campfire), advances time 8 hours
- ✅ Campfire cooks Raw Meat → Cooked Meat automatically (40 HP vs 30 HP)
- ✅ 20% chance of friendly visitor spawn with campfire
- ✅ 40% chance of dream sequence during camp (uses dream system)
- ✅ `forage` command to find herbs/berries in forest/wilderness (PER-based, 1-hour cooldown)
- ✅ `hunt` command to track and kill game (DEX/PER-based, 2-hour cooldown, yields Raw Meat and Animal Pelt)
- ✅ Location restrictions: camping only in forest/wilderness/cave/ruins; foraging/hunting only in forest/wilderness
- ✅ Safe zone handling: camp redirects to rest in towns
- ✅ Cooldowns persist through save/load
- ✅ Camping Supplies available at Market District (40g) and Millbrook Village Inn (30g)

**Future Enhancements** (moved to backlog):
- Hunger system (optional hardcore mode) - starving = stat penalties
- Keep watch to avoid ambush
- Repair gear at camp

### Mana/stamina resource system
**Status**: ✅ RESOLVED

Special abilities should cost resources, not be free.

**Mana System - Implemented**:
- ✅ **Mana pool**: Mages get `50 + INT * 5`, other classes get `20 + INT * 2`
- ✅ **Cast costs mana**: Normal cast costs 10 mana, Arcane Burst combo costs 25 mana
- ✅ **Mana potions**: Items with `mana_restore` field restore mana when used
- ✅ **Level up**: Max mana recalculates based on new INT, mana fully restored
- ✅ **Status display**: Mana bar shown with color coding (like health)
- ✅ **Persistence**: Full serialization with backward compatibility for old saves

**Stamina System - Implemented**:
- ✅ **Stamina pool**: Warriors/Rangers get `50 + STR * 5`, other classes get `20 + STR * 2`
- ✅ **Sneak costs stamina**: Rogue sneak ability costs 10 stamina
- ✅ **Stamina regeneration**: 1 stamina per combat turn (in enemy_turn), 25% max stamina restored on rest
- ✅ **Stamina potions**: Items with `stamina_restore` field restore stamina when used (Stamina Potion: 30 gold, 25 stamina restore)
- ✅ **Status display**: Stamina bar shown with color coding (like health/mana)
- ✅ **Persistence**: Full serialization with backward compatibility for old saves

**Future Enhancements** (moved to backlog):
- Powerful abilities cost more: `fireball` = 20 mana, `power strike` = 15 stamina
- Running out = can only use basic attack
- Some enemies drain mana/stamina with attacks

### Weapon proficiencies & fighting styles
**Status**: ✅ RESOLVED

Not all weapons should feel the same.

- ✅ **Weapon types**: Sword, Axe, Dagger, Mace, Bow, Staff (plus UNKNOWN for unrecognized)
- ✅ **Proficiency system**: Using a weapon type increases skill with it (1 XP per attack)
- ✅ **Proficiency levels**: Novice (0 XP) → Apprentice (25 XP) → Journeyman (50 XP) → Expert (75 XP) → Master (100 XP)
- ✅ **Damage bonuses**: Novice +0%, Apprentice +5%, Journeyman +10%, Expert +15%, Master +20%
- ✅ **`proficiency` command** (alias: `prof`): View weapon proficiency levels with progress bars and damage bonuses
- ✅ **Combat integration**: Proficiency damage bonus applied to attacks, level-up messages displayed
- ✅ **Loot generation**: Weapon loot automatically gets weapon_type assigned via `infer_weapon_type()`
- ✅ **Persistence**: Weapon proficiencies save/load correctly, backward compatible with old saves
- ✅ **Fighting stances** (choose one active via `stance` command):
  - Balanced (default): +5% crit chance
  - Aggressive: +20% damage, -10% defense
  - Defensive: -10% damage, +20% defense
  - Berserker: Damage scales with missing HP (up to +50% at low health)
- ✅ Stance modifiers apply to all attacks (physical, spells, abilities)
- ✅ Stance persists through save/load with backward compatibility

**Future Enhancements** (moved to backlog):
- Special moves unlocked at Journeyman and Master levels
- Faster attacks at higher proficiency

### Status effects and combat depth
**Status**: ACTIVE (Partial)

Combat is too simple - attack until enemy dies. Core status effect system has been implemented with poison, burn, bleed, stun, and freeze.

**Implemented**:
- ✅ Basic poison status effect (DOT damage over time)
- ✅ Poison-capable enemies (spiders, snakes, serpents, vipers with 20% poison chance)
- ✅ Burn status effect (DOT damage over time, 2 turns)
- ✅ Burn-capable enemies (fire elementals, dragons, flame creatures with 20% burn chance)
- ✅ Bleed status effect (DOT damage over time, 3 damage per turn, 4 turns)
- ✅ Bleed-capable enemies (wolves, bears, lions, claw/fang-based creatures with 20% bleed chance)
- ✅ Stun status effect (player skips next action)
- ✅ Stun-capable enemies (trolls, golems, giants, hammer-wielders with 15% stun chance)
- ✅ Freeze status effect (reduces attack damage by 50% while frozen)
- ✅ Freeze-capable enemies (yetis, ice-themed creatures with 20% freeze chance, 2 turns)
- ✅ Freeze can be applied to both players and enemies
- ✅ Status effect display in combat status
- ✅ Status effects cleared on combat end
- ✅ Full persistence/serialization support
- ✅ Buff/debuff status effects (buff_attack, buff_defense, debuff_attack, debuff_defense)
- ✅ Buff/debuff modifies attack power and defense by percentage (stat_modifier field)
- ✅ Multiple buffs/debuffs stack additively
- ✅ Buff/debuff serialization with backward compatibility

**Remaining features**:
- ✅ Elemental strengths and weaknesses - MVP IMPLEMENTED (enemies have element types: PHYSICAL, FIRE, ICE, POISON; Fireball deals 1.5x damage to ICE enemies, 0.5x to FIRE; Ice Bolt deals 1.5x damage to FIRE enemies, 0.5x to ICE; effectiveness messages displayed in combat)
- ✅ Defensive options: `block` command - MVP IMPLEMENTED (costs 5 stamina, 75% damage reduction vs defend's 50%)
- ✅ Defensive options: `parry` command - MVP IMPLEMENTED (costs 8 stamina, 40% + DEX×2% success capped at 70%; success negates damage and counters for 50% attack power; failure takes full damage)
- ✅ Enemy attack patterns and telegraphed special moves - MVP IMPLEMENTED (bosses telegraph special attacks one turn in advance with warning messages; special attacks deal 1.5x-2x damage with optional status effects; defend/block mitigates damage)
- ✅ Critical hits and miss chances based on stats - MVP IMPLEMENTED (Player crits: 5% + 1% per DEX/INT capped at 20%, 1.5x damage; Player dodge: 5% + 0.5% per DEX capped at 15%; Enemy crits: flat 5%, 1.5x damage)
- ✅ Combat stances or modes - MVP IMPLEMENTED (see "Weapon proficiencies & fighting styles" section above; `stance` command with Balanced/Aggressive/Defensive/Berserker options)

### Dynamic world events
**Status**: ACTIVE (Partial)

The world feels static. Need ambient events and world dynamics.

**Implemented**:
- ✅ Day/night cycle with NPC availability (time advances on movement/rest, night whispers, NPCs can be unavailable at night)
- ✅ Random travel encounters (15% chance per move: hostile enemies 60%, wandering merchants 25%, mysterious wanderers 15%)
- ✅ Living world events (5% spawn chance per move: caravans, plagues, invasions with timed consequences)

**Remaining features**:
- ✅ Weather system affecting gameplay (clear, rain, storm, fog with dread modifiers and storm travel delays) - MVP IMPLEMENTED
- ✅ Weather visibility effects (storms reduce visibility/truncate descriptions/hide details, fog obscures exits and NPC names, caves unaffected) - MVP IMPLEMENTED
- ✅ Weather interactions (rain extinguishes burn 40% per turn, storm extends freeze +1 turn on apply) - MVP IMPLEMENTED
- ✅ Seasonal events and festivals - MVP IMPLEMENTED (4 seasons with dread modifiers, 4 festival types with gameplay bonuses)

### Reputation and faction system
**Status**: ACTIVE (MVP Implemented)

NPCs and towns should react to player's reputation and allegiances.

**Implemented**:
- ✅ **Faction model** (`src/cli_rpg/models/faction.py`) with:
  - `ReputationLevel` enum: HOSTILE (1-19), UNFRIENDLY (20-39), NEUTRAL (40-59), FRIENDLY (60-79), HONORED (80-100)
  - `Faction` dataclass with name, description, reputation points (1-100, default 50)
  - `add_reputation()` / `reduce_reputation()` methods with level-change messages
  - `get_reputation_display()` visual bar with color coding by level
  - Full serialization for save/load
- ✅ **GameState integration**: `factions` list field with backward-compatible persistence
- ✅ **`reputation` command** (alias: `rep`) to view all faction standings with visual bars
- ✅ **Default factions**: Town Guard, Merchant Guild, Thieves Guild (all start at Neutral)
- ✅ **Combat reputation consequences** (`src/cli_rpg/faction_combat.py`):
  - Enemy faction affiliation via pattern matching (bandit/thief → Thieves Guild, guard/soldier → Town Guard)
  - Killing affiliated enemies: -5 reputation with that faction
  - Killing affiliated enemies: +3 reputation with opposing faction (faction rivalries)
  - Reputation change messages displayed after combat victory

- ✅ **Merchant Guild shop prices** (`src/cli_rpg/faction_shop.py`):
  - HOSTILE (1-19): Merchants refuse to trade
  - UNFRIENDLY (20-39): +15% buy / -15% sell prices
  - NEUTRAL (40-59): No modifier
  - FRIENDLY (60-79): -10% buy / +10% sell prices
  - HONORED (80-100): -20% buy / +20% sell prices
  - Modifiers stack multiplicatively with CHA modifiers
  - 28 tests in `tests/test_faction_shop_prices.py`

**Remaining features**:
- Additional faction-based content unlocks (quests, areas)
- Additional faction conflicts and quest-based reputation changes
- Titles and recognition based on achievements

### Crafting and gathering system
**Status**: ACTIVE (Gathering & Recipes MVP Implemented)

Players should be able to create items, not just buy/find them.

**Implemented**:
- ✅ `gather` command (alias: `ga`) for resource collection in wilderness/dungeon areas
- ✅ RESOURCE ItemType for crafting materials (distinguished from MISC items)
- ✅ Location-specific resources:
  - Forest/Wilderness: Wood, Fiber
  - Cave/Dungeon: Iron Ore, Stone
  - Ruins: Stone, Iron Ore
- ✅ PER-based success chance: 40% base + 2% per PER point
- ✅ 1-hour cooldown between gather attempts (advances game time 1 hour)
- ✅ Gather blocked in safe zones (towns, villages)
- ✅ Cooldown persistence through save/load
- ✅ `recipes` command to view all available crafting recipes
- ✅ `craft <recipe>` command (alias: `cr`) to craft items from resources
- ✅ 8 crafting recipes:
  - Torch (1 Wood + 1 Fiber): Consumable light source, 10 moves of light
  - Iron Sword (2 Iron Ore + 1 Wood): Weapon, +5 damage
  - Iron Armor (3 Iron Ore + 1 Fiber): Armor, +4 defense
  - Rope (2 Fiber): Misc item
  - Stone Hammer (2 Stone + 1 Wood): Weapon, +3 damage
  - Healing Salve (2 Herbs): Consumable, heals 25 HP
  - Bandage (2 Fiber): Consumable, heals 15 HP
  - Wooden Shield (2 Wood + 1 Fiber): Armor, +2 defense
- ✅ Smart inventory space check (accounts for ingredients being consumed)
- ✅ Case-insensitive recipe names
- ✅ Specific error messages for missing ingredients

**Remaining features**:
- Crafting skill progression
- Rare recipes as quest rewards or discoveries
- Item enhancement/enchanting system

### Secrets and discovery
**Status**: ACTIVE

Exploration should reward curiosity with hidden content.

**Desired features**:
- Hidden rooms and secret passages (require specific actions to find)
- Lore fragments and collectible journal entries
- Easter eggs and rare encounters
- Riddles and puzzles guarding treasure
- Environmental storytelling (discover what happened through clues)
- Achievements for thorough exploration

### Companion system
**Status**: ACTIVE (MVP Implemented)

Adventuring alone limits roleplay possibilities.

**Implemented**:
- ✅ Recruitable NPC companions (NPCs with `is_recruitable=True`)
- ✅ Bond system with 4 levels (STRANGER → ACQUAINTANCE → TRUSTED → DEVOTED)
- ✅ `companions` command to view party members
- ✅ `recruit <npc>` command to recruit willing NPCs
- ✅ `dismiss <name>` command to remove companions from party
- ✅ Persistence with backward compatibility

**Remaining features**:
- ✅ Companion dialogue and banter during travel - MVP IMPLEMENTED (25% trigger chance per move, context-aware comments based on location, weather, time, dread, and bond level)
- ✅ Companion combat bonuses - MVP IMPLEMENTED (passive attack damage bonus based on bond level: STRANGER 0%, ACQUAINTANCE +3%, TRUSTED +5%, DEVOTED +10%; bonuses stack with multiple companions)
- ✅ Companion reactions to player choices - MVP IMPLEMENTED (companions react to combat choices based on personality: warrior approves kills/disapproves fleeing, pacifist approves fleeing/disapproves kills, pragmatic is neutral; bond adjusts ±3 points)
- ✅ Companion-specific quests and storylines - MVP IMPLEMENTED (companions can have personal quests that unlock at TRUSTED bond level; completing a companion's quest grants +15 bond bonus)

### Immersive text presentation
**Status**: ACTIVE (Partial)

Text output could be more atmospheric and engaging.

**Implemented**:
- ✅ Typewriter-style text reveal module (`text_effects.py`) with configurable delay, ANSI code handling, and Ctrl+C graceful fallback
- ✅ Effects follow color settings (disabled when colors are disabled, or when `--non-interactive`/`--json` mode)
- ✅ Typewriter effect integrated into `dreams.py` for dream sequences
- ✅ Typewriter effect integrated into `whisper.py` for ambient whispers
- ✅ Typewriter effect integrated into `combat.py` for dramatic combat moments (display functions: `display_combat_start()`, `display_combo()`, `display_combat_end()`)
- ✅ Effects disabled in `--non-interactive` and `--json` modes via `set_effects_enabled(False)` in `main.py`

**Remaining features**:
- ✅ Color-coding for dialogue and narration - MVP IMPLEMENTED (semantic `dialogue()` and `narration()` helpers in `colors.py`; NPC dialogue displays with blue text, narration uses default terminal color)
- ✅ Sound effects via terminal bell for important events - MVP IMPLEMENTED (terminal bell `\a` plays on combat victory, level up, player death, and quest completion; disabled in `--non-interactive` and `--json` modes)
- ✅ Pause and pacing for dramatic tension - MVP IMPLEMENTED (dramatic pause functions in `text_effects.py` with short/medium/long durations; integrated into combat start/combo/end and dream sequences; respects effects toggle)
- ✅ Stylized borders and frames for different UI elements - MVP IMPLEMENTED (`frames.py` with DOUBLE/SINGLE/SIMPLE frame styles; `frame_text()` for custom framing, `frame_announcement()` for world events, `frame_dream()` for dreams, `frame_combat_intro()` for boss/shadow combat; integrated into `dreams.py`, `world_events.py`, `shadow_creature.py`)

### AI-generated quest objectives don't match spawned enemies
**Status**: ✅ RESOLVED

**Description**: When AI generates kill quests (e.g., "Kill 5 goblins"), the specified enemy types don't actually spawn in the game. Random encounters spawn different enemy types (Wild Boar, Mountain Lion, Giant Spider, Wolf, etc.) that don't count toward quest objectives.

**Resolution**: Updated `DEFAULT_QUEST_GENERATION_PROMPT` in `ai_config.py` to include the valid enemy types from `combat.py`'s `enemy_templates` dictionary. The AI is now instructed to ONLY use these enemy types for kill quests:
- Forest/wilderness: Wolf, Bear, Wild Boar, Giant Spider
- Caves: Bat, Goblin, Troll, Cave Dweller
- Dungeons/ruins: Skeleton, Zombie, Ghost, Dark Knight
- Mountains: Eagle, Goat, Mountain Lion, Yeti
- Towns/villages: Bandit, Thief, Ruffian, Outlaw

**Note**: Players must be in the correct location type to encounter matching enemies. A quest for "Wolf" (forest enemy) won't progress while fighting in mountains (which spawn Eagle, Mountain Lion, Yeti). Players should explore forest areas to find wolves.

### Default world has no hidden secrets for search command
**Status**: ✅ RESOLVED

**Description**: The `search` command is documented in the README as a major feature ("Secret Discovery: PER-based check with +5 bonus; light sources provide additional +2") and the Perception & secret discovery system is marked as RESOLVED in ISSUES.md. However, no locations in the default world actually have any hidden secrets defined.

**Resolution**: Added `hidden_secrets` to 14 default world locations in `src/cli_rpg/world.py`:

| Location | Secret Type | Threshold | Description |
|----------|------------|-----------|-------------|
| Town Well | hidden_treasure | 10 | Loose stone with coins |
| Guard Post | lore_hint | 12 | Monster sighting tallies |
| Forest Edge | trap | 12 | Concealed snare trap |
| Deep Woods | hidden_door | 14 | Overgrown path to clearing |
| Ancient Grove | lore_hint | 15 | Ancient runes about guardian |
| Cave | hidden_treasure | 13 | Gemstone in crack |
| Village Square | lore_hint | 10 | Well inscription |
| Blacksmith | hidden_treasure | 12 | Coins in forge ashes |
| Upper Tunnels | trap | 14 | Unstable ceiling section |
| Flooded Level | hidden_treasure | 16 | Submerged payroll cache |
| Boss Chamber | lore_hint | 18 | Crystal warning inscription |
| Castle Ward | lore_hint | 16 | Coded noble's letter |
| Slums | hidden_door | 14 | Thieves' underground passage |
| Temple Quarter | hidden_treasure | 11 | Forgotten offering box |

Secrets are distributed by difficulty:
- Easy (threshold ≤12): Town areas, Millbrook Village
- Medium (threshold 13-14): Forest, Cave, Slums
- Hard (threshold ≥15): Abandoned Mines, Ironhold City

Tests added in `tests/test_perception.py` (TestDefaultWorldSecrets class).

### Procedural quest generation
**Status**: ACTIVE

Quests should be dynamically generated to keep gameplay fresh.

**Desired features**:
- AI-generated side quests based on current location and world state
- Quest templates with procedural elements (targets, rewards, locations)
- Scaling difficulty based on player level
- Quest chains that build on each other
- Emergent storylines from completed quests

## Resolved Issues


