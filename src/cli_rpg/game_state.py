"""GameState class for managing game state and gameplay."""

import difflib
import logging
import random
from typing import Optional
from cli_rpg.models.character import Character
from cli_rpg.models.game_time import GameTime
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop
from cli_rpg.models.weather import Weather
from cli_rpg.models.companion import Companion
from cli_rpg.combat import (
    CombatEncounter,
    ai_spawn_enemy,
    spawn_enemies,
    spawn_boss,
    calculate_distance_from_origin,
)
from cli_rpg.autosave import autosave
from cli_rpg import colors
from cli_rpg.whisper import WhisperService, display_whisper
from cli_rpg.companion_banter import CompanionBanterService, format_banter
from cli_rpg.random_encounters import check_for_random_encounter
from cli_rpg.shadow_creature import check_and_trigger_shadow_attack
from cli_rpg.hallucinations import check_for_hallucination, DREAD_REDUCTION_ON_DISPEL
from cli_rpg.models.world_event import WorldEvent
from cli_rpg.world_events import (
    check_for_new_event,
    progress_events,
    get_location_event_warning,
)

# Import AI components (with optional support)
try:
    from cli_rpg.ai_service import AIService, AIServiceError
    from cli_rpg.ai_world import expand_world, expand_area
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIService = None  # type: ignore[misc, assignment]
    AIServiceError = Exception  # type: ignore[misc, assignment]
    expand_area = None  # type: ignore[assignment]

# Import fallback generation
from cli_rpg.world import generate_fallback_location

logger = logging.getLogger(__name__)

# All known commands that the game recognizes
KNOWN_COMMANDS: set[str] = {
    "look", "go", "save", "quit", "attack", "defend", "block", "flee", "status", "cast", "sneak", "bash",
    "fireball", "ice_bolt", "heal",  # Mage-specific spells
    "bless", "smite",  # Cleric-specific abilities
    "stance",  # Fighting stance command
    "inventory", "equip", "unequip", "use", "drop", "talk", "buy", "sell", "shop",
    "map", "worldmap", "help", "quests", "quest", "accept", "complete", "abandon", "lore", "rest",
    "bestiary", "dump-state", "events", "companions", "recruit", "dismiss", "companion-quest",
    "enter", "exit", "leave", "resolve", "pick", "open",
    "persuade", "intimidate", "bribe", "haggle",  # Social skills
    "search",  # Secret discovery
    "camp", "forage", "hunt",  # Wilderness survival
    "track",  # Ranger ability
}

# Dread increases by location category (darker areas = more dread)
DREAD_BY_CATEGORY: dict[str, int] = {
    "dungeon": 15,
    "cave": 12,
    "ruins": 10,
    "wilderness": 5,
    "forest": 3,
    "town": 0,  # Towns don't add dread
}
DREAD_NIGHT_BONUS = 5  # Extra dread when moving at night
DREAD_TOWN_REDUCTION = 15  # Dread reduced when entering town
DREAD_COMBAT_INCREASE = 10  # Dread increase when combat starts


def suggest_command(unknown_cmd: str, known_commands: set[str]) -> Optional[str]:
    """Suggest a similar command for typos using fuzzy matching.

    Args:
        unknown_cmd: The unrecognized command entered by the user
        known_commands: Set of valid commands to match against

    Returns:
        The most similar command if similarity >= 60%, None otherwise
    """
    matches = difflib.get_close_matches(unknown_cmd, known_commands, n=1, cutoff=0.6)
    return matches[0] if matches else None


def parse_command(command_str: str) -> tuple[str, list[str]]:
    """Parse a command string into command and arguments.

    Args:
        command_str: The command string to parse

    Returns:
        Tuple of (command, args) where command is lowercase and args is a list
        Returns ("unknown", [original_command]) for unrecognized commands
        (original_command enables 'Did you mean?' suggestions)
    """
    # Strip and lowercase the input
    command_str = command_str.strip().lower()

    # Split into parts
    parts = command_str.split()

    if not parts:
        return ("unknown", [])

    command = parts[0]
    original_command = command  # Save for error messages
    args = parts[1:]

    # Expand shorthand aliases
    aliases = {
        "g": "go", "l": "look", "a": "attack", "c": "cast",
        "d": "defend", "bl": "block", "f": "flee", "s": "status", "i": "inventory",
        "m": "map", "wm": "worldmap", "h": "help", "t": "talk", "u": "use", "e": "equip",
        "q": "quests", "dr": "drop", "r": "rest", "stats": "status",
        "b": "bestiary", "sn": "sneak", "ba": "bash", "lp": "pick", "o": "open", "sr": "search",
        # Mage spell aliases
        "fb": "fireball", "ib": "ice_bolt", "hl": "heal",
        # Cleric ability aliases
        "bs": "bless", "sm": "smite",
        # Fighting stance alias
        "st": "stance",
        # Ultra-short movement shortcuts
        "n": "go", "w": "go",
        "gn": "go", "gs": "go", "ge": "go", "gw": "go",
        # Wilderness survival aliases
        "ca": "camp", "fg": "forage", "hu": "hunt",
        # Ranger ability aliases
        "tr": "track",
    }
    raw_command = command  # Save for movement shortcut detection
    command = aliases.get(command, command)

    # Infer direction from movement shortcuts (when no args provided)
    if command == "go" and not args:
        movement_directions = {
            "n": "north", "w": "west",
            "gn": "north", "gs": "south", "ge": "east", "gw": "west"
        }
        if raw_command in movement_directions:
            args = [movement_directions[raw_command]]

    # Expand direction shorthands for go command
    if command == "go" and args:
        direction_aliases = {"n": "north", "s": "south", "e": "east", "w": "west"}
        args[0] = direction_aliases.get(args[0], args[0])

    # Validate against known commands (using module-level KNOWN_COMMANDS)
    if command not in KNOWN_COMMANDS:
        return ("unknown", [original_command])

    return (command, args)


class GameState:
    """Manages the current game state including character, location, and world.
    
    Attributes:
        current_character: The player's character
        current_location: Name of the current location
        world: Dictionary mapping location names to Location objects
        current_combat: Active combat encounter or None
    """
    
    def __init__(
        self,
        character: Character,
        world: dict[str, Location],
        starting_location: str = "Town Square",
        ai_service: Optional["AIService"] = None,
        theme: str = "fantasy"
    ):
        """Initialize game state.
        
        Args:
            character: The player's character
            world: Dictionary mapping location names to Location objects
            starting_location: Name of starting location (default: "Town Square")
            ai_service: Optional AIService for dynamic world generation
            theme: World theme for AI generation (default: "fantasy")
            
        Raises:
            TypeError: If character is not a Character instance
            ValueError: If world is empty, starting_location not in world,
                       or world connections are invalid
        """
        # Validate character
        if not isinstance(character, Character):
            raise TypeError("character must be a Character instance")
        
        # Validate world
        if not world:
            raise ValueError("world cannot be empty")
        
        # Validate starting location
        if starting_location not in world:
            raise ValueError(f"starting_location '{starting_location}' not found in world")
        
        # Note: Dangling connections (pointing to non-existent locations) are allowed.
        # These support the "infinite world" principle where all locations have
        # forward paths for exploration. When traveled to:
        # - With AI service: the destination is generated dynamically
        # - Without AI service: the move returns an error message
        
        # Set attributes
        self.current_character = character
        self.world = world
        self.current_location = starting_location
        self.ai_service = ai_service
        self.theme = theme
        self.current_combat: Optional[CombatEncounter] = None
        self.current_shop: Optional[Shop] = None  # Active shop interaction
        self.current_npc: Optional[NPC] = None  # NPC being talked to (for accept command)
        self.whisper_service = WhisperService(ai_service=ai_service)
        self.banter_service = CompanionBanterService()  # Companion banter during travel
        self.game_time = GameTime()  # Day/night cycle tracking
        self.weather = Weather()  # Weather system tracking
        self.choices: list[dict] = []  # Echo choices: tracking significant player decisions
        self.world_events: list[WorldEvent] = []  # Living world events
        self.companions: list[Companion] = []  # Party companions with bond mechanics
        self.haggle_bonus: float = 0.0  # Active haggle bonus (reset after one transaction)
        self.forage_cooldown: int = 0  # Forage command cooldown in hours
        self.hunt_cooldown: int = 0  # Hunt command cooldown in hours

    @property
    def is_in_conversation(self) -> bool:
        """Check if player is currently in conversation with an NPC.

        Returns:
            True if in conversation, False otherwise
        """
        return self.current_npc is not None
    
    def get_current_location(self) -> Location:
        """Get the current Location object.

        Returns:
            The Location object for the current location
        """
        return self.world[self.current_location]

    def _get_location_by_coordinates(
        self, coords: tuple[int, int]
    ) -> Optional[Location]:
        """Find a location by its coordinates.

        Args:
            coords: (x, y) coordinate tuple

        Returns:
            Location at those coordinates, or None if not found
        """
        for location in self.world.values():
            if location.coordinates == coords:
                return location
        return None
    
    def look(self) -> str:
        """Get a formatted description of the current location with progressive detail.

        Each look in the same location reveals more:
        - First look: Surface description (standard)
        - Second look: Environmental details
        - Third look: Hidden secrets

        Weather affects visibility:
        - Storm: Reduced visibility (truncated description, no details/secrets)
        - Fog: Obscured visibility (some exits hidden, NPC names as "???")
        - Cave locations are unaffected by weather visibility effects

        At 75%+ dread on 3rd+ look, player may discover "dread treasures" -
        powerful items revealed only to those who brave the darkness.

        Returns:
            String description with appropriate detail layers based on look count
        """
        location = self.get_current_location()
        # Increment and get look count
        look_count = self.current_character.record_look(self.current_location)
        # Get visibility level from weather, accounting for location category
        visibility = self.weather.get_visibility_level(location.category)
        result = location.get_layered_description(look_count, visibility=visibility)

        # Check for dread treasure (brave player rewards)
        from cli_rpg.brave_rewards import check_for_dread_treasure, get_discovery_message
        treasure = check_for_dread_treasure(
            dread_level=self.current_character.dread_meter.dread,
            look_count=look_count,
            location_name=self.current_location
        )
        if treasure is not None:
            if self.current_character.inventory.add_item(treasure):
                result += get_discovery_message(treasure)
            else:
                result += f"\n{colors.warning('Your inventory is full! You cannot take the treasure.')}"

        return result
    
    def is_in_combat(self) -> bool:
        """Check if combat is currently active.

        Returns:
            True if in combat, False otherwise
        """
        return self.current_combat is not None and self.current_combat.is_active

    def mark_boss_defeated(self) -> None:
        """Mark the current location's boss as defeated.

        Called after a boss is defeated in combat. Sets boss_defeated=True
        and makes the location a safe zone.
        """
        location = self.get_current_location()
        if location.boss_enemy and not location.boss_defeated:
            location.boss_defeated = True
            location.is_safe_zone = True
    
    def trigger_encounter(self, location_name: str) -> Optional[str]:
        """Potentially spawn enemies based on location.

        Uses AI-generated enemies when AIService is available, with fallback
        to template-based enemies. Can spawn 1-3 enemies depending on level.
        Enemy stats are scaled by Manhattan distance from origin.

        Args:
            location_name: Name of the location for encounter

        Returns:
            Message about encounter if triggered, None otherwise
        """
        # Check if location is a safe zone
        location = self.world.get(location_name)
        if location and location.is_safe_zone:
            return None

        # 30% chance of encounter
        if random.random() < 0.3:
            # Get current location's coordinates for distance calculation
            location = self.world.get(location_name)
            coords = location.coordinates if location else None
            distance = calculate_distance_from_origin(coords)

            if self.ai_service is not None:
                # AI-powered: use single ai_spawn_enemy for now
                # (Multi-enemy AI spawning could be added later)
                enemy = ai_spawn_enemy(
                    location_name=location_name,
                    player_level=self.current_character.level,
                    ai_service=self.ai_service,
                    theme=self.theme,
                    distance=distance,
                )
                enemies = [enemy]
            else:
                # Template-based: spawn multiple enemies
                enemies = spawn_enemies(
                    location_name=location_name,
                    level=self.current_character.level,
                    distance=distance,
                )
            self.current_combat = CombatEncounter(
                self.current_character,
                enemies=enemies,
                weather=self.weather,
                companions=self.companions,
                location_category=location.category if location else None,
            )

            # Combat increases dread
            dread_message = self.current_character.dread_meter.add_dread(DREAD_COMBAT_INCREASE)
            combat_message = self.current_combat.start()

            if dread_message:
                combat_message += f"\n{dread_message}"

            return combat_message
        return None
    
    def move(self, direction: str) -> tuple[bool, str]:
        """Move to a connected location in the specified direction.

        Uses coordinate-based movement when locations have coordinates,
        falling back to connection-based movement for legacy saves.

        Args:
            direction: The direction to move (e.g., "north", "south", etc.)

        Returns:
            Tuple of (success, message) where:
            - success is True if move was successful, False otherwise
            - message describes the result
        """
        # Block movement during conversation
        if self.is_in_conversation:
            return (False, "You're in a conversation. Say 'bye' to leave first.")

        from cli_rpg.world_grid import DIRECTION_OFFSETS

        # Track previous location for look count reset
        previous_location = self.current_location

        current = self.get_current_location()

        # Check if direction is valid (north, south, east, west)
        valid_game_directions = {"north", "south", "east", "west"}
        if direction not in valid_game_directions:
            return (False, "Invalid direction. Use: north, south, east, or west.")

        # Block movement if no connection exists in that direction
        if not current.has_connection(direction):
            return (False, "You can't go that way.")

        # Track if AI generation was attempted but failed (to inform player)
        ai_fallback_used = False

        # Use coordinate-based movement if current location has coordinates
        if current.coordinates is not None:
            # Calculate target coordinates for valid cardinal directions
            dx, dy = DIRECTION_OFFSETS[direction]
            target_coords = (current.coordinates[0] + dx, current.coordinates[1] + dy)

            # Find location at target coordinates
            target_location = self._get_location_by_coordinates(target_coords)

            if target_location is not None:
                # Location exists at target coordinates - move there
                self.current_location = target_location.name
                # Ensure bidirectional connection exists
                if not current.has_connection(direction):
                    current.add_connection(direction, target_location.name)
            else:
                # No location at target - generate one (AI or fallback)
                ai_succeeded = False
                if self.ai_service is not None and AI_AVAILABLE and expand_area is not None:
                    try:
                        logger.info(
                            f"Generating area at {target_coords} from {current.name}"
                        )
                        expand_area(
                            world=self.world,
                            ai_service=self.ai_service,
                            from_location=self.current_location,
                            direction=direction,
                            theme=self.theme,
                            target_coords=target_coords,
                        )
                        # Find the newly generated location
                        target_location = self._get_location_by_coordinates(target_coords)
                        if target_location:
                            self.current_location = target_location.name
                            ai_succeeded = True
                    except Exception as e:
                        logger.warning(f"AI area generation failed: {e}")
                        # Mark that AI was attempted but failed
                        ai_fallback_used = True

                # Use fallback generation when AI failed or is unavailable
                if not ai_succeeded:
                    try:
                        logger.info(
                            f"Generating fallback location at {target_coords} from {current.name}"
                        )
                        new_location = generate_fallback_location(
                            direction=direction,
                            source_location=current,
                            target_coords=target_coords
                        )
                        # Add to world
                        self.world[new_location.name] = new_location
                        # Add bidirectional connection from source
                        current.add_connection(direction, new_location.name)
                        # Move to new location
                        self.current_location = new_location.name
                    except Exception as e:
                        logger.error(f"Fallback location generation also failed: {e}")
                        return (False, "The path is blocked by an impassable barrier.")
        else:
            # Legacy fallback: use connection-based movement
            if not current.has_connection(direction):
                return (False, "You can't go that way.")

            destination_name = current.get_connection(direction)

            if destination_name not in self.world:
                # Try to generate it with AI if available
                if self.ai_service is not None and AI_AVAILABLE:
                    try:
                        logger.info(f"Generating missing destination: {destination_name}")
                        expand_world(
                            world=self.world,
                            ai_service=self.ai_service,
                            from_location=self.current_location,
                            direction=direction,
                            theme=self.theme,
                        )
                        # Re-read destination name after expansion (may have changed)
                        current = self.get_current_location()
                        destination_name = current.get_connection(direction)
                    except Exception as e:
                        # Log error for debugging but don't expose to player
                        logger.warning(f"AI location generation failed: {e}")
                        return (False, "The path is blocked by an impassable barrier.")
                else:
                    return (False, "The path is blocked by an impassable barrier.")

            if destination_name is None:
                return (False, "Failed to determine destination.")
            self.current_location = destination_name

        # Advance time by 1 hour for movement (+1 hour in storm)
        travel_time = 1 + self.weather.get_travel_modifier()
        self.game_time.advance(travel_time)

        # Autosave after successful movement
        try:
            autosave(self)
        except IOError:
            pass  # Silent failure - don't interrupt gameplay

        # Reset look count for previous location (fresh start on return)
        self.current_character.reset_look_count(previous_location)

        message = f"You head {direction} to {colors.location(self.current_location)}."

        # Add weather flavor text (if not clear weather)
        if self.weather.condition != "clear":
            weather_flavor = self.weather.get_flavor_text()
            message += f"\n{weather_flavor}"

        # Trigger weather transition after movement
        self.weather.transition()

        # Inform player if AI generation failed and template was used
        if ai_fallback_used:
            fallback_notice = colors.warning(
                "[AI world generation temporarily unavailable. Using template generation.]"
            )
            message += f"\n{fallback_notice}"

        # Update dread based on destination
        location = self.get_current_location()
        dread_message = self._update_dread_on_move(location)
        if dread_message:
            message += f"\n{dread_message}"

        # Check for shadow creature attack at 100% dread
        shadow_message = check_and_trigger_shadow_attack(self)
        if shadow_message:
            message += f"\n{shadow_message}"

        # Check for hallucination at high dread (only if no shadow attack)
        if not shadow_message and not self.is_in_combat():
            hallucination_message = check_for_hallucination(self)
            if hallucination_message:
                message += f"\n{hallucination_message}"

        # Check for exploration quest progress
        explore_messages = self.current_character.record_explore(self.current_location)
        for msg in explore_messages:
            message += f"\n{msg}"

        # Check for ambient whisper (only when not in combat)
        if not self.is_in_combat():
            whisper = self.whisper_service.get_whisper(
                location_category=location.category,
                character=self.current_character,
                theme=self.theme,
                is_night=self.game_time.is_night(),
                dread=self.current_character.dread_meter.dread
            )
            if whisper:
                # Display whisper with typewriter effect (immediate output)
                print()  # Blank line for spacing before whisper
                display_whisper(whisper)

        # Check for companion banter (only when not in combat and companions present)
        if not self.is_in_combat() and self.companions:
            banter = self.banter_service.get_banter(
                companions=self.companions,
                location_category=location.category,
                weather=self.weather.condition,
                is_night=self.game_time.is_night(),
                dread=self.current_character.dread_meter.dread
            )
            if banter:
                companion_name, banter_text = banter
                message += f"\n\n{format_banter(companion_name, banter_text)}"

        # Check for random encounter (replaces old trigger_encounter)
        encounter_message = check_for_random_encounter(self)
        if encounter_message:
            message += f"\n{encounter_message}"

        # Check for world event spawn
        event_message = check_for_new_event(self)
        if event_message:
            message += f"\n{event_message}"

        # Check if entering a location with active events
        event_warning = get_location_event_warning(self.current_location, self.world_events)
        if event_warning:
            message += f"\n{event_warning}"

        # Progress world events with time
        event_progress_messages = progress_events(self)
        for msg in event_progress_messages:
            message += f"\n{msg}"

        return (True, message)

    def enter(self, target_name: Optional[str] = None) -> tuple[bool, str]:
        """Enter a sub-location within the current overworld landmark.

        Args:
            target_name: Name of sub-location to enter (partial match, case-insensitive).
                         If None, uses entry_point of current location.

        Returns:
            Tuple of (success, message) where:
            - success is True if entry was successful, False otherwise
            - message describes the result including look() at new location on success
        """
        # Block during conversation
        if self.is_in_conversation:
            return (False, "You're in a conversation. Say 'bye' to leave first.")

        current = self.get_current_location()

        # Must be at an overworld location
        if not current.is_overworld:
            return (False, "You're not at an overworld location.")

        # If no target specified, use entry_point
        if target_name is None:
            if current.entry_point is None:
                return (False, "Enter where? Specify a location name.")
            target_name = current.entry_point

        # Find matching sub-location (case-insensitive partial match)
        target_lower = target_name.lower()
        matched_location: Optional[str] = None

        for sub_name in current.sub_locations:
            if sub_name.lower().startswith(target_lower) or target_lower in sub_name.lower():
                if sub_name in self.world:
                    matched_location = sub_name
                    break

        if matched_location is None:
            return (False, f"No such location: {target_name}")

        # Move to sub-location
        self.current_location = matched_location

        # Build success message with look at new location
        message = f"You enter {colors.location(matched_location)}.\n\n{self.look()}"

        # Check for boss encounter in sub-location
        sub_location = self.world[matched_location]
        if sub_location.boss_enemy and not sub_location.boss_defeated:
            # Spawn the boss
            boss = spawn_boss(
                location_name=matched_location,
                level=self.current_character.level,
                location_category=sub_location.category,
                boss_type=sub_location.boss_enemy
            )
            self.current_combat = CombatEncounter(
                self.current_character,
                enemies=[boss],
                weather=self.weather,
                companions=self.companions,
                location_category=sub_location.category,
            )
            message += f"\n\n{self.current_combat.start()}"

        return (True, message)

    def exit_location(self) -> tuple[bool, str]:
        """Exit from a sub-location back to the parent overworld landmark.

        Returns:
            Tuple of (success, message) where:
            - success is True if exit was successful, False otherwise
            - message describes the result including look() at parent on success
        """
        # Block during conversation
        if self.is_in_conversation:
            return (False, "You're in a conversation. Say 'bye' to leave first.")

        current = self.get_current_location()

        # Must have a parent location
        if current.parent_location is None:
            return (False, "You're not inside a landmark.")

        # Verify parent exists in world
        if current.parent_location not in self.world:
            return (False, f"Cannot find parent location: {current.parent_location}")

        # Move to parent location
        self.current_location = current.parent_location

        # Build success message with look at parent location
        message = f"You exit to {colors.location(self.current_location)}.\n\n{self.look()}"
        return (True, message)

    def _update_dread_on_move(self, location: Location) -> Optional[str]:
        """Update dread level when moving to a new location.

        Light sources affect dread calculation:
        - Halves dread from location category
        - Negates night dread bonus
        - Does not affect town reduction or weather/health modifiers

        Args:
            location: The destination location

        Returns:
            Milestone message if a dread threshold was crossed, None otherwise
        """
        category = location.category or "default"
        dread_meter = self.current_character.dread_meter
        has_light = self.current_character.has_active_light()

        # Towns reduce dread (unaffected by light)
        if category == "town":
            if dread_meter.dread > 0:
                dread_meter.reduce_dread(DREAD_TOWN_REDUCTION)
            # Tick light even in town
            light_message = self.current_character.tick_light()
            return light_message

        # Calculate dread increase based on category
        dread_increase = DREAD_BY_CATEGORY.get(category, 5)  # Default 5 for unknown

        # Light reduces category dread by 50%
        if has_light:
            dread_increase = dread_increase // 2

        # Night adds extra dread (negated by light)
        if self.game_time.is_night() and not has_light:
            dread_increase += DREAD_NIGHT_BONUS

        # Weather adds dread (but not in caves - you're underground)
        effective_weather = self.weather.get_effective_condition(category)
        if effective_weather != "clear":
            weather_dread = self.weather.get_dread_modifier()
            # Only apply if we have an effective weather condition
            if self.weather.condition == effective_weather:
                dread_increase += weather_dread

        # Low health adds dread (<30% health)
        if self.current_character.health < self.current_character.max_health * 0.3:
            dread_increase += 5

        # Add dread
        dread_message = dread_meter.add_dread(dread_increase)

        # Tick light and check for expiration
        light_message = self.current_character.tick_light()

        # Combine messages
        if dread_message and light_message:
            return f"{dread_message}\n{light_message}"
        return dread_message or light_message

    def record_choice(
        self,
        choice_type: str,
        choice_id: str,
        description: str,
        target: Optional[str] = None
    ) -> None:
        """Record a significant player decision.

        Args:
            choice_type: Category of choice (e.g., "combat_mercy", "dialogue", "quest")
            choice_id: Unique identifier for this choice (e.g., "spare_bandit_001")
            description: Human-readable description of the choice
            target: Optional NPC/enemy name involved (if applicable)
        """
        choice = {
            "choice_type": choice_type,
            "choice_id": choice_id,
            "description": description,
            "timestamp": self.game_time.hour,
            "location": self.current_location,
            "target": target,
        }
        self.choices.append(choice)

    def has_choice(self, choice_id: str) -> bool:
        """Check if a specific choice was made.

        Args:
            choice_id: The unique identifier of the choice to check

        Returns:
            True if the choice was recorded, False otherwise
        """
        return any(c["choice_id"] == choice_id for c in self.choices)

    def get_choices_by_type(self, choice_type: str) -> list[dict]:
        """Get all choices of a specific type.

        Args:
            choice_type: The category of choices to filter by

        Returns:
            List of choice dicts matching the specified type
        """
        return [c for c in self.choices if c["choice_type"] == choice_type]

    def to_dict(self) -> dict:
        """Serialize game state to dictionary.

        Returns:
            Dictionary containing character, current_location, world data, theme, game_time, weather, choices, world_events, and companions
        """
        return {
            "character": self.current_character.to_dict(),
            "current_location": self.current_location,
            "world": {
                name: location.to_dict()
                for name, location in self.world.items()
            },
            "theme": self.theme,
            "game_time": self.game_time.to_dict(),
            "weather": self.weather.to_dict(),
            "choices": self.choices,
            "world_events": [event.to_dict() for event in self.world_events],
            "companions": [companion.to_dict() for companion in self.companions],
            "forage_cooldown": self.forage_cooldown,
            "hunt_cooldown": self.hunt_cooldown,
        }
    
    @classmethod
    def from_dict(cls, data: dict, ai_service: Optional["AIService"] = None) -> "GameState":
        """Deserialize game state from dictionary.

        Args:
            data: Dictionary containing game state data
            ai_service: Optional AIService to enable dynamic world generation

        Returns:
            GameState instance

        Raises:
            KeyError: If required fields are missing
        """
        # Deserialize character
        character = Character.from_dict(data["character"])

        # Deserialize world
        world = {
            name: Location.from_dict(location_data)
            for name, location_data in data["world"].items()
        }

        # Get current location
        current_location = data["current_location"]

        # Get theme (default to "fantasy" for backward compatibility)
        theme = data.get("theme", "fantasy")

        # Create game state
        game_state = cls(
            character, world, current_location, ai_service=ai_service, theme=theme
        )

        # Restore game_time if present (default to 6:00 for backward compatibility)
        if "game_time" in data:
            game_state.game_time = GameTime.from_dict(data["game_time"])

        # Restore weather if present (default to clear for backward compatibility)
        if "weather" in data:
            game_state.weather = Weather.from_dict(data["weather"])

        # Restore choices if present (default to empty list for backward compatibility)
        game_state.choices = data.get("choices", [])

        # Restore world_events if present (default to empty list for backward compatibility)
        game_state.world_events = [
            WorldEvent.from_dict(event_data)
            for event_data in data.get("world_events", [])
        ]

        # Restore companions if present (default to empty list for backward compatibility)
        game_state.companions = [
            Companion.from_dict(companion_data)
            for companion_data in data.get("companions", [])
        ]

        # Restore forage/hunt cooldowns (default to 0 for backward compatibility)
        game_state.forage_cooldown = data.get("forage_cooldown", 0)
        game_state.hunt_cooldown = data.get("hunt_cooldown", 0)

        return game_state
