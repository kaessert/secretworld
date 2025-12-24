## Active Issues

### Initial world generated leads to small world with only three locations 

When initial world is created, there are only three locations. Player can visit all of them but can't get any further.
This violated the idea that the world is infinite and automatically generated

CRITICAL there should NEVER be the possibility that the player visited every location as there should always be more locations
added and exits added so the locations added are acutally be able to be visited

### [RESOLVED] Game should ALWAYS SAVE automatically in between each step

Implemented automatic saving that triggers:
1. After successful movement to a new location
2. After combat ends (victory or successful flee)

Uses a dedicated autosave slot (`autosave_{character_name}.json`) that silently overwrites.

### [NEEDS VERIFICATION] Player still gets stuck as world created has only two locations (8d7f56f)

This dead-end issue was marked as fixed in commit 8d7f56f with on-demand world expansion. However, there are reports this may be a regression - the world may still only have exactly two exits and not expand properly. Tests should be added to verify the fix is working correctly.

See also: `issues/DEADLOCK.md` for additional context.
