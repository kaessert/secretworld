# Implementation Plan: Issue 8 - Background Generation Queue

## Overview
Add background pre-generation of adjacent locations to eliminate blocking during player movement. This builds on the existing `_pregenerate_adjacent_regions()` pattern but extends it to pre-generate actual location content in background threads.

## Key Insight
The codebase already has:
1. `_pregenerate_adjacent_regions()` in `game_state.py` - pre-caches **region contexts** synchronously
2. `progress.py` - threading patterns for non-blocking spinners
3. `expand_area()` / `expand_world()` in `ai_world.py` - the actual location generation functions

The gap: Region contexts are pre-generated, but **actual location data** (terrain, descriptions, NPCs) is only generated when the player moves there, causing blocking.

## Spec

**BackgroundGenerationQueue** provides:
1. A thread pool (1-2 workers) for background AI generation
2. Queue adjacent coordinates when player approaches unexplored territory
3. Cache generated locations until player arrives
4. Graceful fallback if generation fails or player arrives before completion
5. No impact on gameplay if disabled or AI unavailable

## Tests (tests/test_background_gen.py)

### Test Class: TestBackgroundGenQueue
1. `test_queue_submits_adjacent_coordinates` - queue.submit(coords, terrain) stores task
2. `test_worker_generates_location_data` - worker calls ai_service.generate_location
3. `test_generated_data_cached` - completed tasks stored in cache by coords
4. `test_get_cached_returns_data` - queue.get_cached(coords) returns data if ready
5. `test_get_cached_returns_none_if_pending` - returns None for in-progress tasks
6. `test_shutdown_stops_workers` - queue.shutdown() cleanly stops threads
7. `test_no_duplicate_submissions` - same coords not queued twice
8. `test_generation_failure_handled` - AI errors don't crash worker

### Test Class: TestBackgroundGenIntegration
9. `test_move_uses_cached_location` - GameState.move() checks cache before generating
10. `test_move_queues_adjacent_after_arrival` - adjacent coords queued after successful move

## Implementation Steps

### Step 1: Create background_gen.py

```python
# src/cli_rpg/background_gen.py
"""Background generation queue for pre-generating adjacent locations."""

import logging
import queue
import threading
from dataclasses import dataclass
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.ai_service import AIService
    from cli_rpg.models.world_context import WorldContext
    from cli_rpg.models.region_context import RegionContext

logger = logging.getLogger(__name__)


@dataclass
class GenerationTask:
    """A background generation task."""
    coords: tuple[int, int]
    terrain: str
    world_context: Optional["WorldContext"] = None
    region_context: Optional["RegionContext"] = None


class BackgroundGenerationQueue:
    """Queue for pre-generating adjacent locations in background threads."""

    def __init__(
        self,
        ai_service: Optional["AIService"],
        theme: str,
        num_workers: int = 1,
    ):
        self._ai_service = ai_service
        self._theme = theme
        self._queue: queue.Queue[GenerationTask] = queue.Queue()
        self._cache: dict[tuple[int, int], dict] = {}
        self._pending: set[tuple[int, int]] = set()
        self._lock = threading.Lock()
        self._running = False
        self._workers: list[threading.Thread] = []
        self._num_workers = num_workers

    def start(self) -> None:
        """Start background worker threads."""
        if self._ai_service is None:
            return  # No AI service, no background generation

        with self._lock:
            if self._running:
                return
            self._running = True

            for i in range(self._num_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    daemon=True,
                    name=f"bg-gen-worker-{i}"
                )
                worker.start()
                self._workers.append(worker)

    def shutdown(self) -> None:
        """Stop background workers."""
        with self._lock:
            self._running = False

        # Wake up workers with sentinel values
        for _ in self._workers:
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                pass

        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=1.0)
        self._workers.clear()

    def submit(
        self,
        coords: tuple[int, int],
        terrain: str,
        world_context: Optional["WorldContext"] = None,
        region_context: Optional["RegionContext"] = None,
    ) -> bool:
        """Submit coordinates for background generation.

        Returns:
            True if submitted, False if already pending/cached or not running.
        """
        with self._lock:
            if not self._running:
                return False
            if coords in self._pending or coords in self._cache:
                return False
            self._pending.add(coords)

        task = GenerationTask(
            coords=coords,
            terrain=terrain,
            world_context=world_context,
            region_context=region_context,
        )
        self._queue.put(task)
        return True

    def get_cached(self, coords: tuple[int, int]) -> Optional[dict]:
        """Get cached location data if available."""
        with self._lock:
            return self._cache.get(coords)

    def pop_cached(self, coords: tuple[int, int]) -> Optional[dict]:
        """Get and remove cached location data."""
        with self._lock:
            return self._cache.pop(coords, None)

    def _worker_loop(self) -> None:
        """Background worker loop."""
        while self._running:
            try:
                task = self._queue.get(timeout=0.5)
                if task is None:  # Shutdown sentinel
                    break
                self._process_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.warning(f"Background generation error: {e}")

    def _process_task(self, task: GenerationTask) -> None:
        """Process a single generation task."""
        try:
            # Generate location data (simplified - uses generate_location)
            location_data = self._ai_service.generate_location_with_context(
                world_context=task.world_context,
                region_context=task.region_context,
                source_location=None,
                direction=None,
                terrain_type=task.terrain,
            ) if task.world_context and task.region_context else (
                self._ai_service.generate_location(
                    theme=self._theme,
                    context_locations=[],
                    source_location=None,
                    direction=None,
                )
            )

            with self._lock:
                self._cache[task.coords] = location_data
                self._pending.discard(task.coords)

            logger.debug(f"Pre-generated location at {task.coords}")

        except Exception as e:
            logger.warning(f"Failed to pre-generate {task.coords}: {e}")
            with self._lock:
                self._pending.discard(task.coords)
```

### Step 2: Integrate into GameState

Modify `game_state.py`:

1. Add `background_gen_queue` attribute to `__init__`:
```python
self.background_gen_queue: Optional[BackgroundGenerationQueue] = None
```

2. Add `start_background_generation()` method:
```python
def start_background_generation(self) -> None:
    """Start background generation queue if AI service available."""
    if self.ai_service is not None:
        from cli_rpg.background_gen import BackgroundGenerationQueue
        self.background_gen_queue = BackgroundGenerationQueue(
            ai_service=self.ai_service,
            theme=self.theme,
        )
        self.background_gen_queue.start()
```

3. Modify `move()` to check cache before generating:
```python
# After calculating target_coords, before generating new location:
if self.background_gen_queue is not None:
    cached_data = self.background_gen_queue.pop_cached(target_coords)
    if cached_data is not None:
        # Use cached location data instead of calling AI
        ...
```

4. Modify `_pregenerate_adjacent_regions()` to also queue locations:
```python
# After pre-generating region contexts, queue adjacent locations
if self.background_gen_queue is not None:
    for direction in DIRECTION_OFFSETS:
        dx, dy = DIRECTION_OFFSETS[direction]
        adj_coords = (coords[0] + dx, coords[1] + dy)
        # Skip if location already exists
        if self._get_location_by_coordinates(adj_coords) is None:
            terrain = self.chunk_manager.get_tile_at(*adj_coords) if self.chunk_manager else "plains"
            self.background_gen_queue.submit(
                coords=adj_coords,
                terrain=terrain,
                world_context=self.world_context,
                region_context=self.get_or_create_region_context(adj_coords, terrain),
            )
```

### Step 3: Integrate into main.py

Add initialization after GameState creation:
```python
# After game_state is created:
game_state.start_background_generation()

# At shutdown (in quit handling):
if game_state.background_gen_queue:
    game_state.background_gen_queue.shutdown()
```

### Step 4: Add serialization support

Modify `to_dict()` and `from_dict()` to handle background_gen_queue:
- Don't serialize pending queue (ephemeral)
- Re-create queue on load if AI service available

## Files Changed

1. **Create**: `src/cli_rpg/background_gen.py` - BackgroundGenerationQueue class
2. **Create**: `tests/test_background_gen.py` - 10 tests
3. **Modify**: `src/cli_rpg/game_state.py` - Add queue, integrate with move()
4. **Modify**: `src/cli_rpg/main.py` - Initialize queue at startup, shutdown at quit
