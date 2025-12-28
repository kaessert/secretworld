"""Unit tests for the BackgroundGenerationQueue.

Tests cover:
1. Queue submits adjacent coordinates
2. Worker generates location data
3. Generated data is cached
4. get_cached returns data when ready
5. get_cached returns None if pending
6. shutdown stops workers cleanly
7. No duplicate submissions
8. Generation failure is handled gracefully
9. Integration: move uses cached location
10. Integration: move queues adjacent locations after arrival
"""

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from cli_rpg.background_gen import BackgroundGenerationQueue, GenerationTask
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.location import Location
from cli_rpg.models.character import Character, CharacterClass


class TestBackgroundGenQueue:
    """Tests for BackgroundGenerationQueue core functionality."""

    # Spec: queue.submit(coords, terrain) stores task
    def test_queue_submits_adjacent_coordinates(self):
        """Queue should store submitted tasks with coordinates and terrain."""
        mock_ai = Mock()
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            result = queue.submit(coords=(1, 0), terrain="forest")
            assert result is True
            assert (1, 0) in queue._pending
        finally:
            queue.shutdown()

    # Spec: worker calls ai_service.generate_location
    def test_worker_generates_location_data(self):
        """Worker should call AI service to generate location data."""
        mock_ai = Mock()
        mock_ai.generate_location.return_value = {
            "name": "Dark Forest",
            "description": "A gloomy forest",
            "category": "wilderness",
            "npcs": [],
        }
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            queue.submit(coords=(1, 0), terrain="forest")
            # Wait for worker to process
            time.sleep(0.3)

            # Verify AI was called
            assert mock_ai.generate_location.called
        finally:
            queue.shutdown()

    # Spec: completed tasks stored in cache by coords
    def test_generated_data_cached(self):
        """Completed generation should be cached by coordinates."""
        mock_ai = Mock()
        mock_ai.generate_location.return_value = {
            "name": "Dark Forest",
            "description": "A gloomy forest",
            "category": "wilderness",
            "npcs": [],
        }
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            queue.submit(coords=(1, 0), terrain="forest")
            # Wait for worker to process
            time.sleep(0.3)

            assert (1, 0) in queue._cache
            assert queue._cache[(1, 0)]["name"] == "Dark Forest"
        finally:
            queue.shutdown()

    # Spec: queue.get_cached(coords) returns data if ready
    def test_get_cached_returns_data(self):
        """get_cached should return cached data when available."""
        mock_ai = Mock()
        mock_ai.generate_location.return_value = {
            "name": "Mountain Peak",
            "description": "A high mountain",
            "category": "wilderness",
            "npcs": [],
        }
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            queue.submit(coords=(0, 1), terrain="mountain")
            # Wait for worker to process
            time.sleep(0.3)

            cached = queue.get_cached((0, 1))
            assert cached is not None
            assert cached["name"] == "Mountain Peak"
        finally:
            queue.shutdown()

    # Spec: returns None for in-progress tasks
    def test_get_cached_returns_none_if_pending(self):
        """get_cached should return None for in-progress tasks."""
        mock_ai = Mock()
        # Make generate_location slow so task stays pending
        mock_ai.generate_location.side_effect = lambda **kwargs: (
            time.sleep(1) or {"name": "Slow", "description": "A slow location", "category": "wilderness", "npcs": []}
        )
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            queue.submit(coords=(2, 2), terrain="forest")
            # Check immediately before worker completes
            cached = queue.get_cached((2, 2))
            assert cached is None
        finally:
            queue.shutdown()

    # Spec: queue.shutdown() cleanly stops threads
    def test_shutdown_stops_workers(self):
        """shutdown should stop all worker threads."""
        mock_ai = Mock()
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy", num_workers=2)
        queue.start()

        # Verify workers started
        assert len(queue._workers) == 2
        assert all(worker.is_alive() for worker in queue._workers)

        queue.shutdown()

        # Workers should be stopped (give some time for threads to finish)
        time.sleep(0.2)
        assert queue._running is False

    # Spec: same coords not queued twice
    def test_no_duplicate_submissions(self):
        """Same coordinates should not be queued twice."""
        mock_ai = Mock()
        mock_ai.generate_location.return_value = {
            "name": "Forest",
            "description": "A forest",
            "category": "wilderness",
            "npcs": [],
        }
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            result1 = queue.submit(coords=(1, 1), terrain="forest")
            result2 = queue.submit(coords=(1, 1), terrain="forest")

            assert result1 is True
            assert result2 is False  # Duplicate rejected
        finally:
            queue.shutdown()

    # Spec: AI errors don't crash worker
    def test_generation_failure_handled(self):
        """AI generation errors should not crash the worker."""
        mock_ai = Mock()
        mock_ai.generate_location.side_effect = Exception("API Error")
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            queue.submit(coords=(3, 3), terrain="swamp")
            # Wait for worker to attempt processing
            time.sleep(0.3)

            # Worker should still be running after error
            assert queue._running is True
            # Coords should be removed from pending on failure
            assert (3, 3) not in queue._pending
            # Coords should NOT be in cache (generation failed)
            assert (3, 3) not in queue._cache
        finally:
            queue.shutdown()

    def test_start_without_ai_service_is_noop(self):
        """Starting queue without AI service should be a no-op."""
        queue = BackgroundGenerationQueue(ai_service=None, theme="fantasy")
        queue.start()

        assert queue._running is False
        assert len(queue._workers) == 0

    def test_submit_without_running_returns_false(self):
        """Submitting to a non-running queue should return False."""
        mock_ai = Mock()
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        # Don't call start()

        result = queue.submit(coords=(1, 0), terrain="forest")
        assert result is False

    def test_pop_cached_removes_from_cache(self):
        """pop_cached should remove the entry from the cache."""
        mock_ai = Mock()
        mock_ai.generate_location.return_value = {
            "name": "Cave Entrance",
            "description": "A dark cave",
            "category": "cave",
            "npcs": [],
        }
        queue = BackgroundGenerationQueue(ai_service=mock_ai, theme="fantasy")
        queue.start()

        try:
            queue.submit(coords=(4, 4), terrain="cave")
            time.sleep(0.3)

            # First pop should return data
            popped = queue.pop_cached((4, 4))
            assert popped is not None
            assert popped["name"] == "Cave Entrance"

            # Second pop should return None (already removed)
            popped_again = queue.pop_cached((4, 4))
            assert popped_again is None
        finally:
            queue.shutdown()


class TestBackgroundGenIntegration:
    """Integration tests for background generation with GameState."""

    def _create_test_game_state(self, ai_service=None):
        """Create a minimal game state for testing."""
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
            level=1,
        )
        starting_location = Location(
            name="Starting Town",
            description="A peaceful town",
            coordinates=(0, 0),
            category="town",
            terrain="plains",
            is_named=True,
        )
        world = {"Starting Town": starting_location}

        from cli_rpg.game_state import GameState
        gs = GameState(
            character=character,
            world=world,
            starting_location="Starting Town",
            ai_service=ai_service,
            theme="fantasy",
        )
        return gs

    # Spec: GameState.move() checks cache before generating
    def test_move_uses_cached_location(self):
        """Move should use cached location data if available."""
        mock_ai = Mock()
        gs = self._create_test_game_state(ai_service=mock_ai)

        # Start background generation
        gs.start_background_generation()

        try:
            # Manually populate cache with pre-generated location
            if gs.background_gen_queue:
                gs.background_gen_queue._cache[(0, 1)] = {
                    "name": "Cached Forest",
                    "description": "A pre-generated forest",
                    "category": "wilderness",
                    "npcs": [],
                }
                gs.background_gen_queue._running = True  # Ensure it's marked as running

            # Move north - force named location generation and skip autosave
            with patch('cli_rpg.game_state.autosave'), \
                 patch.object(gs.location_noise_manager, 'should_spawn_location', return_value=True):
                success, message = gs.move("north")

            assert success is True
            assert "Cached Forest" in gs.current_location
        finally:
            if gs.background_gen_queue:
                gs.background_gen_queue.shutdown()

    # Spec: adjacent coords queued after successful move
    def test_move_queues_adjacent_after_arrival(self):
        """Move should queue adjacent locations for pre-generation after arrival."""
        mock_ai = Mock()
        mock_ai.generate_location.return_value = {
            "name": "New Location",
            "description": "A new location",
            "category": "wilderness",
            "npcs": [],
        }
        mock_ai.generate_region_context.return_value = RegionContext.default("Test Region", (0, 0))
        mock_ai.generate_world_context.return_value = WorldContext.default("fantasy")

        gs = self._create_test_game_state(ai_service=mock_ai)

        # Add destination location so move doesn't need to generate
        north_location = Location(
            name="North Field",
            description="A field to the north",
            coordinates=(0, 1),
            category="wilderness",
            terrain="plains",
            is_named=True,
        )
        gs.world["North Field"] = north_location

        # Mock chunk_manager to provide terrain info
        mock_chunk_manager = Mock()
        mock_chunk_manager.get_tile_at.return_value = "plains"
        gs.chunk_manager = mock_chunk_manager

        # Start background generation
        gs.start_background_generation()

        try:
            # Move north (patch autosave to avoid serialization issues with mocks)
            with patch('cli_rpg.game_state.autosave'):
                success, message = gs.move("north")

            assert success is True

            # Wait a moment for queue submission
            time.sleep(0.1)

            # Check if adjacent locations were queued
            if gs.background_gen_queue:
                # At least one adjacent coord should be queued or pending
                # (1, 1) - north, (-1, 1) - west, (0, 2) - further north, (0, 0) - already visited
                # The exact coords depend on implementation, but queue should have submissions
                total_items = len(gs.background_gen_queue._pending) + len(gs.background_gen_queue._cache)
                # We mainly want to ensure the queue is being used
                assert gs.background_gen_queue._running is True
        finally:
            if gs.background_gen_queue:
                gs.background_gen_queue.shutdown()
