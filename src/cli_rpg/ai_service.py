"""AI service for generating game content using LLMs."""

import json
import hashlib
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.item import ItemType
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
        elif self.provider == "ollama":
            # Ollama uses OpenAI-compatible API with custom base_url
            base_url = config.ollama_base_url or "http://localhost:11434/v1"
            self.client = OpenAI(api_key=config.api_key, base_url=base_url)
        else:
            # Default to OpenAI
            self.client = OpenAI(api_key=config.api_key)

        # Initialize cache if enabled
        self._cache: dict[str, tuple[dict, float]] = {}  # key -> (data, timestamp)

        # Load persisted cache from disk if caching is enabled
        if self.config.enable_caching:
            self._load_cache_from_file()
    
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
        elif self.provider == "ollama":
            # Ollama uses OpenAI-compatible API
            return self._call_openai(prompt, is_ollama=True)
        else:
            return self._call_openai(prompt)

    def _call_openai(self, prompt: str, is_ollama: bool = False) -> str:
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

            except openai.APIConnectionError as e:
                # Connection error - may be Ollama not running
                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                if is_ollama:
                    raise AIServiceError(
                        f"Failed to connect to Ollama after {attempt + 1} attempts. "
                        "Is Ollama running? Start it with 'ollama serve' or check OLLAMA_BASE_URL."
                    ) from e
                raise AIServiceError(f"API call failed after {attempt + 1} attempts: {str(e)}") from e

            except openai.RateLimitError as e:
                # Rate limit - retry
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
        raise AIServiceError(f"API call failed after retries: {str(last_error)}") from last_error  # pragma: no cover

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
        raise AIServiceError(f"API call failed after retries: {str(last_error)}") from last_error  # pragma: no cover

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
        self._save_cache_to_file()

    def _load_cache_from_file(self) -> None:
        """Load persisted cache from disk.

        Reads the cache file specified in config, parses JSON, and populates
        the in-memory cache. Expired entries are pruned during load.
        Handles file I/O errors gracefully by logging a warning.
        """
        cache_file = self.config.cache_file
        if not cache_file:
            return

        import os
        if not os.path.exists(cache_file):
            return

        try:
            with open(cache_file, 'r') as f:
                raw_data = json.load(f)

            # Load entries, pruning expired ones
            current_time = time.time()
            for key, entry in raw_data.items():
                if isinstance(entry, dict) and "data" in entry and "timestamp" in entry:
                    timestamp = entry["timestamp"]
                    if current_time - timestamp < self.config.cache_ttl:
                        # Entry is still valid
                        self._cache[key] = (entry["data"], timestamp)
                    # Else: entry expired, don't load it

        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.warning(f"Failed to load cache from {cache_file}: {e}")

    def _save_cache_to_file(self) -> None:
        """Persist cache to disk.

        Writes the in-memory cache to the cache file specified in config.
        Creates parent directories if they don't exist.
        Handles file I/O errors gracefully by logging a warning.
        """
        cache_file = self.config.cache_file
        if not cache_file:
            return

        import os

        try:
            # Create parent directories if needed
            cache_dir = os.path.dirname(cache_file)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)

            # Convert cache to serializable format
            serializable_cache = {}
            for key, (data, timestamp) in self._cache.items():
                serializable_cache[key] = {
                    "data": data,
                    "timestamp": timestamp
                }

            with open(cache_file, 'w') as f:
                json.dump(serializable_cache, f)

        except (IOError, OSError) as e:
            logger.warning(f"Failed to save cache to {cache_file}: {e}")

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
        self._save_cache_to_file()

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
                "Enemy description too short (min 10 chars)"
            )
        if len(description) > 150:
            raise AIGenerationError(
                "Enemy description too long (max 150 chars)"
            )

        # Validate attack_flavor length (10-100 chars)
        attack_flavor = data["attack_flavor"].strip()
        if len(attack_flavor) < 10:
            raise AIGenerationError(
                "Attack flavor too short (min 10 chars)"
            )
        if len(attack_flavor) > 100:
            raise AIGenerationError(
                "Attack flavor too long (max 100 chars)"
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

    def generate_lore(
        self,
        theme: str,
        location_name: str = "",
        lore_category: str = "history"
    ) -> str:
        """Generate contextual world lore/history snippet.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            location_name: Current location name for context (optional)
            lore_category: Type of lore - "history", "legend", or "secret"

        Returns:
            Generated lore text string (50-500 chars)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
        """
        prompt = self._build_lore_prompt(
            theme=theme,
            location_name=location_name,
            lore_category=lore_category
        )

        response_text = self._call_llm(prompt)

        # Clean and validate response
        lore = response_text.strip().strip('"').strip("'")

        if len(lore) < 50:
            raise AIGenerationError("Generated lore too short (min 50 chars)")

        if len(lore) > 500:
            lore = lore[:497] + "..."

        return lore

    def _build_lore_prompt(
        self,
        theme: str,
        location_name: str,
        lore_category: str
    ) -> str:
        """Build prompt for lore generation.

        Args:
            theme: World theme
            location_name: Current location name (or empty string)
            lore_category: Type of lore (history, legend, secret)

        Returns:
            Formatted prompt string
        """
        return self.config.lore_generation_prompt.format(
            theme=theme,
            location_name=location_name or "the world",
            lore_category=lore_category
        )

    def generate_quest(
        self,
        theme: str,
        npc_name: str,
        player_level: int,
        location_name: str = ""
    ) -> dict:
        """Generate a quest with AI.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            npc_name: Name of the NPC giving the quest
            player_level: Player's current level for scaling rewards
            location_name: Name of the current location for context

        Returns:
            Dictionary with: name, description, objective_type, target,
            target_count, gold_reward, xp_reward, quest_giver

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt
        prompt = self._build_quest_prompt(
            theme=theme,
            npc_name=npc_name,
            player_level=player_level,
            location_name=location_name
        )

        # Check cache if enabled
        if self.config.enable_caching:
            cached_result = self._get_cached(prompt)
            if cached_result is not None:
                # Ensure quest_giver is set correctly for cached results
                cached_result["quest_giver"] = npc_name
                return cached_result

        # Call LLM
        response_text = self._call_llm(prompt)

        # Parse and validate response
        quest_data = self._parse_quest_response(response_text, npc_name)

        # Cache result if enabled
        if self.config.enable_caching:
            self._set_cached(prompt, quest_data)

        return quest_data

    def _build_quest_prompt(
        self,
        theme: str,
        npc_name: str,
        player_level: int,
        location_name: str = ""
    ) -> str:
        """Build prompt for quest generation.

        Args:
            theme: World theme
            npc_name: Name of the quest-giving NPC
            player_level: Player's current level
            location_name: Current location name (or empty string)

        Returns:
            Formatted prompt string
        """
        return self.config.quest_generation_prompt.format(
            theme=theme,
            npc_name=npc_name,
            player_level=player_level,
            location_name=location_name or "unknown location"
        )

    def _parse_quest_response(self, response_text: str, npc_name: str) -> dict:
        """Parse and validate LLM response for quest generation.

        Args:
            response_text: Raw response text from LLM
            npc_name: Name of the NPC giving the quest (added to result)

        Returns:
            Dictionary with validated quest data

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Try to parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e

        # Validate required fields
        required_fields = ["name", "description", "objective_type", "target",
                          "target_count", "gold_reward", "xp_reward"]
        for field in required_fields:
            if field not in data:
                raise AIGenerationError(f"Response missing required field: {field}")

        # Validate name length (2-30 chars)
        name = data["name"].strip()
        if len(name) < 2:
            raise AIGenerationError(
                f"Quest name too short (min 2 chars): {name}"
            )
        if len(name) > 30:
            raise AIGenerationError(
                f"Quest name too long (max 30 chars): {name}"
            )

        # Validate description length (1-200 chars)
        description = data["description"].strip()
        if len(description) < 1:
            raise AIGenerationError(
                "Quest description too short (min 1 char)"
            )
        if len(description) > 200:
            raise AIGenerationError(
                "Quest description too long (max 200 chars)"
            )

        # Validate objective_type
        objective_type = data["objective_type"].lower().strip()
        valid_types = ["kill", "collect", "explore", "talk", "drop"]
        if objective_type not in valid_types:
            raise AIGenerationError(
                f"Invalid objective_type '{objective_type}'. Must be one of: {valid_types}"
            )

        # Validate target is non-empty
        target = data["target"].strip() if isinstance(data["target"], str) else str(data["target"])
        if not target:
            raise AIGenerationError("Quest target cannot be empty")

        # Validate target_count >= 1
        if not isinstance(data["target_count"], (int, float)) or data["target_count"] < 1:
            raise AIGenerationError(
                "target_count must be at least 1"
            )

        # Validate gold_reward >= 0
        if not isinstance(data["gold_reward"], (int, float)) or data["gold_reward"] < 0:
            raise AIGenerationError(
                "gold_reward must be non-negative"
            )

        # Validate xp_reward >= 0
        if not isinstance(data["xp_reward"], (int, float)) or data["xp_reward"] < 0:
            raise AIGenerationError(
                "xp_reward must be non-negative"
            )

        # Return validated data with quest_giver
        return {
            "name": name,
            "description": description,
            "objective_type": objective_type,
            "target": target,
            "target_count": int(data["target_count"]),
            "gold_reward": int(data["gold_reward"]),
            "xp_reward": int(data["xp_reward"]),
            "quest_giver": npc_name
        }

    def generate_conversation_response(
        self,
        npc_name: str,
        npc_description: str,
        npc_role: str,
        theme: str,
        location_name: str,
        conversation_history: list[dict],
        player_input: str
    ) -> str:
        """Generate a contextual conversation response from an NPC.

        Args:
            npc_name: Name of the NPC
            npc_description: NPC's description
            npc_role: Role type ("merchant", "quest_giver", "villager")
            theme: World theme (e.g., "fantasy", "sci-fi")
            location_name: Current location name for context
            conversation_history: List of previous exchanges [{"role": str, "content": str}]
            player_input: The player's latest message

        Returns:
            Generated response string (10-200 chars)

        Raises:
            AIGenerationError: If generation fails or response is too short
            AIServiceError: If API call fails
        """
        prompt = self._build_conversation_prompt(
            npc_name=npc_name,
            npc_description=npc_description,
            npc_role=npc_role,
            theme=theme,
            location_name=location_name,
            conversation_history=conversation_history,
            player_input=player_input
        )

        response_text = self._call_llm(prompt)

        # Clean and validate response
        response = response_text.strip().strip('"').strip("'")

        if len(response) < 10:
            raise AIGenerationError("Generated conversation response too short")

        if len(response) > 200:
            response = response[:197] + "..."

        return response

    def _build_conversation_prompt(
        self,
        npc_name: str,
        npc_description: str,
        npc_role: str,
        theme: str,
        location_name: str,
        conversation_history: list[dict],
        player_input: str
    ) -> str:
        """Build prompt for NPC conversation response generation.

        Args:
            npc_name: Name of the NPC
            npc_description: NPC's description
            npc_role: Role type
            theme: World theme
            location_name: Current location name
            conversation_history: List of previous exchanges
            player_input: The player's latest message

        Returns:
            Formatted prompt string
        """
        # Format conversation history
        if conversation_history:
            history_lines = []
            for entry in conversation_history:
                role = entry.get("role", "unknown")
                content = entry.get("content", "")
                if role == "player":
                    history_lines.append(f"Player: {content}")
                else:
                    history_lines.append(f"{npc_name}: {content}")
            formatted_history = "\n".join(history_lines)
        else:
            formatted_history = "(No previous conversation)"

        return self.config.npc_conversation_prompt.format(
            npc_name=npc_name,
            npc_description=npc_description,
            npc_role=npc_role,
            theme=theme,
            location_name=location_name or "unknown location",
            conversation_history=formatted_history,
            player_input=player_input
        )
