# Implementation Summary: Persistent AI Response Cache

## What Was Implemented

### Features
Added file-based persistent caching for AI-generated content to reduce API costs across game sessions.

### Files Modified

#### 1. `src/cli_rpg/ai_config.py`
- Added `cache_file: Optional[str] = None` field to the `AIConfig` dataclass
- Updated `__post_init__()` to set default cache path (`~/.cli_rpg/cache/ai_cache.json`) when `enable_caching=True` and no explicit path provided
- Added `AI_CACHE_FILE` environment variable support in `from_env()`
- Updated `to_dict()` and `from_dict()` to serialize/deserialize `cache_file`

#### 2. `src/cli_rpg/ai_service.py`
- Added `_load_cache_from_file()` method:
  - Loads persisted cache from disk on service initialization
  - Parses JSON file and populates in-memory cache
  - Prunes expired entries based on `cache_ttl`
  - Handles file I/O errors gracefully (logs warning, continues with in-memory only)

- Added `_save_cache_to_file()` method:
  - Persists in-memory cache to disk
  - Creates parent directories if they don't exist
  - Handles file I/O errors gracefully

- Updated `__init__()` to call `_load_cache_from_file()` when caching is enabled
- Updated `_set_cached()` and `_set_cached_list()` to call `_save_cache_to_file()` after updates

### Files Created

#### 3. `tests/test_ai_cache_persistence.py`
New test file with 13 tests covering:
- `cache_file` config option works
- Default path (`~/.cli_rpg/cache/ai_cache.json`) when caching enabled
- `cache_file` is None when caching disabled
- `AI_CACHE_FILE` environment variable support
- Serialization/deserialization round-trip
- Cache file creation on first API call
- Cache persistence across AIService instances
- Expired entries pruned on load
- Graceful fallback when cache unreadable/corrupt
- Graceful fallback when cache not writable
- Cache directory auto-creation
- Cache saved after each new response
- List caching (generate_area) also persists

### Files Updated for Test Isolation

#### 4. `tests/test_ai_service.py`
- Updated `basic_config` fixture to use `tmp_path` for isolated cache file per test
- Updated 4 tests that create their own `AIConfig` to use isolated cache paths:
  - `test_generate_location_caching_enabled`
  - `test_ai_service_configurable_model`
  - `test_ai_service_configurable_temperature`
  - `test_generate_location_with_anthropic`

## Test Results

- All 53 AI-related tests pass
- Full test suite: 1054 passed, 1 skipped

## Cache File Format

```json
{
  "md5_hash_of_prompt": {
    "data": { /* cached response data */ },
    "timestamp": 1703500000.123
  }
}
```

## Design Decisions

1. **File format**: JSON for human-readability and easy debugging
2. **Cache key**: MD5 hash of prompt (same as in-memory cache)
3. **Expiration**: TTL checked both on load (prune expired) and on access
4. **Error handling**: Graceful degradation - file I/O errors log warnings but don't crash; in-memory caching continues to work
5. **Directory creation**: Automatic creation of parent directories for cache file
6. **Test isolation**: Each test gets its own temp cache file to prevent cross-test contamination

## E2E Tests Should Validate

1. Starting the game creates cache file in `~/.cli_rpg/cache/ai_cache.json`
2. Generating a location via AI and exiting, then restarting shows the cached location is used
3. Cache entries older than `cache_ttl` are refreshed via API call
4. Setting `AI_CACHE_FILE=/custom/path.json` uses that path instead
5. Setting `AI_ENABLE_CACHING=false` disables file caching
