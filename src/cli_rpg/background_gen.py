"""Background generation queue for pre-generating adjacent locations.

This module provides a thread-based queue for pre-generating location data
before the player arrives, eliminating blocking during movement.
"""

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
    """A background generation task.

    Attributes:
        coords: Target coordinates for the location
        terrain: Terrain type at the coordinates
        world_context: Optional world context for layered generation
        region_context: Optional region context for layered generation
    """
    coords: tuple[int, int]
    terrain: str
    world_context: Optional["WorldContext"] = None
    region_context: Optional["RegionContext"] = None


class BackgroundGenerationQueue:
    """Queue for pre-generating adjacent locations in background threads.

    This queue manages worker threads that pre-generate location data
    using the AI service. When the player moves to a pre-generated location,
    the cached data is used instead of blocking on a new AI call.

    Attributes:
        _ai_service: AI service for generating locations
        _theme: World theme for generation
        _queue: Thread-safe queue for pending tasks
        _cache: Dictionary mapping coords to generated location data
        _pending: Set of coordinates currently being processed
        _lock: Thread lock for cache/pending access
        _running: Whether the queue is active
        _workers: List of worker threads
        _num_workers: Number of worker threads to run
    """

    def __init__(
        self,
        ai_service: Optional["AIService"],
        theme: str,
        num_workers: int = 1,
    ):
        """Initialize the background generation queue.

        Args:
            ai_service: AI service for generating locations (None disables queue)
            theme: World theme for generation
            num_workers: Number of worker threads (default 1)
        """
        self._ai_service = ai_service
        self._theme = theme
        self._queue: queue.Queue[Optional[GenerationTask]] = queue.Queue()
        self._cache: dict[tuple[int, int], dict] = {}
        self._pending: set[tuple[int, int]] = set()
        self._lock = threading.Lock()
        self._running = False
        self._workers: list[threading.Thread] = []
        self._num_workers = num_workers

    def start(self) -> None:
        """Start background worker threads.

        If no AI service is configured, this is a no-op.
        """
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
        """Stop background workers.

        Sends shutdown signals to all workers and waits for them to finish.
        """
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

        Args:
            coords: Target coordinates for the location
            terrain: Terrain type at the coordinates
            world_context: Optional world context for layered generation
            region_context: Optional region context for layered generation

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
        """Get cached location data if available.

        Args:
            coords: Coordinates to look up

        Returns:
            Cached location data dict, or None if not available.
        """
        with self._lock:
            return self._cache.get(coords)

    def pop_cached(self, coords: tuple[int, int]) -> Optional[dict]:
        """Get and remove cached location data.

        Args:
            coords: Coordinates to pop from cache

        Returns:
            Cached location data dict (removed from cache), or None if not available.
        """
        with self._lock:
            return self._cache.pop(coords, None)

    def _worker_loop(self) -> None:
        """Background worker loop.

        Continuously processes tasks from the queue until shutdown.
        """
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
        """Process a single generation task.

        Calls the AI service to generate location data and caches the result.

        Args:
            task: The generation task to process
        """
        try:
            # Generate location data using AI service
            location_data = self._ai_service.generate_location(
                theme=self._theme,
                context_locations=[],
                source_location=None,
                direction=None,
                terrain_type=task.terrain,
                world_context=task.world_context,
            )

            with self._lock:
                self._cache[task.coords] = location_data
                self._pending.discard(task.coords)

            logger.debug(f"Pre-generated location at {task.coords}")

        except Exception as e:
            logger.warning(f"Failed to pre-generate {task.coords}: {e}")
            with self._lock:
                self._pending.discard(task.coords)
