# Implementation Plan: ContentCache with Deterministic Keying

## Overview
Create `src/cli_rpg/content_cache.py` to provide deterministic caching for AI-generated content. This enables reproducible worlds by caching content keyed by world seed + coordinates, separate from the existing prompt-based AIService cache.

## Spec

ContentCache is a standalone cache for procedural content that:
1. Uses deterministic keys derived from world seed + spatial coordinates
2. Stores content by content type (room, npc, quest, item)
3. Supports disk persistence (JSON format)
4. Integrates with ContentLayer for cache lookups/writes
5. Does NOT use prompts as keys (unlike AIService cache)

Key differences from AIService._cache:
- **AIService cache**: Keys by prompt hash (MD5) - varies with prompt changes
- **ContentCache**: Keys by seed + coords + type - deterministic across game runs

## Files to Create

### `src/cli_rpg/content_cache.py`
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json
import os

class ContentType(Enum):
    ROOM = "room"
    NPC = "npc"
    QUEST = "quest"
    ITEM = "item"

@dataclass
class ContentCache:
    seed: int
    cache_dir: Optional[str] = None
    _cache: dict[str, dict] = field(default_factory=dict)

    def get(self, content_type: ContentType, coords: tuple[int, int, int]) -> Optional[dict]
    def set(self, content_type: ContentType, coords: tuple[int, int, int], data: dict) -> None
    def _make_key(self, content_type: ContentType, coords: tuple[int, int, int]) -> str
    def save_to_disk(self) -> None
    def load_from_disk(self) -> None
    def clear(self) -> None
```

### `tests/test_content_cache.py`

## Tests (TDD)

| # | Test Name | Verifies |
|---|-----------|----------|
| 1 | `test_deterministic_key_from_seed_and_coords` | Same seed+coords = same key |
| 2 | `test_different_seeds_different_keys` | Different seed = different key |
| 3 | `test_get_returns_none_when_not_cached` | Cache miss returns None |
| 4 | `test_set_then_get_returns_data` | Cache hit returns stored data |
| 5 | `test_disk_persistence_round_trip` | save/load preserves data |
| 6 | `test_content_types_isolated` | room vs npc at same coords = different keys |
| 7 | `test_3d_coords_in_key` | (x, y, z) all contribute to key |
| 8 | `test_load_creates_empty_cache_when_file_missing` | Graceful handling of missing file |
| 9 | `test_cache_dir_created_if_missing` | save() creates parent directories |

## Implementation Steps

1. Create `tests/test_content_cache.py` with failing tests
2. Create `src/cli_rpg/content_cache.py`:
   - ContentType enum
   - ContentCache dataclass
   - Key format: `f"{content_type.value}:{x}:{y}:{z}"` (seed is in filename)
   - get/set methods
   - Disk persistence: `{cache_dir}/content_seed_{seed}.json`
3. Run tests until all pass
4. Update ISSUES.md Phase 4 item 12 as complete

## Key Design Decisions

- **Key format**: `"{content_type}:{x}:{y}:{z}"` - seed is per-file, not per-key
- **File location**: `{cache_dir}/content_seed_{seed}.json` (default: `~/.cli_rpg/cache/`)
- **No TTL**: Content is deterministic and permanent (world regeneration = new seed)
- **Explicit save**: Call `save_to_disk()` on GameState cleanup or save
