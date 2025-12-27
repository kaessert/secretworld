# Plan: Update ISSUES.md - Mark NPC Art Feature as RESOLVED

## Summary
The "Unique AI-generated ASCII art per entity" feature is **already fully implemented**. ISSUES.md incorrectly lists "NPC art stored with NPC data" and "Consistent art for all entity types" as remaining work, but all code, tests, and serialization are complete.

## Evidence of Completion

### NPC Art Implementation
- `NPC.ascii_art` field exists (npc.py:42)
- Serialization in `to_dict()` (npc.py:252-254) and `from_dict()` (npc.py:284)
- Generation on first talk (main.py:1226-1246)
- AI generation via `generate_npc_ascii_art()` (ai_service.py:2167-2204)
- Fallback templates in `npc_art.py`
- **24 tests passing** in `tests/test_npc_ascii_art.py`

### Location Art Implementation
- `Location.ascii_art` field exists (location.py:40)
- Serialization in `to_dict()` (location.py:350-352) and `from_dict()` (location.py:418-419, 460)
- Generation during world expansion (ai_world.py:345-373, 447-452, 559-564, 707-712)
- AI generation via `generate_location_ascii_art()` (ai_service.py:1492+)
- Fallback templates in `location_art.py`

### Monster Art Implementation (Already marked complete in ISSUES.md)
- Stored in bestiary by monster name
- Generated on first combat encounter
- Displayed via `bestiary` command

## Task: Update ISSUES.md

Change section at line 482:

**FROM:**
```markdown
### Unique AI-generated ASCII art per entity
**Status**: ACTIVE

**Implemented**:
- Monster art stored in bestiary by monster name
- First encounter generates and caches art in bestiary
- Subsequent encounters reuse cached art
- `bestiary` command displays discovered monster art

**Remaining**:
- NPC art stored with NPC data in location
- Consistent art for all entity types
```

**TO:**
```markdown
### Unique AI-generated ASCII art per entity
**Status**: RESOLVED
**Date Resolved**: 2025-12-27

**Implemented**:
- Monster art stored in bestiary by monster name
- First encounter generates and caches art in bestiary
- Subsequent encounters reuse cached art
- `bestiary` command displays discovered monster art
- NPC art stored with NPC object, generated on first talk, persisted via save/load
- Location art generated during world creation/expansion, persisted with location data
- All three entity types follow consistent pattern: field + AI generation + fallback templates + serialization
- 24 NPC art tests passing in `tests/test_npc_ascii_art.py`
```

## Files to Modify
- `ISSUES.md`: Update the section (lines 482-494)

## No Tests Needed
Documentation update only. All functionality already tested and passing.
