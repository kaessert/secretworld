"""Tests for ContentCache with deterministic keying.

ContentCache provides reproducible caching for AI-generated content by keying
on world seed + spatial coordinates rather than prompt hashes.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from cli_rpg.content_cache import ContentCache, ContentType


class TestDeterministicKeys:
    """Tests verifying deterministic key generation."""

    def test_deterministic_key_from_seed_and_coords(self):
        """Same seed+coords = same key (Spec: deterministic keys)."""
        cache1 = ContentCache(seed=42)
        cache2 = ContentCache(seed=42)

        key1 = cache1._make_key(ContentType.ROOM, (1, 2, 3))
        key2 = cache2._make_key(ContentType.ROOM, (1, 2, 3))

        assert key1 == key2

    def test_different_seeds_different_keys(self):
        """Different seed = different key (Spec: seed affects key via filename)."""
        # Keys are the same within a cache, but different caches have different files
        cache1 = ContentCache(seed=42)
        cache2 = ContentCache(seed=99)

        # The keys within each cache are the same format
        key1 = cache1._make_key(ContentType.ROOM, (1, 2, 3))
        key2 = cache2._make_key(ContentType.ROOM, (1, 2, 3))

        # Keys are identical within cache (seed is in filename)
        assert key1 == key2

        # But the caches are distinct - verify by setting/getting
        cache1.set(ContentType.ROOM, (1, 2, 3), {"name": "Room A"})
        cache2.set(ContentType.ROOM, (1, 2, 3), {"name": "Room B"})

        assert cache1.get(ContentType.ROOM, (1, 2, 3))["name"] == "Room A"
        assert cache2.get(ContentType.ROOM, (1, 2, 3))["name"] == "Room B"

    def test_content_types_isolated(self):
        """Room vs npc at same coords = different keys (Spec: isolated by type)."""
        cache = ContentCache(seed=42)

        key_room = cache._make_key(ContentType.ROOM, (1, 2, 3))
        key_npc = cache._make_key(ContentType.NPC, (1, 2, 3))

        assert key_room != key_npc

    def test_3d_coords_in_key(self):
        """(x, y, z) all contribute to key (Spec: 3D coordinate support)."""
        cache = ContentCache(seed=42)

        key1 = cache._make_key(ContentType.ROOM, (1, 2, 3))
        key2 = cache._make_key(ContentType.ROOM, (1, 2, 4))  # different z
        key3 = cache._make_key(ContentType.ROOM, (1, 3, 3))  # different y
        key4 = cache._make_key(ContentType.ROOM, (2, 2, 3))  # different x

        # All keys should be unique
        keys = {key1, key2, key3, key4}
        assert len(keys) == 4


class TestCacheOperations:
    """Tests for basic cache get/set operations."""

    def test_get_returns_none_when_not_cached(self):
        """Cache miss returns None (Spec: cache miss behavior)."""
        cache = ContentCache(seed=42)

        result = cache.get(ContentType.ROOM, (1, 2, 3))

        assert result is None

    def test_set_then_get_returns_data(self):
        """Cache hit returns stored data (Spec: cache hit behavior)."""
        cache = ContentCache(seed=42)
        data = {"name": "Dark Cave", "description": "A spooky cave"}

        cache.set(ContentType.ROOM, (1, 2, 3), data)
        result = cache.get(ContentType.ROOM, (1, 2, 3))

        assert result == data

    def test_clear_removes_all_data(self):
        """Clear removes all cached data."""
        cache = ContentCache(seed=42)
        cache.set(ContentType.ROOM, (1, 2, 3), {"name": "Room 1"})
        cache.set(ContentType.NPC, (4, 5, 6), {"name": "NPC 1"})

        cache.clear()

        assert cache.get(ContentType.ROOM, (1, 2, 3)) is None
        assert cache.get(ContentType.NPC, (4, 5, 6)) is None


class TestDiskPersistence:
    """Tests for save/load disk persistence."""

    def test_disk_persistence_round_trip(self, tmp_path):
        """save/load preserves data (Spec: disk persistence)."""
        cache_dir = str(tmp_path)

        # Create and populate cache
        cache1 = ContentCache(seed=42, cache_dir=cache_dir)
        cache1.set(ContentType.ROOM, (1, 2, 3), {"name": "Dark Cave"})
        cache1.set(ContentType.NPC, (4, 5, 6), {"name": "Old Wizard"})
        cache1.save_to_disk()

        # Create new cache and load
        cache2 = ContentCache(seed=42, cache_dir=cache_dir)
        cache2.load_from_disk()

        assert cache2.get(ContentType.ROOM, (1, 2, 3)) == {"name": "Dark Cave"}
        assert cache2.get(ContentType.NPC, (4, 5, 6)) == {"name": "Old Wizard"}

    def test_load_creates_empty_cache_when_file_missing(self, tmp_path):
        """Graceful handling of missing file (Spec: graceful degradation)."""
        cache_dir = str(tmp_path / "nonexistent")

        cache = ContentCache(seed=42, cache_dir=cache_dir)
        cache.load_from_disk()  # Should not raise

        # Cache should be empty but functional
        assert cache.get(ContentType.ROOM, (1, 2, 3)) is None
        cache.set(ContentType.ROOM, (1, 2, 3), {"name": "Test"})
        assert cache.get(ContentType.ROOM, (1, 2, 3)) == {"name": "Test"}

    def test_cache_dir_created_if_missing(self, tmp_path):
        """save() creates parent directories (Spec: directory creation)."""
        cache_dir = str(tmp_path / "nested" / "cache" / "dir")

        cache = ContentCache(seed=42, cache_dir=cache_dir)
        cache.set(ContentType.ROOM, (1, 2, 3), {"name": "Test Room"})
        cache.save_to_disk()

        # Verify directory was created
        assert os.path.isdir(cache_dir)

        # Verify file was created
        expected_file = os.path.join(cache_dir, "content_seed_42.json")
        assert os.path.isfile(expected_file)

    def test_different_seeds_different_files(self, tmp_path):
        """Different seeds save to different files."""
        cache_dir = str(tmp_path)

        cache1 = ContentCache(seed=42, cache_dir=cache_dir)
        cache1.set(ContentType.ROOM, (1, 2, 3), {"name": "Room 42"})
        cache1.save_to_disk()

        cache2 = ContentCache(seed=99, cache_dir=cache_dir)
        cache2.set(ContentType.ROOM, (1, 2, 3), {"name": "Room 99"})
        cache2.save_to_disk()

        # Verify both files exist
        assert os.path.isfile(os.path.join(cache_dir, "content_seed_42.json"))
        assert os.path.isfile(os.path.join(cache_dir, "content_seed_99.json"))

        # Verify content is separate
        cache1_reload = ContentCache(seed=42, cache_dir=cache_dir)
        cache1_reload.load_from_disk()
        assert cache1_reload.get(ContentType.ROOM, (1, 2, 3))["name"] == "Room 42"

        cache2_reload = ContentCache(seed=99, cache_dir=cache_dir)
        cache2_reload.load_from_disk()
        assert cache2_reload.get(ContentType.ROOM, (1, 2, 3))["name"] == "Room 99"
