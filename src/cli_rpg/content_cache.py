"""ContentCache with deterministic keying for reproducible AI-generated content.

Unlike AIService._cache which keys by prompt hash (varies with prompt changes),
ContentCache keys by seed + coords + type for deterministic content across game runs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import json
import os


class ContentType(Enum):
    """Types of content that can be cached."""

    ROOM = "room"
    NPC = "npc"
    QUEST = "quest"
    ITEM = "item"


@dataclass
class ContentCache:
    """Cache for procedural content with deterministic keys.

    Keys are derived from content type + spatial coordinates.
    The seed determines which file is used for persistence.

    Key format: "{content_type}:{x}:{y}:{z}"
    File format: "{cache_dir}/content_seed_{seed}.json"
    """

    seed: int
    cache_dir: Optional[str] = None
    _cache: dict[str, dict] = field(default_factory=dict)

    def get(self, content_type: ContentType, coords: tuple[int, int, int]) -> Optional[dict]:
        """Retrieve cached content by type and coordinates.

        Args:
            content_type: The type of content (room, npc, etc.)
            coords: 3D coordinates (x, y, z)

        Returns:
            The cached data dict, or None if not found.
        """
        key = self._make_key(content_type, coords)
        return self._cache.get(key)

    def set(
        self, content_type: ContentType, coords: tuple[int, int, int], data: dict
    ) -> None:
        """Store content in the cache.

        Args:
            content_type: The type of content (room, npc, etc.)
            coords: 3D coordinates (x, y, z)
            data: The content data to cache
        """
        key = self._make_key(content_type, coords)
        self._cache[key] = data

    def _make_key(self, content_type: ContentType, coords: tuple[int, int, int]) -> str:
        """Generate a deterministic cache key.

        Args:
            content_type: The type of content
            coords: 3D coordinates (x, y, z)

        Returns:
            Key string in format "{type}:{x}:{y}:{z}"
        """
        x, y, z = coords
        return f"{content_type.value}:{x}:{y}:{z}"

    def _get_cache_path(self) -> Optional[str]:
        """Get the path for the cache file.

        Returns:
            Path string, or None if no cache_dir is set.
        """
        if self.cache_dir is None:
            return None
        return os.path.join(self.cache_dir, f"content_seed_{self.seed}.json")

    def save_to_disk(self) -> None:
        """Persist the cache to disk.

        Creates parent directories if they don't exist.
        Does nothing if cache_dir is not set.
        """
        cache_path = self._get_cache_path()
        if cache_path is None:
            return

        # Create parent directories if needed
        os.makedirs(self.cache_dir, exist_ok=True)

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2)

    def load_from_disk(self) -> None:
        """Load the cache from disk.

        If the file doesn't exist, starts with an empty cache.
        Does nothing if cache_dir is not set.
        """
        cache_path = self._get_cache_path()
        if cache_path is None:
            return

        if not os.path.isfile(cache_path):
            # No file yet - start with empty cache
            self._cache = {}
            return

        with open(cache_path, "r", encoding="utf-8") as f:
            self._cache = json.load(f)

    def clear(self) -> None:
        """Clear all cached content."""
        self._cache = {}
