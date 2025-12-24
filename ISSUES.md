## Active Issues

None currently.

---

## Resolved Issues

### [RESOLVED] Initial world dead-end prevention

**Problem**: When initial world was created, there were only three locations. Player could visit all of them but couldn't get any further, violating the "infinite world" principle.

**Solution**: Implemented dead-end prevention for initial world generation:
- Default world: Forest and Cave now have dangling exits ("Deep Woods", "Crystal Cavern")
- AI-generated worlds: Post-generation logic ensures all locations have forward exploration options
- Every location now has at least 2 connections (back + forward)
- Dangling connections are allowed by design; the `move()` method handles them appropriately

**Tests**: 8 new tests in `tests/test_initial_world_dead_end_prevention.py` verify this behavior.

### [RESOLVED] Game should ALWAYS SAVE automatically in between each step

Implemented automatic saving that triggers:
1. After successful movement to a new location
2. After combat ends (victory or successful flee)

Uses a dedicated autosave slot (`autosave_{character_name}.json`) that silently overwrites.

### [RESOLVED] Player stuck with only two locations (8d7f56f)

**Problem**: World was not automatically expanding; initial world had only two exits.

**Solution**: Fixed with on-demand world expansion and initial world dead-end prevention. The world now properly expands when players explore dangling connections (with AI service) and starts with forward exploration options.

See also: `issues/DEADLOCK.md` (now resolved).
