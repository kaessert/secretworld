# Implementation Plan: Persistent AI Response Cache

## Overview
Add file-based persistent caching for AI-generated content to reduce API costs across game sessions. Currently, the cache is in-memory only and lost when the game exits.

## Spec
- Cache AI responses to a JSON file in a configurable location (default: `~/.cli_rpg/cache/`)
- Load existing cache on AIService initialization
- Write cache entries after each new API response
- Honor existing `cache_ttl` for expiration (both in-memory and on disk)
- Add `cache_file` config option to AIConfig (default: `~/.cli_rpg/cache/ai_cache.json`)
- Gracefully handle file I/O errors (log warning, continue with in-memory only)

## Implementation Steps

### 1. Update `src/cli_rpg/ai_config.py`
- Add `cache_file: Optional[str] = None` field to AIConfig dataclass
- Default to `~/.cli_rpg/cache/ai_cache.json` when `enable_caching` is True
- Add `AI_CACHE_FILE` environment variable support in `from_env()`
- Update `to_dict()` and `from_dict()` to include cache_file

### 2. Update `src/cli_rpg/ai_service.py`
- Add `_load_cache_from_file()` method to load persisted cache on init
- Add `_save_cache_to_file()` method to persist cache after updates
- Modify `__init__()` to call `_load_cache_from_file()` if caching enabled
- Modify `_set_cached()` and `_set_cached_list()` to call `_save_cache_to_file()`
- Handle file I/O errors gracefully (log, don't crash)
- Prune expired entries when loading from disk

### 3. Add tests in `tests/test_ai_cache_persistence.py`
- Test cache file is created when caching enabled
- Test cache persists across AIService instances
- Test expired entries are pruned on load
- Test graceful fallback when cache file is unreadable/corrupt
- Test cache_file config option works

### 4. Run tests
- `pytest tests/test_ai_cache_persistence.py -v`
- `pytest tests/test_ai_service.py tests/test_ai_config.py -v`
