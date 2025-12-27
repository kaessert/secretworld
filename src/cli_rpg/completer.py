"""Readline-compatible command completer for game commands.

Provides tab auto-completion for:
1. Command names: `ta<tab>` -> `talk`
2. Contextual arguments:
   - `talk <tab>` -> NPCs at current location
   - `go <tab>` -> available directions
   - `equip <tab>` -> equippable items (WEAPON/ARMOR)
   - `use <tab>` -> consumable items
   - `buy <tab>` -> shop items (when in shop)

Spec requirements from ISSUES.md lines 63-86.
"""
from typing import TYPE_CHECKING, List, Optional

# Import readline with fallback for systems where it's unavailable
try:
    import readline
except ImportError:
    readline = None  # type: ignore[assignment]

from cli_rpg.game_state import KNOWN_COMMANDS
from cli_rpg.models.item import ItemType
from cli_rpg.models.puzzle import PuzzleType

if TYPE_CHECKING:
    from cli_rpg.game_state import GameState


class CommandCompleter:
    """Readline-compatible completer for game commands.

    Implements the readline completer interface with `complete(text, state)`
    method that returns matches one at a time based on state.

    Attributes:
        _game_state: Current game state for contextual completions
        _matches: Cached list of matches for current completion
    """

    def __init__(self) -> None:
        """Initialize the completer without game state."""
        self._game_state: Optional["GameState"] = None
        self._matches: List[str] = []

    def set_game_state(self, game_state: Optional["GameState"]) -> None:
        """Set current game state for contextual completions.

        Args:
            game_state: The current GameState, or None to disable contextual completion
        """
        self._game_state = game_state

    def complete(self, text: str, state: int) -> Optional[str]:
        """Readline completer callback.

        Called by readline for each tab press. Returns the next match
        based on state (0, 1, 2, ...) until None is returned.

        Args:
            text: The text being completed (current word)
            state: The match index (0 for first match, 1 for second, etc.)

        Returns:
            The next matching completion, or None if no more matches
        """
        # On state 0, compute all matches
        if state == 0:
            self._matches = self._get_matches(text)

        # Return the state-th match, or None if exhausted
        if state < len(self._matches):
            return self._matches[state]
        return None

    def _get_matches(self, text: str) -> List[str]:
        """Get all matching completions for the given text.

        Args:
            text: The text being completed

        Returns:
            List of matching completions
        """
        # Get full line buffer from readline
        if readline is None:
            # No readline - just do command completion
            return self._complete_command(text)

        line = readline.get_line_buffer()
        begidx = readline.get_begidx()

        # Determine if we're completing a command or an argument
        if begidx == 0:
            # Completing the first word (command)
            return self._complete_command(text)
        else:
            # Completing an argument - parse the command
            parts = line[:begidx].strip().split()
            if not parts:
                return self._complete_command(text)

            command = parts[0].lower()
            return self._complete_argument(command, text)

    def _complete_command(self, text: str) -> List[str]:
        """Complete a command name.

        Args:
            text: Partial command text

        Returns:
            List of matching command names with trailing space
        """
        text_lower = text.lower()
        matches = []
        for cmd in sorted(KNOWN_COMMANDS):
            if cmd.startswith(text_lower):
                # Add trailing space to indicate completion
                matches.append(cmd + " ")
        return matches

    def _complete_argument(self, command: str, text: str) -> List[str]:
        """Complete a command argument based on command type.

        Args:
            command: The command being completed
            text: Partial argument text

        Returns:
            List of matching argument completions
        """
        if self._game_state is None:
            return []

        text_lower = text.lower()

        if command == "go":
            return self._complete_go(text_lower)
        elif command == "talk":
            return self._complete_talk(text_lower)
        elif command == "equip":
            return self._complete_equip(text_lower)
        elif command == "use":
            return self._complete_use(text_lower)
        elif command == "buy":
            return self._complete_buy(text_lower)
        elif command == "resolve":
            return self._complete_resolve(text_lower)
        elif command in ("pick", "open"):
            return self._complete_treasure(text_lower)
        elif command == "travel":
            return self._complete_travel(text_lower)
        elif command == "unlock":
            return self._complete_puzzle_by_type(text_lower, PuzzleType.LOCKED_DOOR)
        elif command == "pull":
            return self._complete_puzzle_by_type(text_lower, PuzzleType.LEVER)
        elif command == "step":
            return self._complete_puzzle_by_type(text_lower, PuzzleType.PRESSURE_PLATE)
        elif command == "answer":
            return self._complete_puzzle_by_type(text_lower, PuzzleType.RIDDLE)
        elif command == "activate":
            return self._complete_puzzle_by_type(text_lower, PuzzleType.SEQUENCE)

        return []

    def _complete_go(self, text: str) -> List[str]:
        """Complete direction for 'go' command.

        Args:
            text: Partial direction text (lowercase)

        Returns:
            List of matching directions
        """
        if self._game_state is None:
            return []

        location = self._game_state.get_current_location()

        # Provide world context for coordinate-based direction lookup
        if self._game_state.in_sub_location and self._game_state.current_sub_grid:
            directions = location.get_available_directions(
                sub_grid=self._game_state.current_sub_grid
            )
        else:
            directions = location.get_available_directions(
                world=self._game_state.world
            )

        return [d for d in directions if d.startswith(text)]

    def _complete_talk(self, text: str) -> List[str]:
        """Complete NPC name for 'talk' command.

        Args:
            text: Partial NPC name text (lowercase)

        Returns:
            List of matching NPC names
        """
        if self._game_state is None:
            return []

        location = self._game_state.get_current_location()
        npc_names = [npc.name for npc in location.npcs]

        return [name for name in npc_names if name.lower().startswith(text)]

    def _complete_equip(self, text: str) -> List[str]:
        """Complete item name for 'equip' command.

        Only returns WEAPON and ARMOR items from inventory.

        Args:
            text: Partial item name text (lowercase)

        Returns:
            List of matching equippable item names
        """
        if self._game_state is None:
            return []

        inventory = self._game_state.current_character.inventory
        equippable = [
            item.name
            for item in inventory.items
            if item.item_type in (ItemType.WEAPON, ItemType.ARMOR)
        ]

        return [name for name in equippable if name.lower().startswith(text)]

    def _complete_use(self, text: str) -> List[str]:
        """Complete item name for 'use' command.

        Only returns CONSUMABLE items from inventory.

        Args:
            text: Partial item name text (lowercase)

        Returns:
            List of matching consumable item names
        """
        if self._game_state is None:
            return []

        inventory = self._game_state.current_character.inventory
        consumables = [
            item.name
            for item in inventory.items
            if item.item_type == ItemType.CONSUMABLE
        ]

        return [name for name in consumables if name.lower().startswith(text)]

    def _complete_buy(self, text: str) -> List[str]:
        """Complete item name for 'buy' command.

        Returns shop inventory items when in a shop.

        Args:
            text: Partial item name text (lowercase)

        Returns:
            List of matching shop item names
        """
        if self._game_state is None or self._game_state.current_shop is None:
            return []

        shop = self._game_state.current_shop
        item_names = [shop_item.item.name for shop_item in shop.inventory]

        return [name for name in item_names if name.lower().startswith(text)]

    def _complete_resolve(self, text: str) -> List[str]:
        """Complete event name for 'resolve' command.

        Returns active world event names.

        Args:
            text: Partial event name text (lowercase)

        Returns:
            List of matching active event names
        """
        if self._game_state is None:
            return []

        active_events = [e for e in self._game_state.world_events if e.is_active]
        event_names = [event.name for event in active_events]

        return [name for name in event_names if name.lower().startswith(text)]

    def _complete_treasure(self, text: str) -> List[str]:
        """Complete chest name for 'pick' and 'open' commands.

        Returns treasure chest names at the current location.

        Args:
            text: Partial chest name text (lowercase)

        Returns:
            List of matching chest names
        """
        if self._game_state is None:
            return []

        location = self._game_state.get_current_location()
        if not hasattr(location, 'treasures') or not location.treasures:
            return []

        chest_names = [treasure["name"] for treasure in location.treasures]

        return [name for name in chest_names if name.lower().startswith(text)]

    def _complete_travel(self, text: str) -> List[str]:
        """Complete location name for 'travel' command.

        Returns valid fast travel destinations (named overworld locations).

        Args:
            text: Partial location name text (lowercase)

        Returns:
            List of matching destination names
        """
        if self._game_state is None:
            return []

        destinations = self._game_state.get_fast_travel_destinations()
        return [name for name in destinations if name.lower().startswith(text)]

    def _complete_puzzle_by_type(self, text: str, puzzle_type: Optional[PuzzleType] = None) -> List[str]:
        """Complete puzzle names filtered by type.

        Args:
            text: Partial puzzle name text (lowercase)
            puzzle_type: Type of puzzle to filter for, or None for all types

        Returns:
            List of matching puzzle names
        """
        if self._game_state is None:
            return []

        location = self._game_state.get_current_location()
        names = []
        for puzzle in location.puzzles:
            if puzzle_type is None or puzzle.puzzle_type == puzzle_type:
                if not puzzle.solved:
                    names.append(puzzle.name)
        return [n for n in names if n.lower().startswith(text)]


# Module-level singleton instance for use by input_handler
completer = CommandCompleter()
