# Implementation Summary: Location Clustering for POI Generation

## What Was Implemented

Implemented spatial clustering of similar location types when generating named locations (POIs). When generating a new named location, the system now checks for nearby named locations and biases toward generating similar location types, creating more geographically coherent clusters.

## Features Added

### 1. Clustering Constants (`src/cli_rpg/world_tiles.py`)

- **`LOCATION_CLUSTER_GROUPS`**: Maps location categories to cluster groups:
  - `settlements`: village, town, city, settlement
  - `dungeons`: dungeon, cave, ruins
  - `wilderness_pois`: forest, wilderness, grove
  - `sacred`: temple, shrine, monastery
  - `commerce`: shop, tavern, inn, merchant_camp

- **`CLUSTER_RADIUS`**: Set to 10 tiles (Manhattan distance) - locations within this radius are considered for clustering

- **`CLUSTER_PROBABILITY`**: Set to 0.6 (60%) - probability that clustering will occur when nearby similar locations exist

### 2. Clustering Helper Function (`src/cli_rpg/world_tiles.py`)

Added `get_cluster_category_bias(world, target_coords, radius, rng)`:
- Scans for named locations within radius
- Returns a category from the most common nearby cluster group
- Respects `CLUSTER_PROBABILITY` for randomness
- Returns `None` if no clustering should occur

### 3. Category Hint in Fallback Generation (`src/cli_rpg/world.py`)

Modified `generate_fallback_location()` to accept `category_hint` parameter:
- For named locations, `category_hint` overrides terrain-based category
- For unnamed locations (terrain filler), `category_hint` is ignored

### 4. AI Generation Integration (`src/cli_rpg/ai_world.py`)

Modified `expand_area()` to accept `category_hint` parameter:
- Added category-specific sub-theme hints for AI generation
- Maps categories like "village", "dungeon", "temple" to thematic prompts

### 5. Game State Integration (`src/cli_rpg/game_state.py`)

Updated `move()` method:
- Calls `get_cluster_category_bias()` before generating named locations
- Passes `category_hint` to both `expand_area()` and `generate_fallback_location()`

## Files Modified

1. `src/cli_rpg/world_tiles.py` - Added clustering constants and helper function
2. `src/cli_rpg/world.py` - Added `category_hint` parameter to `generate_fallback_location()`
3. `src/cli_rpg/game_state.py` - Integrated clustering into `move()` method
4. `src/cli_rpg/ai_world.py` - Added `category_hint` parameter to `expand_area()`

## New Test File

Created `tests/test_location_clustering.py` with 16 tests covering:
- Clustering constant definitions
- `get_cluster_category_bias()` function behavior
- `generate_fallback_location()` with category hints

## Test Results

- All 16 new tests pass
- Full test suite (4185 tests) passes with no regressions

## How It Works

1. When player moves and triggers named location generation
2. `get_cluster_category_bias()` scans for nearby named locations
3. If similar locations exist nearby and probability check passes (60%)
4. Returns a category from the same cluster group
5. Category hint is passed to location generation
6. New location is generated with biased category

## E2E Validation

- When exploring near villages, new POIs have ~60% chance to be settlements
- When exploring near dungeons/caves/ruins, new POIs cluster as dungeons
- When no nearby named locations exist, generation proceeds normally
- Unnamed terrain filler locations are unaffected
