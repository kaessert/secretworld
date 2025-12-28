"""Session manager for agent checkpoint persistence.

Manages checkpoint directories, files, and crash recovery for
simulation sessions.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.agent_checkpoint import AgentCheckpoint
from scripts.checkpoint_triggers import CheckpointTrigger


class SessionManager:
    """Manages checkpoint directories and files.

    Handles session creation, checkpoint saving/loading, and crash recovery
    for agent simulation sessions.

    Attributes:
        base_dir: Base directory for all session data.
    """

    def __init__(self, base_dir: str = "simulation_saves"):
        """Initialize session manager.

        Args:
            base_dir: Base directory for storing session data.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, seed: int) -> str:
        """Create a new session directory.

        Args:
            seed: RNG seed for the session.

        Returns:
            Unique session ID.
        """
        # Generate unique session ID with timestamp and seed
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}_seed{seed}_{uuid.uuid4().hex[:8]}"

        # Create session directory
        session_path = self.base_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)

        # Create checkpoints subdirectory
        (session_path / "checkpoints").mkdir(exist_ok=True)

        # Write session metadata
        metadata = {
            "session_id": session_id,
            "seed": seed,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }
        metadata_path = session_path / "session.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))

        return session_id

    def _get_session_path(self, session_id: str) -> Path:
        """Get path to session directory.

        Args:
            session_id: Session identifier.

        Returns:
            Path to session directory.
        """
        return self.base_dir / session_id

    def save_checkpoint(
        self,
        checkpoint: AgentCheckpoint,
        trigger: CheckpointTrigger,
        session_id: str,
    ) -> str:
        """Save a checkpoint to disk.

        Args:
            checkpoint: AgentCheckpoint to save.
            trigger: Trigger type that caused this checkpoint.
            session_id: Session to save checkpoint for.

        Returns:
            Unique checkpoint ID.
        """
        session_path = self._get_session_path(session_id)
        checkpoints_path = session_path / "checkpoints"
        checkpoints_path.mkdir(parents=True, exist_ok=True)

        # Generate checkpoint ID
        checkpoint_id = (
            f"cp_{checkpoint.command_index:06d}_{trigger.name.lower()}_"
            f"{uuid.uuid4().hex[:6]}"
        )

        # Prepare checkpoint data with metadata
        checkpoint_data = checkpoint.to_dict()
        checkpoint_data["checkpoint_id"] = checkpoint_id
        checkpoint_data["trigger"] = trigger.name
        checkpoint_data["saved_at"] = datetime.now().isoformat()

        # Save checkpoint file
        checkpoint_path = checkpoints_path / f"{checkpoint_id}.json"
        checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> AgentCheckpoint:
        """Load a checkpoint from disk.

        Args:
            checkpoint_id: Checkpoint identifier.

        Returns:
            Loaded AgentCheckpoint.

        Raises:
            FileNotFoundError: If checkpoint file doesn't exist.
        """
        # Search for checkpoint in all sessions
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue

            checkpoint_path = session_dir / "checkpoints" / f"{checkpoint_id}.json"
            if checkpoint_path.exists():
                data = json.loads(checkpoint_path.read_text())
                return AgentCheckpoint.from_dict(data)

        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

    def list_checkpoints(self, session_id: str) -> list[dict]:
        """List all checkpoints for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of checkpoint metadata dictionaries, sorted by command_index.
        """
        session_path = self._get_session_path(session_id)
        checkpoints_path = session_path / "checkpoints"

        if not checkpoints_path.exists():
            return []

        checkpoints = []
        for checkpoint_file in checkpoints_path.glob("*.json"):
            if checkpoint_file.name == "crash_recovery.json":
                continue  # Skip crash recovery file

            data = json.loads(checkpoint_file.read_text())
            checkpoints.append({
                "checkpoint_id": data.get("checkpoint_id", checkpoint_file.stem),
                "command_index": data.get("command_index", 0),
                "timestamp": data.get("timestamp", ""),
                "saved_at": data.get("saved_at", ""),
                "trigger": data.get("trigger", ""),
                "checkpoint_type": data.get("checkpoint_type", ""),
            })

        # Sort by command_index
        checkpoints.sort(key=lambda x: x["command_index"])
        return checkpoints

    def update_crash_recovery(
        self,
        checkpoint: AgentCheckpoint,
        session_id: str,
    ) -> None:
        """Update crash recovery checkpoint.

        Overwrites the previous crash recovery checkpoint with the latest state.

        Args:
            checkpoint: Current agent checkpoint.
            session_id: Session identifier.
        """
        session_path = self._get_session_path(session_id)
        checkpoints_path = session_path / "checkpoints"
        checkpoints_path.mkdir(parents=True, exist_ok=True)

        # Prepare checkpoint data
        checkpoint_data = checkpoint.to_dict()
        checkpoint_data["checkpoint_id"] = "crash_recovery"
        checkpoint_data["trigger"] = CheckpointTrigger.CRASH_RECOVERY.name
        checkpoint_data["saved_at"] = datetime.now().isoformat()

        # Overwrite crash recovery file
        crash_recovery_path = checkpoints_path / "crash_recovery.json"
        crash_recovery_path.write_text(json.dumps(checkpoint_data, indent=2))

    def get_crash_recovery(self, session_id: str) -> Optional[AgentCheckpoint]:
        """Get crash recovery checkpoint if available.

        Args:
            session_id: Session identifier.

        Returns:
            AgentCheckpoint if crash recovery exists, None otherwise.
        """
        session_path = self._get_session_path(session_id)
        crash_recovery_path = session_path / "checkpoints" / "crash_recovery.json"

        if not crash_recovery_path.exists():
            return None

        data = json.loads(crash_recovery_path.read_text())
        return AgentCheckpoint.from_dict(data)

    def get_latest_session(self) -> Optional[str]:
        """Get the most recently created session ID.

        Returns:
            Session ID of the latest session, or None if no sessions exist.
        """
        sessions = []
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue

            metadata_path = session_dir / "session.json"
            if metadata_path.exists():
                data = json.loads(metadata_path.read_text())
                sessions.append({
                    "session_id": data.get("session_id", session_dir.name),
                    "created_at": data.get("created_at", ""),
                })

        if not sessions:
            return None

        # Sort by creation time and return latest
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions[0]["session_id"]
