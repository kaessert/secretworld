# Verification: `dismiss <name>` Command

## Summary
The `dismiss <name>` command is **already fully implemented and tested**. No implementation work needed.

## Evidence

### Implementation (src/cli_rpg/main.py:1133-1148)
- Command parses companion name argument
- Case-insensitive name matching
- Removes companion from `game_state.companions`
- Returns success/error messages

### Features Present
- ✅ Basic dismiss functionality (removes companion)
- ✅ Case-insensitive name matching
- ✅ Error handling for missing name
- ✅ Error handling for companion not in party
- ✅ Confirmation dialog for high-bond companions (TRUSTED/DEVOTED)
- ✅ `non_interactive=True` mode skips confirmation
- ✅ Command registered in `KNOWN_COMMANDS` (game_state.py:56)
- ✅ Listed in help output (main.py:56)

### Test Coverage (tests/test_companion_commands.py)
- `TestDismissCommand` class (4 tests):
  - `test_dismiss_no_companion_specified`
  - `test_dismiss_companion_not_in_party`
  - `test_dismiss_success_removes_companion`
  - `test_dismiss_case_insensitive`
- `TestDismissConfirmation` class (5 tests):
  - `test_dismiss_high_bond_requires_confirmation`
  - `test_dismiss_low_bond_shows_basic_confirmation`
  - `test_dismiss_cancelled_on_no`
  - `test_dismiss_non_interactive_skips_confirmation`
  - `test_dismiss_devoted_shows_strong_warning`

---

# Suggested Next Priority

Since `dismiss` is complete, here are the smallest actionable increments from ISSUES.md:

1. **Add more recruitable NPCs** - Currently only 3 exist (Hermit, Innkeeper, Beggar). Could add 2-3 more in different location types (tavern barkeep, wandering warrior, etc.)

2. **Add companion personality to existing recruitable NPCs** - The `Companion` model supports `personality` field for combat reactions, but current recruitable NPCs don't have personalities set.

3. **Add personal quests to existing recruitable NPCs** - The companion quest system exists but recruitable NPCs don't have `personal_quest` defined.

The smallest valuable increment would be **#2 or #3** - adding personality/quests to the existing 3 recruitable NPCs to make the companion system more meaningful without adding new content.
