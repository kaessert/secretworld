"""AI service for generating game content using LLMs."""

import json
import hashlib
import time
from typing import Optional
from openai import OpenAI
import openai

# Conditionally import Anthropic to handle missing package
try:
    from anthropic import Anthropic
    import anthropic as anthropic_module
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    anthropic_module = None
    ANTHROPIC_AVAILABLE = False

import logging

from cli_rpg.ai_config import AIConfig
from cli_rpg.models.location import Location

# Valid directions for grid-based movement (subset of Location.VALID_DIRECTIONS)
GRID_DIRECTIONS: set[str] = {"north", "south", "east", "west"}

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIGenerationError(AIServiceError):
    """Exception raised when content generation fails."""
    pass


class AITimeoutError(AIServiceError):
    """Exception raised when API request times out."""
    pass


class AIService:
    """Service for generating game content using LLMs.

    Attributes:
        config: AIConfig instance with service configuration
        provider: The AI provider being used ("openai" or "anthropic")
    """

    def __init__(self, config: AIConfig):
        """Initialize AI service.

        Args:
            config: AIConfig instance with API key and settings

        Raises:
            AIServiceError: If Anthropic provider is requested but package is not installed
        """
        self.config = config
        self.provider = config.provider

        # Initialize the appropriate client based on provider
        if self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise AIServiceError(
                    "Anthropic provider requested but 'anthropic' package is not installed. "
                    "Install it with: pip install anthropic"
                )
            self.client = Anthropic(api_key=config.api_key)
        else:
            # Default to OpenAI
            self.client = OpenAI(api_key=config.api_key)

        # Initialize cache if enabled
        self._cache: dict[str, tuple[dict, float]] = {}  # key -> (data, timestamp)
    
    def generate_location(
        self,
        theme: str,
        context_locations: list[str] = None,
        source_location: Optional[str] = None,
        direction: Optional[str] = None
    ) -> dict:
        """Generate a new location based on context.
        
        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            context_locations: List of existing location names
            source_location: Location to expand from
            direction: Direction of expansion from source
        
        Returns:
            Dictionary with keys: name, description, connections
        
        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        if context_locations is None:
            context_locations = []
        
        # Build prompt
        prompt = self._build_location_prompt(
            theme=theme,
            context_locations=context_locations,
            source_location=source_location,
            direction=direction
        )
        
        # Check cache if enabled
        if self.config.enable_caching:
            cached_result = self._get_cached(prompt)
            if cached_result is not None:
                return cached_result
        
        # Call LLM
        response_text = self._call_llm(prompt)
        
        # Parse and validate response
        location_data = self._parse_location_response(response_text)
        
        # Cache result if enabled
        if self.config.enable_caching:
            self._set_cached(prompt, location_data)
        
        return location_data
    
    def _build_location_prompt(
        self,
        theme: str,
        context_locations: list[str],
        source_location: Optional[str],
        direction: Optional[str]
    ) -> str:
        """Build prompt for location generation.
        
        Args:
            theme: World theme
            context_locations: List of existing location names
            source_location: Location to expand from
            direction: Direction of expansion
        
        Returns:
            Formatted prompt string
        """
        # Format context locations
        if context_locations:
            location_list = ", ".join(context_locations)
        else:
            location_list = "None yet"
        
        # Format source and direction
        source_text = source_location if source_location else "None (starting location)"
        direction_text = direction if direction else "N/A"
        
        # Use template from config
        prompt = self.config.location_generation_prompt.format(
            theme=theme,
            context_locations=location_list,
            source_location=source_text,
            direction=direction_text
        )
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API with retry logic.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Response text from the LLM

        Raises:
            AIServiceError: If API call fails after retries
            AITimeoutError: If request times out
        """
        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        else:
            return self._call_openai(prompt)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Response text from the LLM

        Raises:
            AIServiceError: If API call fails after retries
            AITimeoutError: If request times out
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )

                return response.choices[0].message.content

            except openai.APITimeoutError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                raise AITimeoutError(f"Request timed out after {attempt + 1} attempts") from e

            except (openai.APIConnectionError, openai.RateLimitError) as e:
                # Transient errors - retry
                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                raise AIServiceError(f"API call failed after {attempt + 1} attempts: {str(e)}") from e

            except openai.AuthenticationError as e:
                # Don't retry authentication errors
                raise AIServiceError(f"Authentication failed: {str(e)}") from e

            except Exception as e:
                # Other errors
                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                raise AIServiceError(f"API call failed: {str(e)}") from e

        # Should not reach here, but just in case
        raise AIServiceError(f"API call failed after retries: {str(last_error)}") from last_error

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API with retry logic.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Response text from the LLM

        Raises:
            AIServiceError: If API call fails after retries
            AITimeoutError: If request times out
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.config.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.config.max_tokens
                )

                return response.content[0].text

            except Exception as e:
                # Handle Anthropic-specific exceptions if available
                if anthropic_module is not None:
                    if isinstance(e, anthropic_module.APITimeoutError):
                        last_error = e
                        if attempt < self.config.max_retries:
                            time.sleep(self.config.retry_delay * (2 ** attempt))
                            continue
                        raise AITimeoutError(f"Request timed out after {attempt + 1} attempts") from e

                    if isinstance(e, (anthropic_module.APIConnectionError, anthropic_module.RateLimitError)):
                        last_error = e
                        if attempt < self.config.max_retries:
                            time.sleep(self.config.retry_delay * (2 ** attempt))
                            continue
                        raise AIServiceError(f"API call failed after {attempt + 1} attempts: {str(e)}") from e

                    if isinstance(e, anthropic_module.AuthenticationError):
                        raise AIServiceError(f"Authentication failed: {str(e)}") from e

                # General exception handling
                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                raise AIServiceError(f"API call failed: {str(e)}") from e

        # Should not reach here, but just in case
        raise AIServiceError(f"API call failed after retries: {str(last_error)}") from last_error
    
    def _parse_location_response(self, response_text: str) -> dict:
        """Parse and validate LLM response.
        
        Args:
            response_text: Raw response text from LLM
        
        Returns:
            Dictionary with validated location data
        
        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Try to parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
        
        # Validate required fields
        required_fields = ["name", "description", "connections"]
        for field in required_fields:
            if field not in data:
                raise AIGenerationError(f"Response missing required field: {field}")
        
        # Validate name length
        name = data["name"].strip()
        if len(name) < Location.MIN_NAME_LENGTH:
            raise AIGenerationError(
                f"Location name too short (min {Location.MIN_NAME_LENGTH} chars): {name}"
            )
        if len(name) > Location.MAX_NAME_LENGTH:
            raise AIGenerationError(
                f"Location name too long (max {Location.MAX_NAME_LENGTH} chars): {name}"
            )
        
        # Validate description length
        description = data["description"].strip()
        if len(description) < Location.MIN_DESCRIPTION_LENGTH:
            raise AIGenerationError(
                f"Location description too short (min {Location.MIN_DESCRIPTION_LENGTH} chars)"
            )
        if len(description) > Location.MAX_DESCRIPTION_LENGTH:
            raise AIGenerationError(
                f"Location description too long (max {Location.MAX_DESCRIPTION_LENGTH} chars)"
            )
        
        # Validate connections
        connections = data["connections"]
        if not isinstance(connections, dict):
            raise AIGenerationError("Connections must be a dictionary")

        # Filter connections to only include cardinal directions (grid-based movement)
        filtered_connections = {}
        for direction, target in connections.items():
            if direction in GRID_DIRECTIONS:
                filtered_connections[direction] = target
            else:
                # Log but don't fail - AI sometimes generates up/down
                logger.warning(
                    f"Filtered non-grid direction '{direction}' from location '{name}'"
                )

        # Return validated data with filtered connections
        return {
            "name": name,
            "description": description,
            "connections": filtered_connections
        }
    
    def _get_cached(self, prompt: str) -> Optional[dict]:
        """Get cached location data.
        
        Args:
            prompt: The prompt used as cache key
        
        Returns:
            Cached location data if found and not expired, None otherwise
        """
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - timestamp < self.config.cache_ttl:
                return data.copy()  # Return a copy to avoid mutations
            else:
                # Cache expired, remove it
                del self._cache[cache_key]
        
        return None
    
    def _set_cached(self, prompt: str, data: dict) -> None:
        """Store location data in cache.

        Args:
            prompt: The prompt used as cache key
            data: Location data to cache
        """
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        self._cache[cache_key] = (data.copy(), time.time())

    def generate_area(
        self,
        theme: str,
        sub_theme_hint: str,
        entry_direction: str,
        context_locations: list[str],
        size: int = 5
    ) -> list[dict]:
        """Generate a cluster of connected locations forming a thematic area.

        Creates 4-7 interconnected locations with a consistent sub-theme that
        fits the world theme. The entry location is at relative coordinates (0, 0).

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            sub_theme_hint: Hint for the area's sub-theme (e.g., "graveyard", "forest")
            entry_direction: Direction from which the player enters the area
            context_locations: List of existing location names in the world
            size: Target number of locations (4-7, default 5)

        Returns:
            List of dictionaries, each containing:
            - name: Location name (2-50 characters)
            - description: Location description (1-500 characters)
            - relative_coords: [dx, dy] relative to entry point (entry is [0, 0])
            - connections: Dict mapping directions to location names

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Clamp size to valid range
        size = max(4, min(7, size))

        # Build the prompt for area generation
        prompt = self._build_area_prompt(
            theme=theme,
            sub_theme_hint=sub_theme_hint,
            entry_direction=entry_direction,
            context_locations=context_locations,
            size=size
        )

        # Check cache if enabled
        if self.config.enable_caching:
            cached_result = self._get_cached_list(prompt)
            if cached_result is not None:
                return cached_result

        # Call LLM
        response_text = self._call_llm(prompt)

        # Parse and validate response
        area_data = self._parse_area_response(response_text, size)

        # Cache result if enabled
        if self.config.enable_caching:
            self._set_cached_list(prompt, area_data)

        return area_data

    def _build_area_prompt(
        self,
        theme: str,
        sub_theme_hint: str,
        entry_direction: str,
        context_locations: list[str],
        size: int
    ) -> str:
        """Build prompt for area generation.

        Args:
            theme: World theme
            sub_theme_hint: Hint for area sub-theme
            entry_direction: Direction player enters from
            context_locations: Existing location names
            size: Number of locations to generate

        Returns:
            Formatted prompt string
        """
        # Get opposite direction for the back-connection
        opposites = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east"
        }
        back_direction = opposites.get(entry_direction, "south")

        # Format context
        if context_locations:
            location_list = ", ".join(context_locations[:10])  # Limit to 10
        else:
            location_list = "None yet"

        prompt = f"""You are a creative game world designer. Generate a connected area of {size} locations for a {theme} RPG game.

Area Theme: {sub_theme_hint}
World Theme: {theme}
Existing Locations: {location_list}
Entry Direction: Player enters from the {entry_direction} (so entry location should have a {back_direction} exit back)

Requirements:
1. Generate exactly {size} interconnected locations that form a cohesive themed area
2. Each location needs a unique name (2-50 characters) that fits the "{sub_theme_hint}" theme
3. Each location needs a vivid description (1-500 characters)
4. The FIRST location is the entry point at relative coordinates [0, 0]
5. Use relative coordinates: north = +y, south = -y, east = +x, west = -x
6. All locations must be connected to at least one other location in the area
7. The entry location MUST have a "{back_direction}" exit (to connect back to the existing world)
8. Valid directions: north, south, east, west (no up/down for this area)
9. Ensure internal consistency: if A connects north to B, then B must connect south to A

Respond with valid JSON array (no additional text):
[
  {{
    "name": "Entry Location Name",
    "description": "Description of entry location",
    "relative_coords": [0, 0],
    "connections": {{"{back_direction}": "EXISTING_WORLD", "north": "Next Location Name"}}
  }},
  {{
    "name": "Next Location Name",
    "description": "Description",
    "relative_coords": [0, 1],
    "connections": {{"south": "Entry Location Name"}}
  }}
]

Note: Use "EXISTING_WORLD" as placeholder for the connection back to the source location."""

        return prompt

    def _parse_area_response(self, response_text: str, expected_size: int) -> list[dict]:
        """Parse and validate LLM response for area generation.

        Args:
            response_text: Raw response text from LLM
            expected_size: Expected number of locations

        Returns:
            List of validated location dictionaries

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Try to parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e

        # Validate it's a list
        if not isinstance(data, list):
            raise AIGenerationError("Response must be a JSON array of locations")

        # Validate minimum size
        if len(data) < 1:
            raise AIGenerationError("Response must contain at least one location")

        # Validate each location
        validated_locations = []
        for idx, loc in enumerate(data):
            validated_loc = self._validate_area_location(loc, idx)
            validated_locations.append(validated_loc)

        return validated_locations

    def _validate_area_location(self, loc: dict, index: int) -> dict:
        """Validate a single location in an area response.

        Args:
            loc: Location dictionary from LLM response
            index: Index of location in array (for error messages)

        Returns:
            Validated location dictionary

        Raises:
            AIGenerationError: If validation fails
        """
        # Check required fields
        required_fields = ["name", "description", "relative_coords", "connections"]
        for field in required_fields:
            if field not in loc:
                raise AIGenerationError(
                    f"Location {index} missing required field: {field}"
                )

        # Validate name
        name = loc["name"].strip()
        if len(name) < Location.MIN_NAME_LENGTH:
            raise AIGenerationError(
                f"Location {index} name too short (min {Location.MIN_NAME_LENGTH} chars): {name}"
            )
        if len(name) > Location.MAX_NAME_LENGTH:
            raise AIGenerationError(
                f"Location {index} name too long (max {Location.MAX_NAME_LENGTH} chars): {name}"
            )

        # Validate description
        description = loc["description"].strip()
        if len(description) < Location.MIN_DESCRIPTION_LENGTH:
            raise AIGenerationError(
                f"Location {index} description too short (min {Location.MIN_DESCRIPTION_LENGTH} chars)"
            )
        if len(description) > Location.MAX_DESCRIPTION_LENGTH:
            raise AIGenerationError(
                f"Location {index} description too long (max {Location.MAX_DESCRIPTION_LENGTH} chars)"
            )

        # Validate relative_coords
        coords = loc["relative_coords"]
        if not isinstance(coords, list) or len(coords) != 2:
            raise AIGenerationError(
                f"Location {index} relative_coords must be [x, y] array"
            )

        # Validate connections
        connections = loc["connections"]
        if not isinstance(connections, dict):
            raise AIGenerationError(f"Location {index} connections must be a dictionary")

        # Filter connections to only include cardinal directions (grid-based movement)
        filtered_connections = {}
        for direction, target in connections.items():
            if direction in GRID_DIRECTIONS:
                filtered_connections[direction] = target
            else:
                # Log but don't fail - AI sometimes generates up/down
                logger.warning(
                    f"Filtered non-grid direction '{direction}' from area location '{name}'"
                )

        return {
            "name": name,
            "description": description,
            "relative_coords": coords,
            "connections": filtered_connections
        }

    def _get_cached_list(self, prompt: str) -> Optional[list]:
        """Get cached area data (list of locations).

        Args:
            prompt: The prompt used as cache key

        Returns:
            Cached list of location data if found and not expired, None otherwise
        """
        cache_key = hashlib.md5(prompt.encode()).hexdigest()

        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]

            if time.time() - timestamp < self.config.cache_ttl:
                # Deep copy the list
                import copy
                return copy.deepcopy(data)
            else:
                del self._cache[cache_key]

        return None

    def _set_cached_list(self, prompt: str, data: list) -> None:
        """Store area data (list of locations) in cache.

        Args:
            prompt: The prompt used as cache key
            data: List of location data to cache
        """
        import copy
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        self._cache[cache_key] = (copy.deepcopy(data), time.time())

    def generate_npc_dialogue(
        self,
        npc_name: str,
        npc_description: str,
        npc_role: str,
        theme: str,
        location_name: str = ""
    ) -> str:
        """Generate contextual dialogue for an NPC.

        Args:
            npc_name: Name of the NPC
            npc_description: NPC's description
            npc_role: Role type ("merchant", "quest_giver", "villager")
            theme: World theme (e.g., "fantasy", "sci-fi")
            location_name: Current location name for context

        Returns:
            Generated dialogue string (10-200 chars)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
        """
        prompt = self._build_npc_dialogue_prompt(
            npc_name=npc_name,
            npc_description=npc_description,
            npc_role=npc_role,
            theme=theme,
            location_name=location_name
        )

        response_text = self._call_llm(prompt)

        # Clean and validate response
        dialogue = response_text.strip().strip('"').strip("'")
        if len(dialogue) < 10:
            raise AIGenerationError("Generated dialogue too short")
        if len(dialogue) > 200:
            dialogue = dialogue[:197] + "..."

        return dialogue

    def _build_npc_dialogue_prompt(
        self,
        npc_name: str,
        npc_description: str,
        npc_role: str,
        theme: str,
        location_name: str
    ) -> str:
        """Build prompt for NPC dialogue generation."""
        return self.config.npc_dialogue_prompt.format(
            npc_name=npc_name,
            npc_description=npc_description,
            npc_role=npc_role,
            theme=theme,
            location_name=location_name or "unknown location"
        )

    def generate_enemy(
        self,
        theme: str,
        location_name: str,
        player_level: int
    ) -> dict:
        """Generate an enemy with AI.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            location_name: Name of the current location
            player_level: Player's current level for scaling

        Returns:
            Dictionary with: name, description, attack_flavor, health,
            attack_power, defense, xp_reward, level

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt
        prompt = self._build_enemy_prompt(
            theme=theme,
            location_name=location_name,
            player_level=player_level
        )

        # Call LLM
        response_text = self._call_llm(prompt)

        # Parse and validate response
        enemy_data = self._parse_enemy_response(response_text, player_level)

        return enemy_data

    def _build_enemy_prompt(
        self,
        theme: str,
        location_name: str,
        player_level: int
    ) -> str:
        """Build prompt for enemy generation.

        Args:
            theme: World theme
            location_name: Current location name
            player_level: Player's current level

        Returns:
            Formatted prompt string
        """
        return self.config.enemy_generation_prompt.format(
            theme=theme,
            location_name=location_name,
            player_level=player_level
        )

    def _parse_enemy_response(self, response_text: str, player_level: int) -> dict:
        """Parse and validate LLM response for enemy generation.

        Args:
            response_text: Raw response text from LLM
            player_level: Player's current level (used for setting enemy level)

        Returns:
            Dictionary with validated enemy data

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Try to parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e

        # Validate required fields
        required_fields = ["name", "description", "attack_flavor", "health",
                          "attack_power", "defense", "xp_reward"]
        for field in required_fields:
            if field not in data:
                raise AIGenerationError(f"Response missing required field: {field}")

        # Validate name length (2-30 chars)
        name = data["name"].strip()
        if len(name) < 2:
            raise AIGenerationError(
                f"Enemy name too short (min 2 chars): {name}"
            )
        if len(name) > 30:
            raise AIGenerationError(
                f"Enemy name too long (max 30 chars): {name}"
            )

        # Validate description length (10-150 chars)
        description = data["description"].strip()
        if len(description) < 10:
            raise AIGenerationError(
                f"Enemy description too short (min 10 chars)"
            )
        if len(description) > 150:
            raise AIGenerationError(
                f"Enemy description too long (max 150 chars)"
            )

        # Validate attack_flavor length (10-100 chars)
        attack_flavor = data["attack_flavor"].strip()
        if len(attack_flavor) < 10:
            raise AIGenerationError(
                f"Attack flavor too short (min 10 chars)"
            )
        if len(attack_flavor) > 100:
            raise AIGenerationError(
                f"Attack flavor too long (max 100 chars)"
            )

        # Validate positive stats
        for stat in ["health", "attack_power", "defense", "xp_reward"]:
            if not isinstance(data[stat], (int, float)) or data[stat] <= 0:
                raise AIGenerationError(
                    f"Stat '{stat}' must be a positive number"
                )

        # Return validated data with level
        return {
            "name": name,
            "description": description,
            "attack_flavor": attack_flavor,
            "health": int(data["health"]),
            "attack_power": int(data["attack_power"]),
            "defense": int(data["defense"]),
            "xp_reward": int(data["xp_reward"]),
            "level": player_level
        }

    def generate_item(
        self,
        theme: str,
        location_name: str,
        player_level: int,
        item_type: Optional["ItemType"] = None
    ) -> dict:
        """Generate an item with AI.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            location_name: Name of the current location
            player_level: Player's current level for scaling
            item_type: Optional item type constraint (WEAPON, ARMOR, CONSUMABLE, MISC)

        Returns:
            Dictionary with: name, description, item_type, damage_bonus,
            defense_bonus, heal_amount, suggested_price

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt
        prompt = self._build_item_prompt(
            theme=theme,
            location_name=location_name,
            player_level=player_level,
            item_type=item_type
        )

        # Call LLM
        response_text = self._call_llm(prompt)

        # Parse and validate response
        item_data = self._parse_item_response(response_text)

        return item_data

    def _build_item_prompt(
        self,
        theme: str,
        location_name: str,
        player_level: int,
        item_type: Optional["ItemType"] = None
    ) -> str:
        """Build prompt for item generation.

        Args:
            theme: World theme
            location_name: Current location name
            player_level: Player's current level
            item_type: Optional item type constraint

        Returns:
            Formatted prompt string
        """
        # Format item type hint
        if item_type is not None:
            item_type_hint = f"Generate a {item_type.value} item"
        else:
            item_type_hint = "Generate any type of item"

        return self.config.item_generation_prompt.format(
            theme=theme,
            location_name=location_name,
            player_level=player_level,
            item_type_hint=item_type_hint
        )

    def _parse_item_response(self, response_text: str) -> dict:
        """Parse and validate LLM response for item generation.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Dictionary with validated item data

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Import here to avoid circular import
        from cli_rpg.models.item import Item, ItemType

        # Try to parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e

        # Validate required fields
        required_fields = ["name", "description", "item_type", "damage_bonus",
                          "defense_bonus", "heal_amount", "suggested_price"]
        for field in required_fields:
            if field not in data:
                raise AIGenerationError(f"Response missing required field: {field}")

        # Validate name length (2-30 chars)
        name = data["name"].strip()
        if len(name) < Item.MIN_NAME_LENGTH:
            raise AIGenerationError(
                f"Item name too short (min {Item.MIN_NAME_LENGTH} chars): {name}"
            )
        if len(name) > Item.MAX_NAME_LENGTH:
            raise AIGenerationError(
                f"Item name too long (max {Item.MAX_NAME_LENGTH} chars): {name}"
            )

        # Validate description length (1-200 chars)
        description = data["description"].strip()
        if len(description) < Item.MIN_DESC_LENGTH:
            raise AIGenerationError(
                f"Item description too short (min {Item.MIN_DESC_LENGTH} char)"
            )
        if len(description) > Item.MAX_DESC_LENGTH:
            raise AIGenerationError(
                f"Item description too long (max {Item.MAX_DESC_LENGTH} chars)"
            )

        # Validate item_type
        item_type_str = data["item_type"].lower().strip()
        valid_types = [t.value for t in ItemType]
        if item_type_str not in valid_types:
            raise AIGenerationError(
                f"Invalid item_type '{item_type_str}'. Must be one of: {valid_types}"
            )

        # Validate non-negative stats
        for stat in ["damage_bonus", "defense_bonus", "heal_amount"]:
            if not isinstance(data[stat], (int, float)) or data[stat] < 0:
                raise AIGenerationError(
                    f"Stat '{stat}' must be a non-negative number"
                )

        # Validate positive price
        if not isinstance(data["suggested_price"], (int, float)) or data["suggested_price"] <= 0:
            raise AIGenerationError(
                "suggested_price must be a positive number"
            )

        # Return validated data
        return {
            "name": name,
            "description": description,
            "item_type": item_type_str,
            "damage_bonus": int(data["damage_bonus"]),
            "defense_bonus": int(data["defense_bonus"]),
            "heal_amount": int(data["heal_amount"]),
            "suggested_price": int(data["suggested_price"])
        }
