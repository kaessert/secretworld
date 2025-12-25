# Implementation Plan: Add tests for `companion-quest` command validation

## Summary
The `companion-quest` command in `main.py` has proper input validation, but lacks integration tests. Add tests to `tests/test_companion_commands.py` to verify all validation cases.

## Spec
The `companion-quest <name>` command should:
1. Show usage message when no companion name provided
2. Show error when companion not in party
3. Show error when companion has no personal quest
4. Show error with bond info when quest not available (bond too low)
5. Show error when player already has the quest
6. Accept quest and add to player's quest log on success

## Tests to Add

**File:** `tests/test_companion_commands.py`

Add new class `TestCompanionQuestCommand` with tests:

1. `test_companion_quest_no_name_specified` - Shows usage: "companion-quest <name>"
2. `test_companion_quest_companion_not_in_party` - Shows "No companion named..."
3. `test_companion_quest_no_personal_quest` - Shows "<name> has no personal quest"
4. `test_companion_quest_bond_too_low` - Shows quest unavailable with bond info
5. `test_companion_quest_already_have_quest` - Shows "You already have..."
6. `test_companion_quest_success_adds_quest` - Adds quest to character.quests
7. `test_companion_quest_case_insensitive` - Matches companion name case-insensitively

Also add to `TestCompanionsInKnownCommands`:
8. `test_companion_quest_in_known_commands` - Verify command is in KNOWN_COMMANDS

## Implementation Steps

1. Add imports for Quest, QuestStatus, ObjectiveType to test file
2. Add `TestCompanionQuestCommand` class with 7 test methods following existing patterns
3. Add `test_companion_quest_in_known_commands` to existing test class
4. Run tests to verify all pass
