"""GameState class for managing game state and gameplay."""

import difflib
import logging
import random
from typing import Optional, TYPE_CHECKING
from cli_rpg.models.character import Character

if TYPE_CHECKING:
    from cli_rpg.world_grid import SubGrid
    from cli_rpg.wfc_chunks import ChunkManager
    from cli_rpg.background_gen import BackgroundGenerationQueue
    from cli_rpg.models.quest import Quest
from cli_rpg.models.game_time import GameTime
from cli_rpg.models.location import Location
from cli_rpg.models.npc import NPC
from cli_rpg.models.shop import Shop
from cli_rpg.models.weather import Weather
from cli_rpg.models.companion import Companion
from cli_rpg.models.faction import Faction
from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.generation_context import GenerationContext
from cli_rpg.models.quest_outcome import QuestOutcome
from cli_rpg.models.world_state import WorldStateManager
from cli_rpg.models.economy import EconomyState
from cli_rpg.models.quest_network import QuestNetworkManager
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
from cli_rpg.ambient_sounds import AmbientSoundService, format_ambient_sound
from cli_rpg.random_encounters import check_for_random_encounter
from cli_rpg.shadow_creature import check_and_trigger_shadow_attack
from cli_rpg.hallucinations import check_for_hallucination, DREAD_REDUCTION_ON_DISPEL
from cli_rpg.models.world_event import WorldEvent
from cli_rpg.world_events import (
    check_for_new_event,
    progress_events,
    get_location_event_warning,
)
from cli_rpg.secrets import check_passive_detection
from cli_rpg.location_noise import LocationNoiseManager

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

# Import named location trigger logic and clustering
from cli_rpg.world_tiles import (
    get_unnamed_location_template,
    TERRAIN_TO_CATEGORY,
    get_cluster_category_bias,
    should_force_enterable_category,
    get_forced_enterable_category,
    ENTERABLE_CATEGORIES,
)

logger = logging.getLogger(__name__)

# All known commands that the game recognizes
KNOWN_COMMANDS: set[str] = {
    "look", "go", "save", "quit", "attack", "defend", "block", "parry", "flee", "status", "cast", "sneak", "bash", "hide",
    "fireball", "ice_bolt", "heal",  # Mage-specific spells
    "bless", "smite",  # Cleric-specific abilities
    "stance",  # Fighting stance command
    "inventory", "equip", "unequip", "use", "drop", "talk", "buy", "sell", "shop",
    "map", "worldmap", "help", "quests", "quest", "accept", "complete", "abandon", "lore", "rest",
    "bestiary", "dump-state", "events", "companions", "recruit", "dismiss", "companion-quest",
    "enter", "exit", "leave", "resolve", "pick", "open",
    "persuade", "intimidate", "bribe", "haggle",  # Social skills
    "search",  # Secret discovery
    "camp", "forage", "hunt", "gather", "craft", "recipes",  # Wilderness survival & crafting
    "track",  # Ranger ability
    "companion", "summon", "feed", "tame",  # Ranger animal companion commands
    "proficiency",  # Weapon proficiency display
    "reputation",  # Faction reputation display
    "travel",  # Fast travel to discovered named locations
    "unlock", "pull", "step", "answer", "activate",  # Puzzle commands
}

# Discovery milestone XP rewards (per SubGrid)
MILESTONE_XP_FIRST_SECRET = 25
MILESTONE_XP_ALL_TREASURES = 25
MILESTONE_XP_BOSS_DEFEATED = 25

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
        "b": "bestiary", "sn": "sneak", "ba": "bash", "hd": "hide", "lp": "pick", "o": "open", "sr": "search", "prof": "proficiency", "pa": "parry",
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
        "ca": "camp", "fg": "forage", "hu": "hunt", "ga": "gather",
        # Crafting alias
        "cr": "craft",
        # Ranger ability aliases
        "tr": "track",
        # Faction reputation alias
        "rep": "reputation",
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


def calculate_sneak_success_chance(character: "Character") -> int:
    """Calculate sneak success percentage for exploration.

    Formula: 50% + (DEX * 2%) - (armor defense * 5%) - (15% if lit)
    Capped between 10% and 90%.

    Args:
        character: The player character

    Returns:
        Success chance as integer percentage (10-90)
    """
    base_chance = 50
    dex_bonus = character.dexterity * 2

    # Armor penalty
    armor_penalty = 0
    if character.inventory.equipped_armor:
        armor_penalty = character.inventory.equipped_armor.defense_bonus * 5

    # Light penalty
    light_penalty = 15 if character.light_remaining > 0 else 0

    total = base_chance + dex_bonus - armor_penalty - light_penalty
    return max(10, min(90, total))


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
        theme: str = "fantasy",
        chunk_manager: Optional["ChunkManager"] = None,
    ):
        """Initialize game state.

        Args:
            character: The player's character
            world: Dictionary mapping location names to Location objects
            starting_location: Name of starting location (default: "Town Square")
            ai_service: Optional AIService for dynamic world generation
            theme: World theme for AI generation (default: "fantasy")
            chunk_manager: Optional ChunkManager for WFC terrain generation

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
        self.ambient_sound_service = AmbientSoundService()  # Ambient sounds in SubGrids
        self.game_time = GameTime()  # Day/night cycle tracking
        self.weather = Weather()  # Weather system tracking
        self.choices: list[dict] = []  # Echo choices: tracking significant player decisions
        self.world_events: list[WorldEvent] = []  # Living world events
        self.companions: list[Companion] = []  # Party companions with bond mechanics
        self.haggle_bonus: float = 0.0  # Active haggle bonus (reset after one transaction)
        self.forage_cooldown: int = 0  # Forage command cooldown in hours
        self.hunt_cooldown: int = 0  # Hunt command cooldown in hours
        self.gather_cooldown: int = 0  # Gather command cooldown in hours
        self.is_sneaking: bool = False  # Rogue exploration sneak mode
        self.factions: list[Faction] = []  # Faction reputation tracking
        self.in_sub_location: bool = False  # True when inside a SubGrid
        self.current_sub_grid: Optional["SubGrid"] = None  # Active sub-grid when inside one
        self.chunk_manager = chunk_manager  # Optional WFC chunk manager for terrain
        # Layered context caching (Step 6-7 of layered query architecture)
        self.world_context: Optional[WorldContext] = None  # Layer 1: World theme context
        self.region_contexts: dict[tuple[int, int], RegionContext] = {}  # Layer 2: Region contexts by coords
        # Named location trigger counter (tracks tiles since last named POI)
        self.tiles_since_named: int = 0
        # Enterable location trigger counter (tracks tiles since last enterable location)
        self.tiles_since_enterable: int = 0
        # Dream cooldown tracking (hour of last dream, None if never dreamed)
        self.last_dream_hour: Optional[int] = None
        # Quest outcome history for NPC reactions
        self.quest_outcomes: list[QuestOutcome] = []
        # Visibility system: tiles the player has seen (within visibility radius)
        self.seen_tiles: set[tuple[int, int]] = set()
        # World state tracking for persistent world changes
        self.world_state_manager = WorldStateManager()
        # Background generation queue for pre-generating adjacent locations
        self.background_gen_queue: Optional["BackgroundGenerationQueue"] = None
        # Economy system for dynamic supply/demand pricing
        self.economy_state = EconomyState()
        # Quest network for chain/dependency tracking
        self.quest_network = QuestNetworkManager()
        # Location noise manager for deterministic location density
        # Uses world seed from chunk_manager if available, otherwise random
        world_seed = chunk_manager.world_seed if chunk_manager else random.randint(0, 2**31)
        self.location_noise_manager = LocationNoiseManager(world_seed=world_seed)
        # Pending dialogue choice: True when waiting for player to select tone (1/2/3)
        self.pending_dialogue_choice: bool = False

    @property
    def is_in_conversation(self) -> bool:
        """Check if player is currently in conversation with an NPC.

        Returns:
            True if in conversation, False otherwise
        """
        return self.current_npc is not None
    
    def get_current_location(self) -> Location:
        """Get the current Location object.

        When inside a sub-grid, returns the location from the sub-grid.
        Otherwise returns the location from the overworld.

        Returns:
            The Location object for the current location
        """
        if self.in_sub_location and self.current_sub_grid is not None:
            loc = self.current_sub_grid.get_by_name(self.current_location)
            if loc is not None:
                return loc
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

    def calculate_visibility_radius(self, coords: tuple[int, int]) -> int:
        """Calculate visibility radius from terrain + PER bonus.

        The visibility radius determines how many tiles the player can see
        from their current position. Base radius depends on terrain type,
        with bonuses from standing on mountains and high Perception.

        Args:
            coords: (x, y) coordinate tuple for position

        Returns:
            Total visibility radius in tiles (Manhattan distance)
        """
        from cli_rpg.world_tiles import (
            get_visibility_radius,
            MOUNTAIN_VISIBILITY_BONUS,
        )

        # Get terrain at current position
        terrain = "plains"
        if self.chunk_manager:
            terrain = self.chunk_manager.get_tile_at(*coords)

        # Base radius from terrain
        base_radius = get_visibility_radius(terrain)

        # Mountain standing bonus (can see far from peaks)
        if terrain == "mountain":
            base_radius += MOUNTAIN_VISIBILITY_BONUS

        # Perception bonus: +1 per 5 PER above 10
        per_bonus = max(0, (self.current_character.perception - 10) // 5)

        return base_radius + per_bonus

    def update_visibility(self, coords: tuple[int, int]) -> None:
        """Update seen_tiles based on current position and terrain.

        Calculates tiles visible from the given position based on terrain
        visibility radius and Perception stat, then adds them to seen_tiles.

        Args:
            coords: (x, y) coordinate tuple for player position
        """
        from cli_rpg.world_grid import get_tiles_in_radius

        radius = self.calculate_visibility_radius(coords)
        visible = get_tiles_in_radius(coords[0], coords[1], radius)
        self.seen_tiles.update(visible)

    def look(self) -> str:
        """Get a formatted description of the current location with progressive detail.

        Each look in the same location reveals more:
        - First look: Surface description (standard)
        - Second look: Environmental details
        - Third look: Hidden secrets

        Weather affects visibility:
        - Storm: Reduced visibility (truncated description, no details/secrets)
        - Fog: Obscured visibility (some exits hidden)
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
        # Pass chunk_manager and world/sub_grid for exit direction calculation
        result = location.get_layered_description(
            look_count,
            visibility=visibility,
            chunk_manager=self.chunk_manager,
            world=self.world if not self.in_sub_location else None,
            sub_grid=self.current_sub_grid if self.in_sub_location else None,
        )

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

    def _check_and_report_passive_secrets(self, location: Location) -> Optional[str]:
        """Check for passive secret detection and return message if found.

        Uses the character's Perception stat to automatically detect secrets
        with thresholds at or below their PER value.

        Args:
            location: The location to check for secrets

        Returns:
            Formatted message about discovered secrets, or None if none found
        """
        if not self.current_character:
            return None
        detected = check_passive_detection(self.current_character, location)
        if not detected:
            return None
        lines = [f"{colors.success('You notice:')} {s['description']}" for s in detected]
        return "\n".join(lines)

    def check_and_award_milestones(self, event_type: str) -> Optional[str]:
        """Check and award discovery milestones based on event type.

        Milestones are tracked per-SubGrid and only awarded once per SubGrid.
        Each milestone awards XP and displays a celebration message.

        Args:
            event_type: Type of event that triggered the check:
                - "secret": First secret discovered
                - "treasure": All treasures opened
                - "boss": Boss defeated

        Returns:
            Celebration message if milestone awarded, None otherwise.
        """
        # Milestones only apply when inside a SubGrid
        if not self.in_sub_location or self.current_sub_grid is None:
            return None

        sub_grid = self.current_sub_grid

        if event_type == "secret":
            # First secret found milestone
            if sub_grid.first_secret_found:
                return None  # Already awarded
            sub_grid.first_secret_found = True
            self.current_character.gain_xp(MILESTONE_XP_FIRST_SECRET)
            return (
                f"{colors.heal('★ FIRST SECRET DISCOVERED! ★')} "
                f"You've found your first secret in {sub_grid.parent_name}! "
                f"+{MILESTONE_XP_FIRST_SECRET} XP"
            )

        elif event_type == "treasure":
            # All treasures opened milestone
            if sub_grid.all_treasures_opened:
                return None  # Already awarded
            if not sub_grid.are_all_treasures_opened():
                return None  # Not all treasures opened yet
            sub_grid.all_treasures_opened = True
            self.current_character.gain_xp(MILESTONE_XP_ALL_TREASURES)
            return (
                f"{colors.heal('★ ALL TREASURES FOUND! ★')} "
                f"You've opened every treasure in {sub_grid.parent_name}! "
                f"+{MILESTONE_XP_ALL_TREASURES} XP"
            )

        elif event_type == "boss":
            # Boss defeated milestone
            if sub_grid.boss_milestone_awarded:
                return None  # Already awarded
            # Verify boss was actually defeated
            location = self.get_current_location()
            if not location.boss_defeated:
                return None  # Boss not defeated yet
            sub_grid.boss_milestone_awarded = True
            self.current_character.gain_xp(MILESTONE_XP_BOSS_DEFEATED)
            return (
                f"{colors.heal('★ BOSS VANQUISHED! ★')} "
                f"You've defeated the boss of {sub_grid.parent_name}! "
                f"+{MILESTONE_XP_BOSS_DEFEATED} XP"
            )

        return None

    def is_in_combat(self) -> bool:
        """Check if combat is currently active.

        Returns:
            True if in combat, False otherwise
        """
        return self.current_combat is not None and self.current_combat.is_active

    def mark_boss_defeated(self) -> None:
        """Mark the current location's boss as defeated.

        Called after a boss is defeated in combat. Sets boss_defeated=True
        and makes the location a safe zone. Also records the defeat in the
        world state manager for permanent tracking.
        """
        location = self.get_current_location()
        if location.boss_enemy and not location.boss_defeated:
            location.boss_defeated = True
            location.is_safe_zone = True
            # Record in world state manager for permanent tracking
            self.world_state_manager.record_boss_defeated(
                boss_name=location.boss_enemy,
                location=location.name,
                timestamp=self.game_time.total_hours,
            )
    
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
                game_state=self,
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

        # Handle movement inside sub-location grid (supports up/down)
        if self.in_sub_location and self.current_sub_grid is not None:
            return self._move_in_sub_grid(direction)

        # Overworld only allows 2D movement - block up/down
        if direction in ("up", "down"):
            return (False, "You can only go up or down inside buildings and dungeons.")

        from cli_rpg.world_grid import DIRECTION_OFFSETS

        # Track previous location for look count reset
        previous_location = self.current_location

        current = self.get_current_location()

        # Check if direction is valid (north, south, east, west)
        valid_game_directions = {"north", "south", "east", "west"}
        if direction not in valid_game_directions:
            self.is_sneaking = False  # Clear sneaking mode on any move attempt
            return (False, "Invalid direction. Use: north, south, east, or west.")

        # Track if AI generation was attempted but failed (to inform player)
        ai_fallback_used = False

        # Require coordinates for movement
        if current.coordinates is None:
            self.is_sneaking = False
            return (False, "Cannot navigate - location has no coordinates.")

        # Calculate target coordinates
        dx, dy = DIRECTION_OFFSETS[direction]
        target_coords = (current.coordinates[0] + dx, current.coordinates[1] + dy)

        # Check WFC terrain passability (when chunk_manager available)
        if self.chunk_manager is not None:
            from cli_rpg.world_tiles import is_passable

            # Set region context for biased terrain generation before chunk lookup
            # This ensures new chunks use terrain weights appropriate for the region
            region_ctx = self.get_or_create_region_context(
                target_coords, current.terrain or "wilderness"
            )
            self.chunk_manager.set_region_context(region_ctx)

            terrain = self.chunk_manager.get_tile_at(*target_coords)
            if not is_passable(terrain):
                self.is_sneaking = False
                return (False, f"The {terrain} ahead is impassable.")

        # Find location at target coordinates
        target_location = self._get_location_by_coordinates(target_coords)

        if target_location is not None:
            # Location exists at target coordinates - move there
            self.current_location = target_location.name
            # Update tiles_since_named counter based on existing location
            if target_location.is_named:
                self.tiles_since_named = 0
            else:
                self.tiles_since_named += 1
            # Update tiles_since_enterable counter based on existing location
            if target_location.category in ENTERABLE_CATEGORIES:
                self.tiles_since_enterable = 0
            else:
                self.tiles_since_enterable += 1
        else:
            # No location at target - generate new location
            terrain = None
            if self.chunk_manager is not None:
                # Get terrain from WFC for location generation
                terrain = self.chunk_manager.get_tile_at(*target_coords)

            # Determine if this should be a named location (POI) or unnamed (terrain filler)
            # Uses noise-based location density for natural clustering
            generate_named = self.location_noise_manager.should_spawn_location(
                target_coords[0],
                target_coords[1],
                terrain or "plains"
            )

            # Force named location if we need to force an enterable location
            # (enterable locations like dungeons, caves must be named POIs)
            if not generate_named and should_force_enterable_category(self.tiles_since_enterable):
                generate_named = True
                logger.info(
                    f"Forcing named location at {target_coords} to generate "
                    f"enterable location after {self.tiles_since_enterable} tiles"
                )

            if not generate_named:
                # Generate unnamed location from template (fast, no AI)
                try:
                    name_template, desc_template = get_unnamed_location_template(
                        terrain or "plains"
                    )
                    category = TERRAIN_TO_CATEGORY.get(terrain or "plains", "wilderness")
                    new_location = Location(
                        name=f"{name_template} ({target_coords[0]},{target_coords[1]})",
                        description=desc_template,
                        coordinates=target_coords,
                        category=category,
                        terrain=terrain,
                        is_named=False,
                        is_overworld=True,  # Enable enter command from this location
                    )
                    self.world[new_location.name] = new_location
                    self.current_location = new_location.name
                    self.tiles_since_named += 1
                    logger.info(
                        f"Generated unnamed location '{new_location.name}' at {target_coords}"
                    )
                except Exception as e:
                    logger.error(f"Unnamed location generation failed: {e}")
                    self.is_sneaking = False
                    return (False, "The path is blocked by an impassable barrier.")
            else:
                # Generate named location via AI or fallback
                # First, check if we need to force an enterable category
                if should_force_enterable_category(self.tiles_since_enterable):
                    category_hint = get_forced_enterable_category(terrain or "plains")
                    logger.info(
                        f"Forcing enterable category '{category_hint}' after "
                        f"{self.tiles_since_enterable} tiles without enterable location"
                    )
                else:
                    # Otherwise, check if we should cluster with nearby locations
                    category_hint = get_cluster_category_bias(self.world, target_coords)

                ai_succeeded = False

                # Check background generation cache first
                cached_data = None
                if self.background_gen_queue is not None:
                    cached_data = self.background_gen_queue.pop_cached(target_coords)

                if cached_data is not None:
                    # Use pre-generated location from cache
                    try:
                        logger.info(
                            f"Using cached location data for {target_coords}"
                        )
                        new_location = Location(
                            name=cached_data.get("name", f"Location ({target_coords[0]},{target_coords[1]})"),
                            description=cached_data.get("description", "A mysterious place."),
                            coordinates=target_coords,
                            category=cached_data.get("category", "wilderness"),
                            terrain=terrain,
                            is_named=True,
                            is_overworld=True,
                        )
                        self.world[new_location.name] = new_location
                        self.current_location = new_location.name
                        ai_succeeded = True
                    except Exception as e:
                        logger.warning(f"Failed to use cached location: {e}")
                        # Fall through to normal generation

                if not ai_succeeded and self.ai_service is not None and AI_AVAILABLE and expand_area is not None:
                    try:
                        logger.info(
                            f"Generating named area at {target_coords} from {current.name}"
                        )
                        # Get layered context for AI generation
                        world_ctx = self.get_or_create_world_context()
                        region_ctx = self.get_or_create_region_context(
                            target_coords, terrain or "wilderness"
                        )
                        expand_area(
                            world=self.world,
                            ai_service=self.ai_service,
                            from_location=self.current_location,
                            direction=direction,
                            theme=self.theme,
                            target_coords=target_coords,
                            world_context=world_ctx,
                            region_context=region_ctx,
                            terrain_type=terrain,
                            category_hint=category_hint,  # Pass clustering hint
                        )
                        # Find the newly generated location
                        target_location = self._get_location_by_coordinates(target_coords)
                        if target_location:
                            # Set terrain and mark as named
                            if terrain is not None:
                                target_location.terrain = terrain
                            target_location.is_named = True
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
                            f"Generating named fallback location at {target_coords} from {current.name}"
                        )
                        new_location = generate_fallback_location(
                            direction=direction,
                            source_location=current,
                            target_coords=target_coords,
                            terrain=terrain,
                            chunk_manager=self.chunk_manager,
                            is_named=True,  # Mark as named POI
                            category_hint=category_hint,  # Pass clustering hint
                        )
                        # Add to world
                        self.world[new_location.name] = new_location
                        # Move to new location
                        self.current_location = new_location.name
                    except Exception as e:
                        logger.error(f"Fallback location generation also failed: {e}")
                        self.is_sneaking = False  # Clear sneaking mode on any move attempt
                        return (False, "The path is blocked by an impassable barrier.")

                # Reset counter after generating named location
                self.tiles_since_named = 0

                # Update tiles_since_enterable counter based on generated location
                generated_location = self._get_location_by_coordinates(target_coords)
                if generated_location and generated_location.category in ENTERABLE_CATEGORIES:
                    self.tiles_since_enterable = 0
                else:
                    self.tiles_since_enterable += 1

        # Advance time by 1 hour for movement (+1 hour in storm)
        travel_time = 1 + self.weather.get_travel_modifier()
        self.game_time.advance(travel_time)

        # Update economy with time-based recovery
        self.economy_state.update_time(self.game_time.hour)

        # Check for expired time-limited quests after time advances
        expired_quest_messages = self.check_expired_quests()

        # Autosave after successful movement
        try:
            autosave(self)
        except IOError:
            pass  # Silent failure - don't interrupt gameplay

        # Update visibility based on current position
        self.update_visibility(target_coords)

        # Pre-generate adjacent region contexts if near boundary
        self._pregenerate_adjacent_regions(target_coords)

        # Reset look count for previous location (fresh start on return)
        self.current_character.reset_look_count(previous_location)

        message = f"You head {direction} to {colors.location(self.current_location)}."

        # Add weather flavor text (if not clear weather)
        if self.weather.condition != "clear":
            weather_flavor = self.weather.get_flavor_text()
            message += f"\n{weather_flavor}"

        # Add expired quest messages (quests that failed due to time limit)
        for expired_msg in expired_quest_messages:
            message += f"\n{colors.error(expired_msg)}"

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

        # Check for passive secret detection (PER-based)
        secret_message = self._check_and_report_passive_secrets(location)
        if secret_message:
            message += f"\n{secret_message}"

        # Increase tiredness from travel (3 points per move)
        tiredness_msg = self.current_character.tiredness.increase(3)
        if tiredness_msg:
            message += f"\n{tiredness_msg}"

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

    def _move_in_sub_grid(self, direction: str) -> tuple[bool, str]:
        """Handle movement within a sub-location grid.

        Uses 3D coordinate-based movement within the sub-grid bounds.
        Supports up/down movement for multi-level dungeons and towers.

        Args:
            direction: The direction to move (north, south, east, west, up, down)

        Returns:
            Tuple of (success, message) where:
            - success is True if move was successful, False otherwise
            - message describes the result
        """
        from cli_rpg.world_grid import SUBGRID_DIRECTION_OFFSETS

        current = self.get_current_location()

        if direction not in {"north", "south", "east", "west", "up", "down"}:
            return (False, "Invalid direction. Use: north, south, east, west, up, or down.")

        # Check if direction is blocked (by a puzzle or cave-in)
        if direction in current.blocked_directions:
            return (False, f"The way {direction} is blocked.")

        if current.coordinates is None:
            return (False, "Cannot navigate - location has no coordinates.")

        dx, dy, dz = SUBGRID_DIRECTION_OFFSETS[direction]
        # Get current z-coordinate (support both 2D and 3D locations)
        x, y = current.coordinates[:2]
        z = current.coordinates[2] if len(current.coordinates) > 2 else 0
        target_coords = (x + dx, y + dy, z + dz)

        # Check bounds
        if not self.current_sub_grid.is_within_bounds(*target_coords):
            if dz != 0:
                return (False, "There's no way to go that direction.")
            return (False, "You can't go that way - you've reached the edge of this area.")

        # Find location at target coordinates
        destination = self.current_sub_grid.get_by_coordinates(*target_coords)

        if destination is None:
            return (False, "The path is blocked by a wall.")

        self.current_location = destination.name

        # Mark destination as visited and check for exploration bonus
        exploration_bonus_message = None
        if destination.coordinates is not None:
            coords = destination.coordinates
            if len(coords) == 3:
                x, y, z = coords
            else:
                x, y = coords
                z = 0

            # Check if this will complete exploration (before marking visited)
            was_fully_explored = self.current_sub_grid.is_fully_explored()

            self.current_sub_grid.mark_visited(x, y, z)

            # Award bonus if just completed exploration
            if (
                not was_fully_explored
                and self.current_sub_grid.is_fully_explored()
                and not self.current_sub_grid.exploration_bonus_awarded
            ):
                # Calculate bonus: XP = 50 * total_rooms, Gold = 25 * total_rooms
                _, total_rooms, _ = self.current_sub_grid.get_exploration_stats()
                xp_bonus = 50 * total_rooms
                gold_bonus = 25 * total_rooms

                self.current_character.gain_xp(xp_bonus)
                self.current_character.gold += gold_bonus
                self.current_sub_grid.exploration_bonus_awarded = True

                exploration_bonus_message = (
                    f"\n{colors.heal('★ FULLY EXPLORED! ★')} "
                    f"You've discovered every room in {self.current_sub_grid.parent_name}! "
                    f"+{xp_bonus} XP, +{gold_bonus} gold"
                )

        # Advance time by 1 hour for movement inside buildings
        self.game_time.advance(1)

        # Update economy with time-based recovery
        self.economy_state.update_time(self.game_time.hour)

        # Check for boss encounter at destination
        if destination.boss_enemy and not destination.boss_defeated:
            boss = spawn_boss(
                destination.name,
                level=self.current_character.level,
                location_category=destination.category,
                boss_type=destination.boss_enemy
            )
            self.current_combat = CombatEncounter(
                self.current_character,
                enemies=[boss],
                weather=self.weather,
                companions=self.companions,
                location_category=destination.category,
                game_state=self,
            )
            combat_message = self.current_combat.start()
            return (True, f"You head {direction} to {colors.location(self.current_location)}.\n{combat_message}")

        # Build message and check for passive secret detection
        message = f"You head {direction} to {colors.location(self.current_location)}."
        secret_message = self._check_and_report_passive_secrets(destination)
        if secret_message:
            message += f"\n{secret_message}"

        # Add exploration bonus message if awarded
        if exploration_bonus_message:
            message += exploration_bonus_message

        # Get destination z-coordinate for depth-based features
        dest_z = 0
        if destination.coordinates is not None:
            dest_z = destination.coordinates[2] if len(destination.coordinates) > 2 else 0

        # Update dread based on destination with depth modifier
        from cli_rpg.whisper import get_depth_dread_modifier
        category = destination.category or "default"
        base_dread = DREAD_BY_CATEGORY.get(category, 5)
        depth_modifier = get_depth_dread_modifier(dest_z)
        dread_gain = int(base_dread * depth_modifier)
        dread_message = self.current_character.dread_meter.add_dread(dread_gain)
        if dread_message:
            message += f"\n{dread_message}"

        # Check for ambient whisper with depth parameter
        whisper = self.whisper_service.get_whisper(
            location_category=destination.category,
            character=self.current_character,
            theme=self.theme,
            is_night=self.game_time.is_night(),
            dread=self.current_character.dread_meter.dread,
            depth=dest_z
        )
        if whisper:
            print()  # Blank line for spacing before whisper
            display_whisper(whisper)

        # Check for ambient sound (SubGrid only)
        ambient = self.ambient_sound_service.get_ambient_sound(
            category=destination.category or "dungeon",
            depth=dest_z,
        )
        if ambient:
            print()  # Blank line for spacing before sound
            print(format_ambient_sound(ambient))

        # Progress interior events (clear expired cave-ins)
        from cli_rpg.interior_events import (
            progress_interior_events,
            check_for_cave_in,
            progress_rival_party,
            get_rival_encounter_at_location,
            progress_ritual,
            get_ritual_encounter_at_location,
        )
        event_messages = progress_interior_events(self, self.current_sub_grid)
        for msg in event_messages:
            message += f"\n{msg}"

        # Check for new cave-in (5% chance)
        cave_in_message = check_for_cave_in(self, self.current_sub_grid)
        if cave_in_message:
            message += f"\n{cave_in_message}"

        # Progress rival adventurer party (if one exists)
        rival_message = progress_rival_party(self, self.current_sub_grid)
        if rival_message:
            message += f"\n{rival_message}"

        # Check for rival encounter at destination (triggers combat)
        rival_encounter = get_rival_encounter_at_location(
            self.current_sub_grid, destination
        )
        if rival_encounter and rival_encounter.rival_party:
            # Create enemies from rival party
            from cli_rpg.models.enemy import Enemy
            enemies = []
            for rival in rival_encounter.rival_party:
                enemy = Enemy(
                    name=rival["name"],
                    health=rival["hp"],
                    max_health=rival["hp"],
                    attack_power=rival["attack"],
                    defense=rival["defense"],
                    xp_reward=rival["hp"],  # XP based on HP
                    level=self.current_character.level,
                    description="A rival adventurer racing for the same prize.",
                )
                enemies.append(enemy)

            self.current_combat = CombatEncounter(
                self.current_character,
                enemies=enemies,
                weather=self.weather,
                companions=self.companions,
                location_category=destination.category,
                game_state=self,
            )
            # Mark rival event as inactive after combat starts
            rival_encounter.is_active = False
            message += f"\n\n{colors.enemy('The rival adventurers turn to face you!')}\n{self.current_combat.start()}"

        # Progress ritual countdown (if one exists) - only if not already in combat
        if not self.is_in_combat():
            ritual_progress_message = progress_ritual(self, self.current_sub_grid)
            if ritual_progress_message:
                message += f"\n{ritual_progress_message}"

            # Check for ritual encounter at destination (triggers combat)
            ritual_encounter = get_ritual_encounter_at_location(
                self.current_sub_grid, destination
            )
            if ritual_encounter:
                ritual_event, is_empowered = ritual_encounter
                # Spawn the ritual boss
                boss = spawn_boss(
                    location_name=destination.name,
                    level=self.current_character.level,
                    location_category=destination.category,
                    boss_type="ritual_summoned",
                    empowered=is_empowered,
                )
                self.current_combat = CombatEncounter(
                    self.current_character,
                    enemies=[boss],
                    weather=self.weather,
                    companions=self.companions,
                    location_category=destination.category,
                    game_state=self,
                )
                # Mark ritual event as inactive after combat starts
                ritual_event.is_active = False

                if is_empowered:
                    message += f"\n\n{colors.damage('The ritual is complete! An empowered entity manifests!')}\n{self.current_combat.start()}"
                else:
                    message += f"\n\n{colors.warning('You interrupt the ritual! A weakened entity emerges!')}\n{self.current_combat.start()}"

        # Check for environmental hazards at destination
        from cli_rpg.hazards import check_hazards_on_entry
        hazard_messages = check_hazards_on_entry(self, destination)
        for msg in hazard_messages:
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

        # On-demand SubGrid generation for named locations or enterable categories
        from cli_rpg.world_tiles import is_enterable_category
        can_generate_subgrid = is_enterable_category(current.category)
        has_existing_content = current.sub_grid is not None or bool(current.sub_locations)

        if not can_generate_subgrid and not has_existing_content:
            return (False, "There's nothing to enter here. This is open wilderness.")
        # Only generate SubGrid if no legacy sub_locations exist
        if not has_existing_content:
            # Generate SubGrid on-demand for enterable locations
            from cli_rpg.ai_world import generate_subgrid_for_location
            current.sub_grid = generate_subgrid_for_location(
                location=current,
                ai_service=self.ai_service,
                theme=self.theme,
                world_context=self.world_context,
                region_context=self.get_or_create_region_context(
                    current.coordinates, current.terrain or "wilderness"
                ) if current.coordinates else None,
            )
            # Set entry_point from first is_exit_point location
            for loc in current.sub_grid._by_name.values():
                if loc.is_exit_point:
                    current.entry_point = loc.name
                    break

        # If no target specified, use entry_point
        if target_name is None:
            if current.entry_point is None:
                return (False, "Enter where? Specify a location name.")
            target_name = current.entry_point

        # Find matching sub-location (case-insensitive partial match)
        target_lower = target_name.lower()
        matched_location: Optional[str] = None
        sub_grid_location: Optional[Location] = None

        # First check if current location has a sub_grid
        if current.sub_grid is not None:
            # Look for target in sub_grid
            for loc in current.sub_grid._by_name.values():
                if loc.name.lower().startswith(target_lower) or target_lower in loc.name.lower():
                    matched_location = loc.name
                    sub_grid_location = loc
                    break

            # Only allow entry through entry_point (is_exit_point locations)
            if sub_grid_location is not None and not sub_grid_location.is_exit_point:
                entry_point_name = current.entry_point
                if entry_point_name is None:
                    # Find entry point from is_exit_point flag
                    for loc in current.sub_grid._by_name.values():
                        if loc.is_exit_point:
                            entry_point_name = loc.name
                            break
                return (
                    False,
                    f"You can't enter {matched_location} directly. "
                    f"Enter through {colors.location(entry_point_name or 'the entrance')}.",
                )

        # Fall back to traditional sub_locations list (in world dict)
        if matched_location is None:
            for sub_name in current.sub_locations:
                if sub_name.lower().startswith(target_lower) or target_lower in sub_name.lower():
                    if sub_name in self.world:
                        matched_location = sub_name
                        break

        if matched_location is None:
            # Build helpful error message with available locations
            available = []
            if current.sub_grid is not None:
                available.extend(current.sub_grid._by_name.keys())
            if current.sub_locations:
                available.extend(current.sub_locations)
            # Remove duplicates while preserving order
            available = list(dict.fromkeys(available))

            if available:
                return (False, f"No such location: {target_name}. Available: {', '.join(available)}")
            else:
                return (False, "There are no locations to enter here.")

        # Check faction-based access before entry
        from cli_rpg.faction_content import check_location_access
        target_location = sub_grid_location if sub_grid_location is not None else self.world.get(matched_location)
        if target_location is not None:
            allowed, block_message = check_location_access(target_location, self.factions)
            if not allowed:
                return (False, block_message)

        # Handle sub_grid entry
        if sub_grid_location is not None:
            self.in_sub_location = True
            self.current_sub_grid = current.sub_grid
            self.current_location = matched_location
            # Mark entry room as visited
            if sub_grid_location.coordinates is not None:
                coords = sub_grid_location.coordinates
                if len(coords) == 3:
                    self.current_sub_grid.mark_visited(*coords)
                else:
                    self.current_sub_grid.mark_visited(coords[0], coords[1], 0)
        else:
            # Traditional sub-location entry (in world dict)
            self.current_location = matched_location

        # Build success message with look at new location
        message = f"You enter {colors.location(matched_location)}.\n\n{self.look()}"

        # Check for rival adventurer spawn (15% chance on SubGrid entry)
        if sub_grid_location is not None and self.current_sub_grid is not None:
            from cli_rpg.interior_events import (
                check_for_rival_spawn,
                check_for_ritual_spawn,
                check_for_spreading_hazard,
            )
            rival_message = check_for_rival_spawn(self, self.current_sub_grid)
            if rival_message:
                message += f"\n\n{rival_message}"

            # Check for ritual spawn (15% chance on SubGrid entry, separate roll)
            ritual_message = check_for_ritual_spawn(self, self.current_sub_grid)
            if ritual_message:
                message += f"\n\n{ritual_message}"

            # Check for spreading hazard spawn (5% chance on SubGrid entry, separate roll)
            hazard_message = check_for_spreading_hazard(self, self.current_sub_grid)
            if hazard_message:
                message += f"\n\n{hazard_message}"

        # Get the actual location for secret and boss checks
        sub_location = sub_grid_location if sub_grid_location is not None else self.world[matched_location]

        # Check for passive secret detection (PER-based)
        secret_message = self._check_and_report_passive_secrets(sub_location)
        if secret_message:
            message += f"\n{secret_message}"

        # Check for boss encounter in sub-location
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
                game_state=self,
            )
            message += f"\n\n{self.current_combat.start()}"

        return (True, message)

    def exit_location(self) -> tuple[bool, str]:
        """Exit from a sub-location back to the parent overworld landmark.

        When in a sub-grid, only locations marked is_exit_point=True can be exited.
        Exiting clears the sub-grid state and returns to the parent overworld location.

        Returns:
            Tuple of (success, message) where:
            - success is True if exit was successful, False otherwise
            - message describes the result including look() at parent on success
        """
        # Block during conversation
        if self.is_in_conversation:
            return (False, "You're in a conversation. Say 'bye' to leave first.")

        current = self.get_current_location()

        # Check if at exit point when in sub-location
        if self.in_sub_location and not current.is_exit_point:
            return (False, "You cannot exit from here. Find an exit point.")

        # Must have a parent location
        if current.parent_location is None:
            return (False, "You're not inside a building or dungeon. Use 'go <direction>' to travel.")

        # Verify parent exists in world
        if current.parent_location not in self.world:
            return (False, f"Cannot find parent location: {current.parent_location}")

        # Move to parent location
        self.current_location = current.parent_location

        # Clear sub-location state
        self.in_sub_location = False
        self.current_sub_grid = None

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

    def _pregenerate_adjacent_regions(self, coords: tuple[int, int]) -> None:
        """Pre-generate region contexts for regions near the given coordinates.

        Called after movement to pre-cache region contexts before the player
        reaches the boundary, ensuring smooth gameplay.

        Args:
            coords: Current world coordinates to check for proximity
        """
        from cli_rpg.world_tiles import check_region_boundary_proximity, REGION_SIZE

        # Get terrain hint from chunk_manager if available
        terrain_hint = "wilderness"
        if self.chunk_manager is not None:
            terrain_hint = self.chunk_manager.get_tile_at(*coords)

        # Check for adjacent regions within proximity threshold
        adjacent_regions = check_region_boundary_proximity(*coords)

        for region_coords in adjacent_regions:
            # Skip if already cached
            if region_coords in self.region_contexts:
                continue

            # Generate context for this region using center coordinates
            center_x = region_coords[0] * REGION_SIZE + REGION_SIZE // 2
            center_y = region_coords[1] * REGION_SIZE + REGION_SIZE // 2

            try:
                self.get_or_create_region_context((center_x, center_y), terrain_hint)
                logger.debug(f"Pre-generated region context for {region_coords}")
            except Exception as e:
                logger.warning(f"Failed to pre-generate region {region_coords}: {e}")

        # Queue adjacent locations for background generation
        self._queue_adjacent_locations(coords)

    def _queue_adjacent_locations(self, coords: tuple[int, int]) -> None:
        """Queue adjacent locations for background generation.

        Submits unexplored adjacent coordinates to the background generation
        queue for pre-generation before the player arrives.

        Args:
            coords: Current world coordinates
        """
        if self.background_gen_queue is None:
            return

        from cli_rpg.world_grid import DIRECTION_OFFSETS

        for direction in DIRECTION_OFFSETS:
            dx, dy = DIRECTION_OFFSETS[direction]
            adj_coords = (coords[0] + dx, coords[1] + dy)

            # Skip if location already exists
            if self._get_location_by_coordinates(adj_coords) is not None:
                continue

            # Get terrain from chunk_manager if available
            terrain = "plains"
            if self.chunk_manager is not None:
                terrain = self.chunk_manager.get_tile_at(*adj_coords)

            # Get context for layered generation
            world_ctx = self.world_context
            region_ctx = None
            if world_ctx is not None:
                try:
                    region_ctx = self.get_or_create_region_context(adj_coords, terrain)
                except Exception:
                    pass  # Skip context if generation fails

            self.background_gen_queue.submit(
                coords=adj_coords,
                terrain=terrain,
                world_context=world_ctx,
                region_context=region_ctx,
            )

    def start_background_generation(self) -> None:
        """Start background generation queue if AI service available.

        Creates and starts a BackgroundGenerationQueue for pre-generating
        adjacent locations before the player arrives.
        """
        if self.ai_service is not None:
            from cli_rpg.background_gen import BackgroundGenerationQueue
            self.background_gen_queue = BackgroundGenerationQueue(
                ai_service=self.ai_service,
                theme=self.theme,
            )
            self.background_gen_queue.start()

    def stop_background_generation(self) -> None:
        """Stop background generation queue.

        Shuts down the background generation queue and its worker threads.
        """
        if self.background_gen_queue is not None:
            self.background_gen_queue.shutdown()
            self.background_gen_queue = None

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

    def check_expired_quests(self) -> list[str]:
        """Check for and fail any expired time-limited quests.

        Also records quest outcomes for failed quests.

        Returns:
            List of messages about failed quests
        """
        from cli_rpg.models.quest import QuestStatus

        messages = []
        current_hour = self.game_time.total_hours
        for quest in self.current_character.quests:
            if quest.status == QuestStatus.ACTIVE and quest.is_expired(current_hour):
                quest.status = QuestStatus.FAILED
                # Record the expired quest outcome
                self.record_quest_outcome(quest, method="expired")
                messages.append(f"Quest '{quest.name}' has expired and failed!")
        return messages

    def record_quest_outcome(
        self,
        quest: "Quest",
        method: str,
        branch_name: Optional[str] = None,
        affected_npcs: Optional[list[str]] = None,
        faction_changes: Optional[dict[str, int]] = None,
    ) -> None:
        """Record a quest completion outcome for NPC memory.

        Args:
            quest: The completed quest
            method: How quest was completed ("main", "branch_<id>", "expired", "abandoned")
            branch_name: Display name of branch if completed via branch
            affected_npcs: NPCs involved in the quest outcome
            faction_changes: Faction reputation changes from the quest
        """
        from cli_rpg.models.quest import Quest

        outcome = QuestOutcome(
            quest_name=quest.name,
            quest_giver=quest.quest_giver or "Unknown",
            completion_method=method,
            completed_branch_name=branch_name,
            timestamp=self.game_time.total_hours,
            affected_npcs=affected_npcs or [],
            faction_changes=faction_changes or {},
        )
        self.quest_outcomes.append(outcome)

    def get_quest_outcomes_for_npc(self, npc_name: str) -> list[QuestOutcome]:
        """Get quest outcomes relevant to a specific NPC.

        Returns outcomes where the NPC was either the quest giver or
        was affected by the quest outcome.

        Args:
            npc_name: Name of the NPC to filter by

        Returns:
            List of relevant QuestOutcome objects
        """
        relevant = []
        for outcome in self.quest_outcomes:
            if (
                outcome.quest_giver.lower() == npc_name.lower()
                or npc_name.lower() in [n.lower() for n in outcome.affected_npcs]
            ):
                relevant.append(outcome)
        return relevant

    # Quest network integration methods
    def register_quest(self, quest: "Quest") -> None:
        """Register a quest in the quest network.

        Adds the quest to the network for chain/dependency tracking.
        Does not add to character.quests - use accept_quest for that.

        Args:
            quest: Quest to register
        """
        self.quest_network.add_quest(quest)

    def get_completed_quest_names(self) -> list[str]:
        """Get names of all completed quests from character.

        Returns:
            List of completed quest names (for dependency checks)
        """
        from cli_rpg.models.quest import QuestStatus

        return [
            q.name
            for q in self.current_character.quests
            if q.status == QuestStatus.COMPLETED
        ]

    def get_available_quests(self) -> list["Quest"]:
        """Get quests available based on completed prerequisites.

        Returns:
            List of Quest objects with satisfied prerequisites
        """
        completed = self.get_completed_quest_names()
        return self.quest_network.get_available_quests(completed)

    def get_chain_progression(self, chain_id: str) -> tuple[int, int]:
        """Get (completed, total) count for a quest chain.

        Args:
            chain_id: The chain identifier

        Returns:
            Tuple of (completed_count, total_count)
        """
        completed = self.get_completed_quest_names()
        return self.quest_network.get_chain_progression(chain_id, completed)

    def get_next_in_chain(self, chain_id: str) -> Optional["Quest"]:
        """Get the next incomplete quest in a chain.

        Args:
            chain_id: The chain identifier

        Returns:
            Next Quest in chain, or None if chain is complete
        """
        completed = self.get_completed_quest_names()
        return self.quest_network.get_next_in_chain(chain_id, completed)

    def get_or_create_world_context(self) -> WorldContext:
        """Get cached world context or generate/create default.

        If world_context is already cached, returns it.
        If AI service is available, generates using AI.
        Otherwise, creates a default context for the theme.

        Returns:
            WorldContext for the current world theme
        """
        # Return cached if available
        if self.world_context is not None:
            return self.world_context

        # Try AI generation if available
        if self.ai_service is not None:
            try:
                self.world_context = self.ai_service.generate_world_context(self.theme)
                return self.world_context
            except Exception as e:
                logger.warning(f"AI world context generation failed: {e}")
                # Fall through to default

        # Create default context
        self.world_context = WorldContext.default(self.theme)
        return self.world_context

    def get_or_create_region_context(
        self, coords: tuple[int, int], terrain_hint: str = "wilderness"
    ) -> RegionContext:
        """Get cached region context or generate/create default.

        Region contexts are cached by region coordinates (16x16 tile regions),
        not by individual world coordinates.

        Args:
            coords: World coordinates as (x, y) tuple - will be converted to region coords
            terrain_hint: Terrain type hint for the region (e.g., "mountains", "swamp")

        Returns:
            RegionContext for the region containing the specified coordinates
        """
        from cli_rpg.world_tiles import get_region_coords, REGION_SIZE

        # Convert world coords to region coords
        region_x, region_y = get_region_coords(*coords)
        region_key = (region_x, region_y)

        # Return cached if available
        if region_key in self.region_contexts:
            return self.region_contexts[region_key]

        # Need world context first
        world_context = self.get_or_create_world_context()

        # Use center of region as representative coordinates for AI generation
        center_x = region_x * REGION_SIZE + REGION_SIZE // 2
        center_y = region_y * REGION_SIZE + REGION_SIZE // 2
        center_coords = (center_x, center_y)

        # Try AI generation if available
        if self.ai_service is not None:
            try:
                region_context = self.ai_service.generate_region_context(
                    theme=self.theme,
                    world_context=world_context,
                    coordinates=center_coords,
                    terrain_hint=terrain_hint
                )
                self.region_contexts[region_key] = region_context
                return region_context
            except Exception as e:
                logger.warning(f"AI region context generation failed: {e}")
                # Fall through to default

        # Create default context
        region_name = f"Region {region_x},{region_y}"
        region_context = RegionContext.default(region_name, center_coords)
        self.region_contexts[region_key] = region_context
        return region_context

    def get_generation_context(
        self,
        coords: Optional[tuple[int, int]] = None,
        settlement_name: Optional[str] = None,
    ) -> GenerationContext:
        """Build GenerationContext from cached layers.

        Aggregates all available context layers (WorldContext, RegionContext,
        SettlementContext, LoreContext) into a single GenerationContext for
        use in AI prompt generation.

        Args:
            coords: Coordinates for region lookup (defaults to current location)
            settlement_name: Name for settlement context lookup (if applicable)

        Returns:
            GenerationContext with available layers populated
        """
        # Get current location for defaults
        current = self.get_current_location()

        # Use provided coords or fall back to current location coords
        if coords is None:
            coords = current.coordinates

        # Layer 1: WorldContext (always present)
        world_ctx = self.get_or_create_world_context()

        # Layer 2: RegionContext (if coords available)
        region_ctx = None
        if coords is not None:
            terrain_hint = current.terrain or "wilderness"
            region_ctx = self.get_or_create_region_context(coords, terrain_hint)

        # Layer 5: SettlementContext - not yet implemented in caches
        # Future: lookup from settlement_contexts cache when available
        settlement_ctx = None

        # Layer 6: LoreContext - not yet implemented in caches
        # Future: lookup from lore_contexts cache when available
        world_lore = None
        region_lore = None

        return GenerationContext(
            world=world_ctx,
            region=region_ctx,
            settlement=settlement_ctx,
            world_lore=world_lore,
            region_lore=region_lore,
        )

    def get_explored_regions(self) -> set[tuple[int, int]]:
        """Return set of region coordinates that have been explored.

        Analyzes all locations in world grid to determine which regions
        (REGION_SIZE x REGION_SIZE tile areas) have been visited.

        Returns:
            Set of (region_x, region_y) tuples
        """
        from cli_rpg.world_tiles import get_region_coords

        explored = set()
        for location in self.world.values():
            if location.coordinates is not None:
                explored.add(get_region_coords(*location.coordinates))
        return explored

    def get_fast_travel_destinations(self) -> list[str]:
        """Get list of valid fast travel destinations.

        Returns named overworld locations (excluding current location).
        Only includes locations with coordinates and no parent_location.

        Returns:
            Alphabetically sorted list of destination names.
        """
        destinations = []
        for loc in self.world.values():
            # Must be named POI, have coordinates, be overworld (no parent)
            if (loc.is_named and
                loc.coordinates is not None and
                loc.parent_location is None and
                loc.name != self.current_location):
                destinations.append(loc.name)
        return sorted(destinations)

    def fast_travel(self, destination: str) -> tuple[bool, str]:
        """Travel instantly to a previously-visited named location.

        Consumes time proportional to Manhattan distance, increases tiredness,
        and has a chance for random encounters during the journey.

        Args:
            destination: Name of destination (case-insensitive partial match)

        Returns:
            Tuple of (success, message)
        """
        from cli_rpg.combat import spawn_enemy

        # Block conditions
        if self.is_in_combat():
            return (False, "You cannot travel while in combat!")
        if self.is_in_conversation:
            return (False, "You're in a conversation. Say 'bye' to leave first.")
        if self.in_sub_location:
            return (False, "You must exit this location before fast traveling. Use 'exit' first.")

        # Find destination (case-insensitive partial match)
        dest_lower = destination.lower()
        matched = None
        for name in self.get_fast_travel_destinations():
            if name.lower().startswith(dest_lower) or dest_lower in name.lower():
                matched = name
                break

        if matched is None:
            return (False, f"Unknown destination: {destination}. Use 'travel' to see available locations.")

        dest_location = self.world[matched]
        current = self.get_current_location()

        # Calculate Manhattan distance and travel time
        dx = abs(dest_location.coordinates[0] - current.coordinates[0])
        dy = abs(dest_location.coordinates[1] - current.coordinates[1])
        distance = dx + dy
        travel_hours = max(1, min(8, distance // 4))

        messages = [f"You begin your journey to {colors.location(matched)}..."]

        # Simulate travel hour by hour
        for hour in range(travel_hours):
            # Advance time
            self.game_time.advance(1)

            # Update economy with time-based recovery
            self.economy_state.update_time(self.game_time.hour)

            # Weather transition
            self.weather.transition()

            # Tiredness increase (3 per move)
            tiredness_msg = self.current_character.tiredness.increase(3)
            if tiredness_msg:
                messages.append(tiredness_msg)

            # Dread increase (wilderness average = 5)
            dread_msg = self.current_character.dread_meter.add_dread(5)
            if dread_msg:
                messages.append(dread_msg)

            # Random encounter check (15% per hour)
            if random.random() < 0.15 and not self.get_current_location().is_safe_zone:
                # Hostile encounter interrupts travel
                enemy = spawn_enemy(
                    location_name=self.current_location,
                    level=self.current_character.level,
                    location_category="wilderness",
                )
                self.current_combat = CombatEncounter(
                    self.current_character,
                    enemies=[enemy],
                    companions=self.companions,
                    location_category="wilderness",
                    game_state=self,
                )
                combat_start = self.current_combat.start()
                messages.append(f"\n{colors.warning('[Ambush!]')} Your journey is interrupted!")
                messages.append(combat_start)
                return (True, "\n".join(messages))

        # Arrive at destination
        self.current_location = matched
        messages.append(f"\nAfter {travel_hours} hour{'s' if travel_hours > 1 else ''}, you arrive at {colors.location(matched)}.")

        # Look at new location
        messages.append(f"\n{self.look()}")

        # Autosave
        try:
            autosave(self)
        except IOError:
            pass

        return (True, "\n".join(messages))

    def to_dict(self) -> dict:
        """Serialize game state to dictionary.

        Returns:
            Dictionary containing character, current_location, world data, theme, game_time, weather, choices, world_events, companions, and chunk_manager
        """
        data = {
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
            "factions": [faction.to_dict() for faction in self.factions],
            "forage_cooldown": self.forage_cooldown,
            "hunt_cooldown": self.hunt_cooldown,
            "gather_cooldown": self.gather_cooldown,
            "in_sub_location": self.in_sub_location,
            "tiles_since_named": self.tiles_since_named,
            "tiles_since_enterable": self.tiles_since_enterable,
            "last_dream_hour": self.last_dream_hour,
            "quest_outcomes": [outcome.to_dict() for outcome in self.quest_outcomes],
            "seen_tiles": list(self.seen_tiles),
            "world_state_manager": self.world_state_manager.to_dict(),
            "economy_state": self.economy_state.to_dict(),
            "quest_network": self.quest_network.to_dict(),
            "location_noise_seed": self.location_noise_manager.world_seed,
        }
        # Include chunk_manager if present (WFC terrain)
        if self.chunk_manager is not None:
            data["chunk_manager"] = self.chunk_manager.to_dict()
        # Include world_context if present (Layer 1)
        if self.world_context is not None:
            data["world_context"] = self.world_context.to_dict()
        # Include region_contexts if present (Layer 2)
        # Serialize as list of [coords, context] pairs for JSON compatibility
        if self.region_contexts:
            data["region_contexts"] = [
                [list(coords), ctx.to_dict()]
                for coords, ctx in self.region_contexts.items()
            ]
        return data
    
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
        in_sub_location = data.get("in_sub_location", False)

        # Get theme (default to "fantasy" for backward compatibility)
        theme = data.get("theme", "fantasy")

        # If in a sub-location, find the parent location for initial state
        # The actual sub-grid location will be set after construction
        initial_location = current_location
        parent_sub_grid = None
        if in_sub_location and current_location not in world:
            # Find parent location that contains this sub-grid location
            for loc in world.values():
                if loc.sub_grid is not None:
                    sub_grid_loc = loc.sub_grid.get_by_name(current_location)
                    if sub_grid_loc is not None:
                        initial_location = loc.name
                        parent_sub_grid = loc.sub_grid
                        break

        # Create game state
        game_state = cls(
            character, world, initial_location, ai_service=ai_service, theme=theme
        )

        # Restore actual current_location and sub-grid state
        game_state.current_location = current_location
        if in_sub_location:
            game_state.in_sub_location = True
            game_state.current_sub_grid = parent_sub_grid

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

        # Restore factions if present (default to empty list for backward compatibility)
        game_state.factions = [
            Faction.from_dict(faction_data)
            for faction_data in data.get("factions", [])
        ]

        # Restore forage/hunt/gather cooldowns (default to 0 for backward compatibility)
        game_state.forage_cooldown = data.get("forage_cooldown", 0)
        game_state.hunt_cooldown = data.get("hunt_cooldown", 0)
        game_state.gather_cooldown = data.get("gather_cooldown", 0)

        # Restore tiles_since_named counter (default to 0 for backward compatibility)
        game_state.tiles_since_named = data.get("tiles_since_named", 0)

        # Restore tiles_since_enterable counter (default to 0 for backward compatibility)
        game_state.tiles_since_enterable = data.get("tiles_since_enterable", 0)

        # Restore last_dream_hour (default to None for backward compatibility)
        game_state.last_dream_hour = data.get("last_dream_hour")

        # Restore quest_outcomes (default to empty list for backward compatibility)
        game_state.quest_outcomes = [
            QuestOutcome.from_dict(outcome_data)
            for outcome_data in data.get("quest_outcomes", [])
        ]

        # Restore seen_tiles (default to empty set for backward compatibility)
        game_state.seen_tiles = set(tuple(t) for t in data.get("seen_tiles", []))

        # Restore world_state_manager (default to empty for backward compatibility)
        game_state.world_state_manager = WorldStateManager.from_dict(
            data.get("world_state_manager")
        )

        # Restore economy_state (default to fresh for backward compatibility)
        game_state.economy_state = EconomyState.from_dict(
            data.get("economy_state")
        )

        # Restore quest_network (default to empty for backward compatibility)
        if "quest_network" in data:
            game_state.quest_network = QuestNetworkManager.from_dict(data["quest_network"])

        # Restore chunk_manager if present (WFC terrain)
        # Must restore before location_noise_manager for fallback seed logic
        if "chunk_manager" in data:
            from cli_rpg.wfc_chunks import ChunkManager
            from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY
            game_state.chunk_manager = ChunkManager.from_dict(
                data["chunk_manager"], DEFAULT_TILE_REGISTRY
            )

        # Restore location_noise_manager (for backward compatibility, check multiple sources)
        noise_seed = data.get("location_noise_seed")
        if noise_seed is not None:
            game_state.location_noise_manager = LocationNoiseManager(world_seed=noise_seed)
        elif game_state.chunk_manager is not None:
            game_state.location_noise_manager = LocationNoiseManager(
                world_seed=game_state.chunk_manager.world_seed
            )
        else:
            game_state.location_noise_manager = LocationNoiseManager(
                world_seed=random.randint(0, 2**31)
            )

        # Restore world_context if present (Layer 1)
        if "world_context" in data:
            game_state.world_context = WorldContext.from_dict(data["world_context"])

        # Restore region_contexts if present (Layer 2)
        # Serialized as list of [coords, context] pairs
        if "region_contexts" in data:
            game_state.region_contexts = {
                tuple(coords): RegionContext.from_dict(ctx_data)
                for coords, ctx_data in data["region_contexts"]
            }

        return game_state
