## Active Issues

### `complete` command not recognized
**Status**: OPEN

**Description**: The `complete <quest>` command is documented in both the README and in-game help text, but the game does not recognize it. When users type `complete` or `complete <questname>`, they receive "Unknown command. Type 'help' for a list of commands."

**Steps to Reproduce**:
1. Create a new character
2. Type `help` to see the list of commands (shows `complete <quest>` as a valid command)
3. Talk to an NPC with `talk merchant`
4. Type `complete test` or just `complete`
5. Observe "Unknown command" error

**Expected Behavior**: The `complete` command should either:
- Work as documented (turn in a completed quest to the current NPC), or
- Provide a helpful error message like "Complete which quest? Specify a quest name." when no argument is given

**Actual Behavior**: The command is not recognized at all and returns "Unknown command."

**Note**: The similar `accept` command works correctly - it returns "You need to talk to an NPC first" when not talking to an NPC, and "Merchant doesn't offer any quests" when talking to a merchant. This suggests the `complete` command handler may be missing from the command parser.

## Resolved Issues

### AI-generated content expansion
**Status**: RESOLVED

All AI-generated content features have been implemented:
- ✅ NPC conversations (AI-generated dialogue that persists to NPC greetings)
- ✅ Monsters/enemies (AI-generated with descriptions and attack flavor text)
- ✅ Item catalogue (weapons, armor, consumables) - `AIService.generate_item()` method
- ✅ Lore and world history - `AIService.generate_lore()` method

### Map misaligned and confusing
**Status**: RESOLVED

The map alignment issue with colored markers has been fixed. The player's `@` marker now aligns correctly with column headers and other location markers. Additionally, available exits are now displayed below the map legend (e.g., "Exits: east, north").


