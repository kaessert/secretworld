# Implementation Plan: Agent Memory System

## Task
Implement `scripts/agent/memory.py` with failure tracking for Phase 2 of the Playtesting Infrastructure.

## Spec

The memory module enables agents to learn from experience through:

1. **FailureRecord** - Track deaths/damage causes:
   - `enemy_name: str` - Enemy that caused failure
   - `location: str` - Where failure occurred
   - `cause: str` - "death", "critical_damage", "flee"
   - `timestamp: str` - When it happened
   - `health_at_failure: int` - HP when failure occurred

2. **NPCMemory** - Track NPC interactions:
   - `name: str` - NPC name
   - `location: str` - Where first met
   - `trust_level: int` - -100 to 100 (hostile to friendly)
   - `interactions: list[str]` - History of interaction types
   - `has_quest: bool` - Offered quest before
   - `last_interaction: str` - Timestamp

3. **LocationMemory** - Track location knowledge:
   - `name: str` - Location name
   - `category: str` - Location type
   - `danger_level: float` - 0.0-1.0 based on combat encounters
   - `has_secrets: bool` - Found secrets here
   - `has_treasure: bool` - Found treasure here
   - `deaths_here: int` - Number of deaths at location
   - `visits: int` - Visit count

4. **AgentMemory** - Main memory container:
   - `failures: list[FailureRecord]` - All recorded failures
   - `npc_memories: dict[str, NPCMemory]` - NPC name -> memory
   - `location_memories: dict[str, LocationMemory]` - Location name -> memory
   - `dangerous_enemies: set[str]` - Enemy types that killed agent
   - Methods: `record_failure()`, `record_npc_interaction()`, `update_location()`, `is_enemy_dangerous()`, `get_location_danger()`, `to_dict()`, `from_dict()`

## Tests (tests/test_agent_memory.py)

### FailureRecord Tests
- `test_failure_record_creation` - Create with all fields
- `test_failure_record_serialization` - to_dict/from_dict roundtrip

### NPCMemory Tests
- `test_npc_memory_creation` - Create with all fields
- `test_npc_memory_serialization` - to_dict/from_dict roundtrip
- `test_npc_memory_trust_bounds` - Trust clamped to -100..100

### LocationMemory Tests
- `test_location_memory_creation` - Create with all fields
- `test_location_memory_serialization` - to_dict/from_dict roundtrip
- `test_location_danger_calculation` - Danger increases with deaths

### AgentMemory Tests
- `test_record_failure_adds_to_list` - Failure added to failures list
- `test_record_failure_adds_dangerous_enemy` - Death adds to dangerous_enemies
- `test_record_npc_interaction_creates_memory` - New NPC creates entry
- `test_record_npc_interaction_updates_existing` - Updates existing NPC
- `test_update_location_creates_memory` - New location creates entry
- `test_update_location_increments_visits` - Visit count increases
- `test_is_enemy_dangerous_returns_true` - Returns true for killer enemies
- `test_is_enemy_dangerous_returns_false` - Returns false for unknown enemies
- `test_get_location_danger_returns_value` - Returns correct danger level
- `test_agent_memory_serialization` - Full to_dict/from_dict roundtrip

## Implementation Steps

1. Create `tests/test_agent_memory.py` with all tests (TDD)
2. Create `scripts/agent/memory.py` with dataclasses:
   - `FailureRecord` dataclass with `to_dict()`, `from_dict()`
   - `NPCMemory` dataclass with trust clamping, `to_dict()`, `from_dict()`
   - `LocationMemory` dataclass with danger tracking, `to_dict()`, `from_dict()`
   - `AgentMemory` dataclass with all methods
3. Update `scripts/agent/__init__.py` to export memory classes
4. Run tests to verify implementation

## Files to Create/Modify
- `tests/test_agent_memory.py` (new)
- `scripts/agent/memory.py` (new)
- `scripts/agent/__init__.py` (update exports)
