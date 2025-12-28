"""Tests for agent checkpoint system.

Tests for AgentCheckpoint serialization, CheckpointTrigger detection,
SessionManager operations, and Agent/GameSession checkpoint methods.
"""
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.agent_checkpoint import AgentCheckpoint
from scripts.checkpoint_triggers import CheckpointTrigger, detect_trigger
from scripts.agent_persistence import SessionManager
from scripts.ai_agent import Agent, GameSession, SessionStats
from scripts.state_parser import AgentState


class TestAgentCheckpoint:
    """Tests for AgentCheckpoint dataclass serialization."""

    def test_checkpoint_to_dict_roundtrip(self):
        """Test that AgentCheckpoint can be serialized and deserialized."""
        # Spec: AgentCheckpoint serialization roundtrip
        checkpoint = AgentCheckpoint(
            current_goal="EXPLORE_OVERWORLD",
            visited_coordinates=[(0, 0), (1, 0), (0, 1)],
            current_coords=(1, 0),
            direction_history=["north", "east"],
            talked_this_location=["Merchant", "Guard"],
            sub_location_moves=5,
            stats={
                "commands_issued": 42,
                "locations_visited": ["Town Square", "Market"],
                "enemies_defeated": 3,
            },
            checkpoint_type="auto",
            game_save_path="/saves/game_001.json",
            seed=12345,
            timestamp="2024-01-15T10:30:00",
            command_index=42,
        )

        # Serialize to dict
        data = checkpoint.to_dict()

        # Verify dict structure
        assert data["current_goal"] == "EXPLORE_OVERWORLD"
        assert data["visited_coordinates"] == [(0, 0), (1, 0), (0, 1)]
        assert data["current_coords"] == (1, 0)
        assert data["direction_history"] == ["north", "east"]
        assert data["talked_this_location"] == ["Merchant", "Guard"]
        assert data["sub_location_moves"] == 5
        assert data["stats"]["commands_issued"] == 42
        assert data["checkpoint_type"] == "auto"
        assert data["game_save_path"] == "/saves/game_001.json"
        assert data["seed"] == 12345
        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert data["command_index"] == 42

        # Deserialize back
        restored = AgentCheckpoint.from_dict(data)

        # Verify roundtrip
        assert restored.current_goal == checkpoint.current_goal
        assert restored.visited_coordinates == checkpoint.visited_coordinates
        assert restored.current_coords == checkpoint.current_coords
        assert restored.direction_history == checkpoint.direction_history
        assert restored.talked_this_location == checkpoint.talked_this_location
        assert restored.sub_location_moves == checkpoint.sub_location_moves
        assert restored.stats == checkpoint.stats
        assert restored.checkpoint_type == checkpoint.checkpoint_type
        assert restored.game_save_path == checkpoint.game_save_path
        assert restored.seed == checkpoint.seed
        assert restored.timestamp == checkpoint.timestamp
        assert restored.command_index == checkpoint.command_index

    def test_checkpoint_with_empty_collections(self):
        """Test checkpoint with empty collections."""
        # Spec: Handle edge case of empty collections
        checkpoint = AgentCheckpoint(
            current_goal="HEAL_UP",
            visited_coordinates=[],
            current_coords=(0, 0),
            direction_history=[],
            talked_this_location=[],
            sub_location_moves=0,
            stats={},
            checkpoint_type="death",
            game_save_path="",
            seed=0,
            timestamp="",
            command_index=0,
        )

        data = checkpoint.to_dict()
        restored = AgentCheckpoint.from_dict(data)

        assert restored.visited_coordinates == []
        assert restored.direction_history == []
        assert restored.talked_this_location == []
        assert restored.stats == {}


class TestCheckpointTrigger:
    """Tests for CheckpointTrigger enum and detection."""

    def test_all_trigger_types_exist(self):
        """Test that all expected trigger types are defined."""
        # Spec: CheckpointTrigger enum values
        expected_triggers = [
            "QUEST_ACCEPT",
            "QUEST_COMPLETE",
            "DUNGEON_ENTRY",
            "DUNGEON_EXIT",
            "BOSS_ENCOUNTER",
            "BOSS_DEFEAT",
            "DEATH",
            "LEVEL_UP",
            "INTERVAL",
            "CRASH_RECOVERY",
        ]
        for trigger_name in expected_triggers:
            assert hasattr(CheckpointTrigger, trigger_name)

    def test_detect_trigger_quest_accept(self):
        """Test detection of quest acceptance."""
        # Spec: CheckpointTrigger detection for QUEST_ACCEPT
        prev_state = AgentState()
        prev_state.quests = []

        curr_state = AgentState()
        curr_state.quests = ["Kill 5 Goblins"]

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.QUEST_ACCEPT

    def test_detect_trigger_dungeon_entry(self):
        """Test detection of dungeon entry."""
        # Spec: CheckpointTrigger detection for DUNGEON_ENTRY
        prev_state = AgentState()
        prev_state.in_sub_location = False

        curr_state = AgentState()
        curr_state.in_sub_location = True

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.DUNGEON_ENTRY

    def test_detect_trigger_dungeon_exit(self):
        """Test detection of dungeon exit."""
        # Spec: CheckpointTrigger detection for DUNGEON_EXIT
        prev_state = AgentState()
        prev_state.in_sub_location = True

        curr_state = AgentState()
        curr_state.in_sub_location = False

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.DUNGEON_EXIT

    def test_detect_trigger_death(self):
        """Test detection of player death."""
        # Spec: CheckpointTrigger detection for DEATH
        prev_state = AgentState()
        prev_state.health = 50
        prev_state.last_narrative = ""

        curr_state = AgentState()
        curr_state.health = 0
        curr_state.last_narrative = "You have died!"

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.DEATH

    def test_detect_trigger_level_up(self):
        """Test detection of level up."""
        # Spec: CheckpointTrigger detection for LEVEL_UP
        prev_state = AgentState()
        prev_state.level = 2

        curr_state = AgentState()
        curr_state.level = 3

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.LEVEL_UP

    def test_detect_trigger_interval(self):
        """Test detection of interval checkpoint (every 50 commands)."""
        # Spec: CheckpointTrigger detection for INTERVAL
        prev_state = AgentState()
        curr_state = AgentState()

        # At exactly 50 commands
        trigger = detect_trigger(prev_state, curr_state, command_count=50)
        assert trigger == CheckpointTrigger.INTERVAL

        # At 100 commands
        trigger = detect_trigger(prev_state, curr_state, command_count=100)
        assert trigger == CheckpointTrigger.INTERVAL

        # At 49 commands - no trigger
        trigger = detect_trigger(prev_state, curr_state, command_count=49)
        assert trigger is None

    def test_detect_trigger_no_trigger(self):
        """Test that no trigger is detected when nothing changed."""
        # Spec: No trigger when state unchanged
        prev_state = AgentState()
        prev_state.location = "Town Square"
        prev_state.health = 100

        curr_state = AgentState()
        curr_state.location = "Town Square"
        curr_state.health = 100

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger is None

    def test_detect_trigger_boss_encounter(self):
        """Test detection of boss encounter."""
        # Spec: CheckpointTrigger detection for BOSS_ENCOUNTER
        prev_state = AgentState()
        prev_state.in_combat = False

        curr_state = AgentState()
        curr_state.in_combat = True
        curr_state.enemy = "Ancient Dragon"
        curr_state.last_narrative = "A fearsome boss appears before you!"

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.BOSS_ENCOUNTER

    def test_detect_trigger_boss_defeat(self):
        """Test detection of boss defeat."""
        # Spec: CheckpointTrigger detection for BOSS_DEFEAT
        prev_state = AgentState()
        prev_state.in_combat = True
        prev_state.has_boss = True
        prev_state.boss_defeated = False

        curr_state = AgentState()
        curr_state.in_combat = False
        curr_state.has_boss = True
        curr_state.boss_defeated = True

        trigger = detect_trigger(prev_state, curr_state, command_count=10)
        assert trigger == CheckpointTrigger.BOSS_DEFEAT


class TestSessionManager:
    """Tests for SessionManager checkpoint operations."""

    def test_create_session(self):
        """Test session directory creation."""
        # Spec: SessionManager.create_session returns session_id
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(base_dir=tmpdir)
            session_id = manager.create_session(seed=42)

            assert session_id is not None
            assert len(session_id) > 0

            # Verify session directory exists
            session_path = Path(tmpdir) / session_id
            assert session_path.exists()
            assert session_path.is_dir()

    def test_save_and_load_checkpoint(self):
        """Test saving and loading a checkpoint."""
        # Spec: SessionManager save/load operations
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(base_dir=tmpdir)
            session_id = manager.create_session(seed=42)

            checkpoint = AgentCheckpoint(
                current_goal="EXPLORE_DUNGEON",
                visited_coordinates=[(0, 0), (1, 1)],
                current_coords=(1, 1),
                direction_history=["north"],
                talked_this_location=["Innkeeper"],
                sub_location_moves=10,
                stats={"commands_issued": 25},
                checkpoint_type="dungeon",
                game_save_path="save_001.json",
                seed=42,
                timestamp="2024-01-15T12:00:00",
                command_index=25,
            )

            # Save checkpoint
            checkpoint_id = manager.save_checkpoint(
                checkpoint, CheckpointTrigger.DUNGEON_ENTRY, session_id
            )

            assert checkpoint_id is not None

            # Load checkpoint
            loaded = manager.load_checkpoint(checkpoint_id)

            assert loaded.current_goal == checkpoint.current_goal
            assert loaded.visited_coordinates == checkpoint.visited_coordinates
            assert loaded.current_coords == checkpoint.current_coords
            assert loaded.sub_location_moves == checkpoint.sub_location_moves
            assert loaded.seed == checkpoint.seed

    def test_list_checkpoints(self):
        """Test listing checkpoints for a session."""
        # Spec: SessionManager.list_checkpoints
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(base_dir=tmpdir)
            session_id = manager.create_session(seed=42)

            # Create multiple checkpoints
            for i in range(3):
                checkpoint = AgentCheckpoint(
                    current_goal="EXPLORE_OVERWORLD",
                    visited_coordinates=[(0, 0)],
                    current_coords=(0, 0),
                    direction_history=[],
                    talked_this_location=[],
                    sub_location_moves=0,
                    stats={"commands_issued": i * 10},
                    checkpoint_type="auto",
                    game_save_path=f"save_{i}.json",
                    seed=42,
                    timestamp=f"2024-01-15T12:0{i}:00",
                    command_index=i * 10,
                )
                manager.save_checkpoint(
                    checkpoint, CheckpointTrigger.INTERVAL, session_id
                )

            # List checkpoints
            checkpoints = manager.list_checkpoints(session_id)

            assert len(checkpoints) == 3
            # Should be ordered by timestamp/command_index
            for cp in checkpoints:
                assert "checkpoint_id" in cp
                assert "command_index" in cp
                assert "timestamp" in cp

    def test_crash_recovery(self):
        """Test crash recovery checkpoint management."""
        # Spec: SessionManager crash recovery
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SessionManager(base_dir=tmpdir)
            session_id = manager.create_session(seed=42)

            checkpoint = AgentCheckpoint(
                current_goal="COMPLETE_QUEST",
                visited_coordinates=[(0, 0), (1, 0)],
                current_coords=(1, 0),
                direction_history=["east"],
                talked_this_location=[],
                sub_location_moves=0,
                stats={"commands_issued": 100},
                checkpoint_type="crash_recovery",
                game_save_path="autosave.json",
                seed=42,
                timestamp="2024-01-15T15:00:00",
                command_index=100,
            )

            # Update crash recovery
            manager.update_crash_recovery(checkpoint, session_id)

            # Get crash recovery
            recovered = manager.get_crash_recovery(session_id)

            assert recovered is not None
            assert recovered.current_goal == checkpoint.current_goal
            assert recovered.command_index == checkpoint.command_index


class TestAgentCheckpointMethods:
    """Tests for Agent checkpoint methods."""

    def test_agent_to_checkpoint_dict(self):
        """Test Agent.to_checkpoint_dict serialization."""
        # Spec: Agent.to_checkpoint_dict
        from scripts.ai_agent import AgentGoal

        agent = Agent(verbose=False)
        agent.current_goal = AgentGoal.EXPLORE_DUNGEON
        agent.visited_coordinates = {(0, 0), (1, 0), (0, 1)}
        agent.current_coords = (1, 0)
        agent.direction_history = ["north", "east"]
        agent.talked_this_location = {"Merchant", "Guard"}
        agent.sub_location_moves = 15

        data = agent.to_checkpoint_dict()

        assert data["current_goal"] == "EXPLORE_DUNGEON"
        assert set(tuple(c) for c in data["visited_coordinates"]) == {(0, 0), (1, 0), (0, 1)}
        assert tuple(data["current_coords"]) == (1, 0)
        assert data["direction_history"] == ["north", "east"]
        assert set(data["talked_this_location"]) == {"Merchant", "Guard"}
        assert data["sub_location_moves"] == 15

    def test_agent_restore_from_checkpoint(self):
        """Test Agent.restore_from_checkpoint deserialization."""
        # Spec: Agent.restore_from_checkpoint
        from scripts.ai_agent import AgentGoal

        agent = Agent(verbose=False)

        data = {
            "current_goal": "EXPLORE_DUNGEON",
            "visited_coordinates": [(0, 0), (1, 0), (0, 1)],
            "current_coords": (1, 0),
            "direction_history": ["north", "east"],
            "talked_this_location": ["Merchant", "Guard"],
            "sub_location_moves": 15,
        }

        agent.restore_from_checkpoint(data)

        assert agent.current_goal == AgentGoal.EXPLORE_DUNGEON
        assert agent.visited_coordinates == {(0, 0), (1, 0), (0, 1)}
        assert agent.current_coords == (1, 0)
        assert agent.direction_history == ["north", "east"]
        assert agent.talked_this_location == {"Merchant", "Guard"}
        assert agent.sub_location_moves == 15


class TestGameSessionCheckpoint:
    """Tests for GameSession checkpoint integration."""

    def test_check_triggers_detects_changes(self):
        """Test that _check_triggers detects state changes."""
        # Spec: GameSession._check_triggers
        session = GameSession(seed=42, max_commands=100)
        session.state = AgentState()
        session.state.quests = ["New Quest"]
        session.stats = SessionStats()
        session.stats.commands_issued = 10

        prev_state = AgentState()
        prev_state.quests = []

        trigger = session._check_triggers(prev_state)

        assert trigger == CheckpointTrigger.QUEST_ACCEPT

    def test_game_session_from_checkpoint(self):
        """Test GameSession.from_checkpoint recovery."""
        # Spec: GameSession.from_checkpoint recovery
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a session and save a checkpoint
            manager = SessionManager(base_dir=tmpdir)
            session_id = manager.create_session(seed=42)

            checkpoint = AgentCheckpoint(
                current_goal="EXPLORE_OVERWORLD",
                visited_coordinates=[(0, 0), (1, 0)],
                current_coords=(1, 0),
                direction_history=["east"],
                talked_this_location=["Merchant"],
                sub_location_moves=0,
                stats={"commands_issued": 50, "locations_visited": ["Town"]},
                checkpoint_type="auto",
                game_save_path=str(Path(tmpdir) / "game_save.json"),
                seed=42,
                timestamp="2024-01-15T10:00:00",
                command_index=50,
            )

            checkpoint_id = manager.save_checkpoint(
                checkpoint, CheckpointTrigger.INTERVAL, session_id
            )

            # Restore session from checkpoint
            with patch.object(GameSession, 'start'):
                with patch.object(GameSession, '_load_game_save'):
                    restored_session = GameSession.from_checkpoint(
                        checkpoint_id, session_manager=manager
                    )

                    assert restored_session.seed == 42
                    assert restored_session.agent.current_coords == (1, 0)
                    assert restored_session.agent.visited_coordinates == {(0, 0), (1, 0)}
