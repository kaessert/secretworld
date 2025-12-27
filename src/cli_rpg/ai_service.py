"""AI service for generating game content using LLMs."""

import json
import hashlib
import random
import time
from enum import Enum, auto
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from cli_rpg.models.item import ItemType  # pragma: no cover
from openai import OpenAI
import openai

# Conditionally import Anthropic to handle missing package
try:
    from anthropic import Anthropic
    from anthropic.types import TextBlock
    import anthropic as anthropic_module
    ANTHROPIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore[misc, assignment]  # pragma: no cover
    TextBlock = None  # type: ignore[misc, assignment]  # pragma: no cover
    anthropic_module = None  # type: ignore[assignment]  # pragma: no cover
    ANTHROPIC_AVAILABLE = False  # pragma: no cover

import logging

from cli_rpg.ai_config import AIConfig
from cli_rpg.models.location import Location
from cli_rpg.models.world_context import DEFAULT_THEME_ESSENCES, WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.progress import progress_indicator

# Valid directions for grid-based movement (subset of Location.VALID_DIRECTIONS)
GRID_DIRECTIONS: set[str] = {"north", "south", "east", "west"}

# Valid categories for location types
VALID_LOCATION_CATEGORIES: set[str] = {
    "town", "dungeon", "wilderness", "settlement",
    "ruins", "cave", "forest", "mountain", "village"
}


class LayoutType(Enum):
    """Layout types for procedural dungeon/area generation."""

    LINEAR = auto()      # Corridor-style progression (caves, mines)
    BRANCHING = auto()   # Current default behavior (forests, ruins)
    HUB = auto()         # Central room with spokes (temples, shrines)
    MAZE = auto()        # Multiple paths with dead ends (dungeons)


# Category to layout type mapping
CATEGORY_LAYOUTS: dict[str, LayoutType] = {
    # Linear (progression-focused)
    "cave": LayoutType.LINEAR,
    "mine": LayoutType.LINEAR,
    # Hub (central with spokes)
    "temple": LayoutType.HUB,
    "monastery": LayoutType.HUB,
    "shrine": LayoutType.HUB,
    # Maze (exploration-focused)
    "dungeon": LayoutType.MAZE,
    # Everything else uses BRANCHING (forest, ruins, wilderness, etc.)
}


logger = logging.getLogger(__name__)

# Valid obtainable items for COLLECT quest validation
# Includes: shop items, loot drops, forage/hunt/gather items, crafted items
OBTAINABLE_ITEMS: frozenset[str] = frozenset({
    # Shop items (static shops)
    "health potion", "antidote", "travel rations", "iron sword", "leather armor",
    "torch", "lockpick", "camping supplies", "stamina potion", "steel sword",
    "chainmail", "iron helmet", "greater health potion", "fine steel sword",
    "plate armor",
    # Caravan event items
    "exotic spices", "traveler's map", "foreign elixir", "rare gemstone",
    # Loot drops - weapons (prefix + name combinations)
    "rusty sword", "rusty dagger", "rusty axe", "rusty mace", "rusty spear",
    "iron dagger", "iron axe", "iron mace", "iron spear",
    "steel dagger", "steel axe", "steel mace", "steel spear",
    "sharp sword", "sharp dagger", "sharp axe", "sharp mace", "sharp spear",
    "worn sword", "worn dagger", "worn axe", "worn mace", "worn spear",
    "old sword", "old dagger", "old axe", "old mace", "old spear",
    # Loot drops - armor (prefix + name combinations)
    "worn armor", "worn shield", "worn helmet", "worn gauntlets", "worn boots",
    "sturdy armor", "sturdy shield", "sturdy helmet", "sturdy gauntlets", "sturdy boots",
    "leather shield", "leather helmet", "leather gauntlets", "leather boots",
    "chain armor", "chain shield", "chain helmet", "chain gauntlets", "chain boots",
    "old armor", "old shield", "old helmet", "old gauntlets", "old boots",
    # Loot drops - consumables
    "healing elixir", "life draught",
    "cure vial", "purification elixir",
    # Loot drops - misc
    "gold coin", "strange key", "monster fang", "gem stone",
    # Wandering merchant items (prefix + name combinations)
    "sturdy blade", "sturdy dagger", "sturdy mace", "sturdy staff",
    "sharp blade", "sharp dagger", "sharp mace", "sharp staff",
    "fine blade", "fine dagger", "fine mace", "fine staff",
    "tempered blade", "tempered dagger", "tempered mace", "tempered staff",
    "padded vest", "padded guard", "padded helm", "padded gloves",
    "leather vest", "leather guard", "leather helm", "leather gloves",
    "chain vest", "chain guard", "chain helm", "chain gloves",
    "reinforced vest", "reinforced guard", "reinforced helm", "reinforced gloves",
    "healing tonic", "restoration brew",
    # Forage items
    "herbs", "wild berries", "medicinal root", "moonpetal flower",
    # Hunt items
    "raw meat", "animal pelt", "cooked meat",
    # Gather items (resources)
    "wood", "fiber", "stone", "iron ore",
    # Crafted items
    "rope", "stone hammer", "healing salve", "bandage", "wooden shield",
    "iron armor",  # crafted version (same name as loot)
})


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

    # Type annotation for client that can be either OpenAI or Anthropic
    client: Any

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
        # Cache can hold dict (for single location) or list (for area locations)
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (data, timestamp)

        # Load persisted cache from disk if caching is enabled
        if self.config.enable_caching:
            self._load_cache_from_file()
    
    def generate_location(
        self,
        theme: str,
        context_locations: Optional[list[str]] = None,
        source_location: Optional[str] = None,
        direction: Optional[str] = None,
        terrain_type: Optional[str] = None,
        world_context: Optional[WorldContext] = None
    ) -> dict:
        """Generate a new location based on context.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            context_locations: List of existing location names
            source_location: Location to expand from (deprecated, kept for compatibility)
            direction: Direction of expansion from source (deprecated, kept for compatibility)
            terrain_type: Optional terrain type (e.g., "desert", "forest") for coherent generation
            world_context: Optional WorldContext for theme essence enrichment

        Returns:
            Dictionary with keys: name, description, category, npcs

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
            terrain_type=terrain_type,
            world_context=world_context
        )

        # Check cache if enabled
        if self.config.enable_caching:
            cached_result = self._get_cached(prompt)
            if cached_result is not None:
                return cached_result

        # Define the generation function that will be retried on parse failures
        def _do_generate() -> dict:
            response_text = self._call_llm(prompt, generation_type="location")
            return self._parse_location_response(response_text)

        # Call with retry wrapper for parse/validation failures
        location_data = self._generate_with_retry(_do_generate)

        # Cache result if enabled
        if self.config.enable_caching:
            self._set_cached(prompt, location_data)

        return location_data
    
    def _build_location_prompt(
        self,
        theme: str,
        context_locations: list[str],
        terrain_type: Optional[str] = None,
        world_context: Optional[WorldContext] = None
    ) -> str:
        """Build prompt for location generation.

        Args:
            theme: World theme
            context_locations: List of existing location names
            terrain_type: Optional terrain type (e.g., "desert", "forest")
            world_context: Optional WorldContext for theme essence enrichment

        Returns:
            Formatted prompt string
        """
        # Format context locations
        if context_locations:
            location_list = ", ".join(context_locations)
        else:
            location_list = "None yet"

        # Format terrain type
        terrain_text = terrain_type if terrain_type else "wilderness"

        # Extract theme essence from WorldContext or use default
        if world_context:
            theme_essence = world_context.theme_essence
        else:
            theme_essence = DEFAULT_THEME_ESSENCES.get(theme, "")

        # Use template from config
        prompt = self.config.location_generation_prompt.format(
            theme=theme,
            theme_essence=theme_essence,
            context_locations=location_list,
            terrain_type=terrain_text
        )

        return prompt
    
    def _call_llm(self, prompt: str, generation_type: str = "default") -> str:
        """Call LLM API with retry logic and progress indication.

        Args:
            prompt: The prompt to send to the LLM
            generation_type: Type of content being generated for progress messages
                            (location, npc, enemy, lore, area, default)

        Returns:
            Response text from the LLM

        Raises:
            AIServiceError: If API call fails after retries
            AITimeoutError: If request times out
        """
        with progress_indicator(generation_type):
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
        last_error: Optional[Exception] = None

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

                content = response.choices[0].message.content
                return content if content is not None else ""

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
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.config.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.config.max_tokens
                )

                # Extract text from first content block (must be TextBlock)
                first_block = response.content[0]
                if TextBlock is not None and isinstance(first_block, TextBlock):
                    return first_block.text
                # Fallback: access text attribute directly (for mocked responses in tests)
                return getattr(first_block, 'text', '')

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

    def _generate_with_retry(
        self,
        generation_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Wrap a generation function with retry logic for parse/validation failures.

        This method retries on AIGenerationError (parse/validation failures) but NOT
        on AIServiceError (API failures), as those already have API-level retries.

        Args:
            generation_func: The generation function to call (must return the result)
            *args: Positional arguments to pass to generation_func
            **kwargs: Keyword arguments to pass to generation_func

        Returns:
            Result from generation_func

        Raises:
            AIGenerationError: If all retries fail
            AIServiceError: If API call fails (passed through without retry)
            AITimeoutError: If request times out (passed through without retry)
        """
        last_error: Optional[AIGenerationError] = None
        max_retries = self.config.generation_max_retries

        for attempt in range(max_retries + 1):  # 1 initial + max_retries
            try:
                return generation_func(*args, **kwargs)
            except AIGenerationError as e:
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff: 0.5s, 1s, 2s, ...
                    delay = 0.5 * (2 ** attempt)
                    logger.debug(
                        f"Generation attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
                # Final failure - log full error
                logger.warning(
                    f"Generation failed after {max_retries + 1} attempts: {e}"
                )
                raise
            except (AIServiceError, AITimeoutError):
                # Don't retry API-level errors - they already have their own retry logic
                raise

        # Should not reach here, but just in case
        raise last_error  # type: ignore[misc]  # pragma: no cover

    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from markdown code blocks if present.

        Args:
            response_text: Raw response text from LLM (may contain markdown)

        Returns:
            Extracted JSON string, or original text if no code block found
        """
        import re
        # Match ```json ... ``` or ``` ... ``` (with optional language tag)
        pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        match = re.search(pattern, response_text)
        if match:
            return match.group(1).strip()
        return response_text.strip()

    def _extract_ascii_art_from_code_block(self, response_text: str) -> str:
        """Extract ASCII art from markdown code fence if present.

        Args:
            response_text: Raw response text that may contain code fences

        Returns:
            Extracted content without code fences, or original text if no fence found
        """
        import re
        # Match ```<optional-lang>\n ... ``` (handles ascii, text, or no language tag)
        # The newline after opening fence is required to avoid eating leading spaces
        pattern = r'```(?:\w*)?\n([\s\S]*?)\n?```'
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)
        return response_text

    def _repair_truncated_json(self, json_text: str) -> str:
        """Attempt to repair truncated JSON by closing unclosed brackets.

        Args:
            json_text: Potentially truncated JSON string

        Returns:
            Repaired JSON string, or original if repair not possible
        """
        repaired = json_text.rstrip()

        # Check for unclosed string (track in_string state)
        in_string = False
        escaped = False
        for char in repaired:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = not in_string

        # If we're in an unclosed string, close it
        if in_string:
            repaired += '"'

        # Track opening brackets to close in correct order
        closers: list[str] = []
        in_string = False
        escaped = False
        for char in repaired:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    closers.append('}')
                elif char == '[':
                    closers.append(']')
                elif char in '}]' and closers and closers[-1] == char:
                    closers.pop()

        # If no unclosed brackets, return original
        if not closers:
            return json_text

        # Append closing brackets in reverse order
        repaired += ''.join(reversed(closers))
        logger.warning("Repaired truncated JSON response")
        return repaired

    def _log_parse_failure(self, response_text: str, error: Exception, context: str = "") -> None:
        """Log full AI response when JSON parsing fails.

        Args:
            response_text: The raw response text that failed to parse
            error: The exception that was raised
            context: Optional context about what was being parsed (e.g., "location", "area")
        """
        logger.debug(
            f"AI response parse failure{f' ({context})' if context else ''}: {error}\n"
            f"Full response ({len(response_text)} chars):\n{response_text}"
        )

    def _parse_location_response(self, response_text: str) -> dict:
        """Parse and validate LLM response.
        
        Args:
            response_text: Raw response text from LLM
        
        Returns:
            Dictionary with validated location data
        
        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Try to parse JSON, attempting repair if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            if repaired != json_text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    self._log_parse_failure(response_text, e, "location")
                    raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
            else:
                self._log_parse_failure(response_text, e, "location")
                raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e

        # Validate required fields (no connections - WFC handles terrain structure)
        required_fields = ["name", "description"]
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
        
        # Extract and validate category (optional field)
        # Note: connections field is ignored - WFC handles terrain structure
        category = data.get("category")
        if category is not None:
            category = category.strip().lower() if isinstance(category, str) else None
            if category not in VALID_LOCATION_CATEGORIES:
                logger.warning(
                    f"Invalid category '{category}' for location '{name}', defaulting to None"
                )
                category = None

        # Parse NPCs (optional field)
        npcs = self._parse_npcs(data.get("npcs", []), name)

        # Return validated data WITHOUT connections (WFC handles terrain structure)
        return {
            "name": name,
            "description": description,
            "category": category,
            "npcs": npcs
        }
    
    def _parse_npcs(self, npcs_data: list, location_name: str) -> list[dict]:
        """Parse and validate NPC data from AI response.

        Args:
            npcs_data: List of NPC dictionaries from AI response
            location_name: Name of the location (for logging)

        Returns:
            List of validated NPC dictionaries
        """
        if not isinstance(npcs_data, list):
            logger.warning(
                f"Invalid npcs field for location '{location_name}', expected list"
            )
            return []

        # Valid roles for NPCs
        valid_roles = ("villager", "merchant", "quest_giver", "guard", "traveler", "innkeeper")

        validated_npcs = []
        for idx, npc in enumerate(npcs_data):
            if not isinstance(npc, dict):
                logger.warning(
                    f"Invalid NPC {idx} for location '{location_name}', expected dict"
                )
                continue

            # Validate name (2-30 chars)
            name = npc.get("name", "").strip() if isinstance(npc.get("name"), str) else ""
            if len(name) < 2 or len(name) > 30:
                logger.warning(
                    f"Invalid NPC name length at location '{location_name}': '{name}'"
                )
                continue

            # Validate description (1-200 chars)
            description = npc.get("description", "").strip() if isinstance(npc.get("description"), str) else ""
            if len(description) < 1 or len(description) > 200:
                logger.warning(
                    f"Invalid NPC description length at location '{location_name}': NPC '{name}'"
                )
                continue

            # Get dialogue (optional, default to empty)
            dialogue = npc.get("dialogue", "").strip() if isinstance(npc.get("dialogue"), str) else ""
            if not dialogue:
                dialogue = f"Hello, traveler."

            # Get role (default to 'villager')
            role = npc.get("role", "villager").strip().lower() if isinstance(npc.get("role"), str) else "villager"
            if role not in valid_roles:
                logger.warning(
                    f"Invalid NPC role '{role}' at location '{location_name}', defaulting to 'villager'"
                )
                role = "villager"

            # Get faction (optional)
            faction = None
            if isinstance(npc.get("faction"), str):
                faction_str = npc["faction"].strip()
                if faction_str:
                    faction = faction_str

            # Parse shop_inventory (optional, for merchants)
            shop_inventory = self._parse_shop_inventory(npc.get("shop_inventory", []), name, location_name)

            npc_data = {
                "name": name,
                "description": description,
                "dialogue": dialogue,
                "role": role
            }

            # Add optional fields if present
            if faction:
                npc_data["faction"] = faction
            if shop_inventory is not None:
                npc_data["shop_inventory"] = shop_inventory

            validated_npcs.append(npc_data)

        return validated_npcs

    def _parse_shop_inventory(
        self, inventory_data: list, npc_name: str, location_name: str
    ) -> Optional[list[dict]]:
        """Parse and validate shop inventory from AI response.

        Args:
            inventory_data: List of item dictionaries from AI response
            npc_name: Name of the NPC (for logging)
            location_name: Name of the location (for logging)

        Returns:
            List of validated shop item dictionaries, or None if not provided
        """
        if not isinstance(inventory_data, list):
            return None

        # Empty list is valid (will trigger fallback to default shop)
        if len(inventory_data) == 0:
            return []

        validated_items = []
        for item in inventory_data:
            if not isinstance(item, dict):
                continue

            # Validate name
            item_name = item.get("name", "").strip() if isinstance(item.get("name"), str) else ""
            if len(item_name) < 1:
                logger.warning(
                    f"Invalid shop item name for NPC '{npc_name}' at '{location_name}'"
                )
                continue

            # Validate price
            price = item.get("price")
            if not isinstance(price, (int, float)) or price < 0:
                logger.warning(
                    f"Invalid shop item price for '{item_name}' at '{location_name}'"
                )
                continue

            validated_items.append({
                "name": item_name,
                "price": int(price)
            })

        return validated_items

    def _get_cached(self, prompt: str) -> Optional[dict[str, Any]]:
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
                result: dict[str, Any] = data.copy()  # Return a copy to avoid mutations
                return result
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
            - category: Location category (optional)
            - npcs: List of NPC data (optional)

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

        # Define the generation function that will be retried on parse failures
        def _do_generate() -> list[dict]:
            response_text = self._call_llm(prompt, generation_type="area")
            return self._parse_area_response(response_text, size)

        # Call with retry wrapper for parse/validation failures
        area_data = self._generate_with_retry(_do_generate)

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
6. Relative coordinates must be within bounds: x from -3 to 3, y from -3 to 3 (7x7 grid max)
7. All locations must be connected to at least one other location in the area
8. The entry location MUST have a "{back_direction}" exit (to connect back to the existing world)
9. Valid directions: north, south, east, west (no up/down for this area)
10. Ensure internal consistency: if A connects north to B, then B must connect south to A
11. Include a category for each location (one of: town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
12. Optionally include 0-2 NPCs per location appropriate to that location
   - Each NPC needs: name (2-30 chars), description (1-200 chars), dialogue (a greeting), role (villager, merchant, or quest_giver)

Respond with valid JSON array (no additional text):
[
  {{
    "name": "Entry Location Name",
    "description": "Description of entry location",
    "relative_coords": [0, 0],
    "connections": {{"{back_direction}": "EXISTING_WORLD", "north": "Next Location Name"}},
    "category": "wilderness",
    "npcs": [
      {{
        "name": "NPC Name",
        "description": "Brief description of the NPC.",
        "dialogue": "What the NPC says when greeted.",
        "role": "villager"
      }}
    ]
  }},
  {{
    "name": "Next Location Name",
    "description": "Description",
    "relative_coords": [0, 1],
    "connections": {{"south": "Entry Location Name"}},
    "category": "forest",
    "npcs": []
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
        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Try to parse JSON, attempting repair if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            if repaired != json_text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    self._log_parse_failure(response_text, e, "area")
                    raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
            else:
                self._log_parse_failure(response_text, e, "area")
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
        # Check required fields (connections no longer required - navigation is coordinate-based)
        required_fields = ["name", "description", "relative_coords"]
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

        # Note: connections field is ignored - navigation is coordinate-based via SubGrid/WorldGrid
        # AI may still generate connections, but we don't use them

        # Extract and validate category (optional field)
        category = loc.get("category")
        if category is not None:
            category = category.strip().lower() if isinstance(category, str) else None
            if category not in VALID_LOCATION_CATEGORIES:
                logger.warning(
                    f"Invalid category '{category}' for area location '{name}', defaulting to None"
                )
                category = None

        # Parse NPCs (optional field)
        npcs = self._parse_npcs(loc.get("npcs", []), name)

        return {
            "name": name,
            "description": description,
            "relative_coords": coords,
            "category": category,
            "npcs": npcs
        }

    def _get_cached_list(self, prompt: str) -> Optional[list[dict[str, Any]]]:
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
                result: list[dict[str, Any]] = copy.deepcopy(data)
                return result
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

        response_text = self._call_llm(prompt, generation_type="npc")

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
        response_text = self._call_llm(prompt, generation_type="enemy")

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
        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Try to parse JSON, attempting repair if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            if repaired != json_text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    self._log_parse_failure(response_text, e, "enemy")
                    raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
            else:
                self._log_parse_failure(response_text, e, "enemy")
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

    def generate_ascii_art(
        self,
        enemy_name: str,
        enemy_description: str,
        theme: str
    ) -> str:
        """Generate ASCII art for an enemy.

        Args:
            enemy_name: Name of the enemy
            enemy_description: Description of the enemy's appearance
            theme: World theme (e.g., "fantasy", "sci-fi")

        Returns:
            ASCII art string (5-8 lines, max 40 chars wide)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt
        prompt = self._build_ascii_art_prompt(
            enemy_name=enemy_name,
            enemy_description=enemy_description,
            theme=theme
        )

        # Call LLM
        response_text = self._call_llm(prompt, generation_type="art")

        # Clean and validate response
        art = self._parse_ascii_art_response(response_text)

        return art

    def _build_ascii_art_prompt(
        self,
        enemy_name: str,
        enemy_description: str,
        theme: str
    ) -> str:
        """Build prompt for ASCII art generation.

        Args:
            enemy_name: Name of the enemy
            enemy_description: Description of the enemy's appearance
            theme: World theme

        Returns:
            Formatted prompt string
        """
        return self.config.ascii_art_generation_prompt.format(
            enemy_name=enemy_name,
            enemy_description=enemy_description,
            theme=theme
        )

    def _parse_ascii_art_response(self, response_text: str) -> str:
        """Parse and validate LLM response for ASCII art generation.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Cleaned ASCII art string

        Raises:
            AIGenerationError: If validation fails
        """
        # Extract from code fence if present
        art = self._extract_ascii_art_from_code_block(response_text)
        # Strip only trailing whitespace, preserve first line's leading spaces
        art = art.rstrip()
        # Remove leading empty lines
        while art.startswith("\n"):
            art = art[1:]

        # Validate minimum content
        lines = art.splitlines()
        if len(lines) < 3:
            raise AIGenerationError("ASCII art too short (min 3 lines)")

        # Truncate lines that are too long (max 40 chars)
        cleaned_lines = []
        for line in lines[:8]:  # Max 8 lines
            if len(line) > 40:
                cleaned_lines.append(line[:40])
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def generate_location_ascii_art(
        self,
        location_name: str,
        location_description: str,
        location_category: Optional[str],
        theme: str
    ) -> str:
        """Generate ASCII art for a location.

        Args:
            location_name: Name of the location
            location_description: Description of the location's appearance
            location_category: Category of the location (town, forest, etc.)
            theme: World theme (e.g., "fantasy", "sci-fi")

        Returns:
            ASCII art string (6-10 lines, max 50 chars wide)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt
        prompt = self._build_location_ascii_art_prompt(
            location_name=location_name,
            location_description=location_description,
            location_category=location_category,
            theme=theme
        )

        # Call LLM
        response_text = self._call_llm(prompt, generation_type="art")

        # Clean and validate response
        art = self._parse_location_ascii_art_response(response_text)

        return art

    def _build_location_ascii_art_prompt(
        self,
        location_name: str,
        location_description: str,
        location_category: Optional[str],
        theme: str
    ) -> str:
        """Build prompt for location ASCII art generation.

        Args:
            location_name: Name of the location
            location_description: Description of the location
            location_category: Category of the location
            theme: World theme

        Returns:
            Formatted prompt string
        """
        return self.config.location_ascii_art_generation_prompt.format(
            location_name=location_name,
            location_description=location_description,
            location_category=location_category or "unknown",
            theme=theme
        )

    def _parse_location_ascii_art_response(self, response_text: str) -> str:
        """Parse and validate LLM response for location ASCII art generation.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Cleaned ASCII art string

        Raises:
            AIGenerationError: If validation fails
        """
        # Extract from code fence if present
        art = self._extract_ascii_art_from_code_block(response_text)
        # Strip only trailing whitespace, preserve first line's leading spaces
        art = art.rstrip()
        # Remove leading empty lines
        while art.startswith("\n"):
            art = art[1:]

        # Validate minimum content
        lines = art.splitlines()
        if len(lines) < 3:
            raise AIGenerationError("Location ASCII art too short (min 3 lines)")

        # Truncate lines that are too long (max 50 chars for locations)
        cleaned_lines = []
        for line in lines[:10]:  # Max 10 lines for locations
            if len(line) > 50:
                cleaned_lines.append(line[:50])
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

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
        response_text = self._call_llm(prompt, generation_type="item")

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

        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Try to parse JSON, attempting repair if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            if repaired != json_text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    self._log_parse_failure(response_text, e, "item")
                    raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
            else:
                self._log_parse_failure(response_text, e, "item")
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

        response_text = self._call_llm(prompt, generation_type="lore")

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
        location_name: str = "",
        valid_locations: Optional[set[str]] = None,
        valid_npcs: Optional[set[str]] = None,
        world_context: Optional[WorldContext] = None,
        region_context: Optional[RegionContext] = None
    ) -> dict:
        """Generate a quest with AI.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            npc_name: Name of the NPC giving the quest
            player_level: Player's current level for scaling rewards
            location_name: Name of the current location for context
            valid_locations: Optional set of valid location names (lowercase) for
                EXPLORE quest validation. If None, EXPLORE validation is skipped.
            valid_npcs: Optional set of valid NPC names (lowercase) for
                TALK quest validation. If None, TALK validation is skipped.
            world_context: Optional WorldContext for theme essence and tone
            region_context: Optional RegionContext for region theme and danger level

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
            location_name=location_name,
            world_context=world_context,
            region_context=region_context
        )

        # Check cache if enabled
        if self.config.enable_caching:
            cached_result = self._get_cached(prompt)
            if cached_result is not None:
                # Ensure quest_giver is set correctly for cached results
                cached_result["quest_giver"] = npc_name
                return cached_result

        # Call LLM
        response_text = self._call_llm(prompt, generation_type="quest")

        # Parse and validate response
        quest_data = self._parse_quest_response(
            response_text, npc_name, valid_locations=valid_locations, valid_npcs=valid_npcs
        )

        # Cache result if enabled
        if self.config.enable_caching:
            self._set_cached(prompt, quest_data)

        return quest_data

    def _build_quest_prompt(
        self,
        theme: str,
        npc_name: str,
        player_level: int,
        location_name: str = "",
        world_context: Optional[WorldContext] = None,
        region_context: Optional[RegionContext] = None
    ) -> str:
        """Build prompt for quest generation.

        Args:
            theme: World theme
            npc_name: Name of the quest-giving NPC
            player_level: Player's current level
            location_name: Current location name (or empty string)
            world_context: Optional WorldContext for theme essence and tone
            region_context: Optional RegionContext for region theme and danger level

        Returns:
            Formatted prompt string
        """
        # Extract context values with sensible fallbacks
        theme_essence = world_context.theme_essence if world_context else theme
        tone = world_context.tone if world_context else "adventurous"
        region_theme = region_context.theme if region_context else "unexplored lands"
        danger_level = region_context.danger_level if region_context else "moderate"

        return self.config.quest_generation_prompt.format(
            theme=theme,
            theme_essence=theme_essence,
            tone=tone,
            region_theme=region_theme,
            danger_level=danger_level,
            npc_name=npc_name,
            player_level=player_level,
            location_name=location_name or "unknown location"
        )

    def _parse_quest_response(
        self,
        response_text: str,
        npc_name: str,
        valid_locations: Optional[set[str]] = None,
        valid_npcs: Optional[set[str]] = None
    ) -> dict:
        """Parse and validate LLM response for quest generation.

        Args:
            response_text: Raw response text from LLM
            npc_name: Name of the NPC giving the quest (added to result)
            valid_locations: Optional set of valid location names (lowercase) for
                EXPLORE quest validation. If None, EXPLORE validation is skipped.
            valid_npcs: Optional set of valid NPC names (lowercase) for
                TALK quest validation. If None, TALK validation is skipped.

        Returns:
            Dictionary with validated quest data

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Try to parse JSON, attempting repair if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            if repaired != json_text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    self._log_parse_failure(response_text, e, "quest")
                    raise AIGenerationError(f"Failed to parse response as JSON: {str(e)}") from e
            else:
                self._log_parse_failure(response_text, e, "quest")
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

        # Validate KILL quest targets against spawnable enemies
        if objective_type == "kill":
            from cli_rpg.combat import VALID_ENEMY_TYPES
            if target.lower() not in VALID_ENEMY_TYPES:
                raise AIGenerationError(
                    f"Invalid KILL quest target '{target}'. Must be a spawnable enemy type."
                )

        # Validate EXPLORE quest targets against known locations
        if objective_type == "explore" and valid_locations is not None:
            if target.lower() not in valid_locations:
                raise AIGenerationError(
                    f"Invalid EXPLORE quest target '{target}'. Must be an existing location."
                )

        # Validate COLLECT quest targets against obtainable items
        if objective_type == "collect":
            if target.lower() not in OBTAINABLE_ITEMS:
                raise AIGenerationError(
                    f"Invalid COLLECT quest target '{target}'. Must be an obtainable item."
                )

        # Validate TALK quest targets against world NPCs
        if objective_type == "talk" and valid_npcs is not None:
            if target.lower() not in valid_npcs:
                raise AIGenerationError(
                    f"Invalid TALK quest target '{target}'. Must be an existing NPC."
                )

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
            "quest_giver": npc_name,
            "difficulty": data.get("difficulty", "normal"),
            "recommended_level": int(data.get("recommended_level", 1)),
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

        response_text = self._call_llm(prompt, generation_type="npc")

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

    def generate_npc_ascii_art(
        self,
        npc_name: str,
        npc_description: str,
        npc_role: str,
        theme: str
    ) -> str:
        """Generate ASCII art for an NPC.

        Args:
            npc_name: Name of the NPC
            npc_description: Description of the NPC's appearance
            npc_role: Role of the NPC (merchant, quest_giver, villager, etc.)
            theme: World theme (e.g., "fantasy", "sci-fi")

        Returns:
            ASCII art string (5-7 lines, max 40 chars wide)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt
        prompt = self._build_npc_ascii_art_prompt(
            npc_name=npc_name,
            npc_description=npc_description,
            npc_role=npc_role,
            theme=theme
        )

        # Call LLM
        response_text = self._call_llm(prompt, generation_type="art")

        # Clean and validate response
        art = self._parse_npc_ascii_art_response(response_text)

        return art

    def _build_npc_ascii_art_prompt(
        self,
        npc_name: str,
        npc_description: str,
        npc_role: str,
        theme: str
    ) -> str:
        """Build prompt for NPC ASCII art generation.

        Args:
            npc_name: Name of the NPC
            npc_description: Description of the NPC
            npc_role: Role of the NPC
            theme: World theme

        Returns:
            Formatted prompt string
        """
        return self.config.npc_ascii_art_generation_prompt.format(
            npc_name=npc_name,
            npc_description=npc_description,
            npc_role=npc_role,
            theme=theme
        )

    def _parse_npc_ascii_art_response(self, response_text: str) -> str:
        """Parse and validate LLM response for NPC ASCII art generation.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Cleaned ASCII art string

        Raises:
            AIGenerationError: If validation fails
        """
        # Extract from code fence if present
        art = self._extract_ascii_art_from_code_block(response_text)
        # Strip only trailing whitespace, preserve first line's leading spaces
        art = art.rstrip()
        # Remove leading empty lines
        while art.startswith("\n"):
            art = art[1:]

        # Validate minimum content
        lines = art.splitlines()
        if len(lines) < 3:
            raise AIGenerationError("NPC ASCII art too short (min 3 lines)")

        # Truncate lines that are too long (max 40 chars for NPCs)
        cleaned_lines = []
        for line in lines[:7]:  # Max 7 lines for NPCs
            if len(line) > 40:
                cleaned_lines.append(line[:40])
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def generate_dream(
        self,
        theme: str,
        dread: int,
        choices: Optional[list[dict]],
        location_name: str,
        is_nightmare: bool
    ) -> str:
        """Generate a dream sequence with AI.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            dread: Current dread level (0-100)
            choices: Player's recorded choices (from game_state.choices)
            location_name: Name of the current location
            is_nightmare: Whether this should be a nightmare (dread >= 50)

        Returns:
            Generated dream text string (20-300 chars)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
        """
        prompt = self._build_dream_prompt(
            theme=theme,
            dread=dread,
            choices=choices,
            location_name=location_name,
            is_nightmare=is_nightmare
        )

        response_text = self._call_llm(prompt, generation_type="dream")

        # Clean and validate response
        dream = response_text.strip().strip('"').strip("'")

        if len(dream) < 20:
            raise AIGenerationError("Generated dream too short (min 20 chars)")

        if len(dream) > 300:
            dream = dream[:297] + "..."

        return dream

    def generate_whisper(
        self,
        theme: str,
        location_category: Optional[str] = None
    ) -> str:
        """Generate an atmospheric whisper with AI.

        Args:
            theme: World theme (e.g., "fantasy", "sci-fi")
            location_category: Category of the current location (e.g., "dungeon", "town")

        Returns:
            Generated whisper text string (10-100 chars)

        Raises:
            AIGenerationError: If generation fails or response is too short
            AIServiceError: If API call fails
        """
        prompt = self._build_whisper_prompt(
            theme=theme,
            location_category=location_category
        )

        response_text = self._call_llm(prompt, generation_type="atmosphere")

        # Clean and validate response
        whisper = response_text.strip().strip('"').strip("'")

        if len(whisper) < 10:
            raise AIGenerationError("Generated whisper too short (min 10 chars)")

        if len(whisper) > 100:
            whisper = whisper[:97] + "..."

        return whisper

    def _build_whisper_prompt(
        self,
        theme: str,
        location_category: Optional[str]
    ) -> str:
        """Build prompt for whisper generation.

        Args:
            theme: World theme
            location_category: Category of the current location

        Returns:
            Formatted prompt string
        """
        return self.config.whisper_generation_prompt.format(
            theme=theme,
            location_category=location_category or "mysterious"
        )

    def _build_dream_prompt(
        self,
        theme: str,
        dread: int,
        choices: Optional[list[dict]],
        location_name: str,
        is_nightmare: bool
    ) -> str:
        """Build prompt for dream generation.

        Args:
            theme: World theme
            dread: Current dread level (0-100)
            choices: Player's recorded choices
            location_name: Current location name
            is_nightmare: Whether this should be a nightmare

        Returns:
            Formatted prompt string
        """
        # Summarize player choices for context
        choices_summary = "None recorded"
        if choices:
            flee_count = sum(1 for c in choices if c.get("choice_type") == "combat_flee")
            kill_count = sum(1 for c in choices if c.get("choice_type") == "combat_kill")
            parts = []
            if flee_count > 0:
                parts.append(f"Fled from combat {flee_count} times")
            if kill_count > 0:
                parts.append(f"Defeated {kill_count} enemies")
            if parts:
                choices_summary = ", ".join(parts)

        # Determine dream type
        dream_type = "nightmare (unsettling, dark)" if is_nightmare else "normal dream (surreal, atmospheric)"

        return self.config.dream_generation_prompt.format(
            theme=theme,
            location_name=location_name or "unknown location",
            dread=dread,
            choices_summary=choices_summary,
            dream_type=dream_type
        )

    def generate_world_context(self, theme: str) -> "WorldContext":
        """Generate world-level thematic context using AI.

        Args:
            theme: Base theme keyword (e.g., "fantasy", "cyberpunk")

        Returns:
            WorldContext with AI-generated theme_essence, naming_style, and tone

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        from datetime import datetime
        from cli_rpg.models.world_context import WorldContext

        prompt = self._build_world_context_prompt(theme)
        response_text = self._call_llm(prompt, generation_type="lore")
        return self._parse_world_context_response(response_text, theme)

    def _build_world_context_prompt(self, theme: str) -> str:
        """Build prompt for world context generation.

        Args:
            theme: Base theme keyword

        Returns:
            Formatted prompt string
        """
        return self.config.world_context_prompt.format(theme=theme)

    def _parse_world_context_response(self, response_text: str, theme: str) -> "WorldContext":
        """Parse and validate LLM response for world context generation.

        Args:
            response_text: Raw response text from LLM
            theme: Base theme keyword for the WorldContext

        Returns:
            WorldContext instance with validated data

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        from datetime import datetime
        from cli_rpg.models.world_context import WorldContext

        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Attempt to parse JSON, repairing if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            # Try to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as e:
                self._log_parse_failure(response_text, e, "world_context")
                raise AIGenerationError(f"Invalid JSON in world context response: {e}")

        # Validate required fields
        required_fields = ["theme_essence", "naming_style", "tone"]
        for field in required_fields:
            if field not in data:
                raise AIGenerationError(f"Missing required field: {field}")
            if not isinstance(data[field], str) or not data[field].strip():
                raise AIGenerationError(f"Field '{field}' must be a non-empty string")

        # Validate field lengths
        theme_essence = data["theme_essence"].strip()
        naming_style = data["naming_style"].strip()
        tone = data["tone"].strip()

        if len(theme_essence) > 200:
            raise AIGenerationError(
                f"theme_essence exceeds 200 characters ({len(theme_essence)} chars)"
            )
        if len(naming_style) > 100:
            raise AIGenerationError(
                f"naming_style exceeds 100 characters ({len(naming_style)} chars)"
            )
        if len(tone) > 100:
            raise AIGenerationError(
                f"tone exceeds 100 characters ({len(tone)} chars)"
            )

        return WorldContext(
            theme=theme,
            theme_essence=theme_essence,
            naming_style=naming_style,
            tone=tone,
            generated_at=datetime.now()
        )

    def generate_region_context(
        self,
        theme: str,
        world_context: "WorldContext",
        coordinates: tuple[int, int],
        terrain_hint: str = "wilderness"
    ) -> "RegionContext":
        """Generate region-level thematic context using AI.

        Args:
            theme: Base theme keyword (e.g., "fantasy", "cyberpunk")
            world_context: Layer 1 context for consistency
            coordinates: Center coordinates of the region
            terrain_hint: Terrain type hint for the region (e.g., "mountains", "swamp")

        Returns:
            RegionContext with AI-generated name, theme, danger_level, landmarks

        Raises:
            AIGenerationError: If generation fails or response invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        from cli_rpg.models.region_context import RegionContext

        prompt = self._build_region_context_prompt(theme, world_context, coordinates, terrain_hint)
        response_text = self._call_llm(prompt, generation_type="area")
        return self._parse_region_context_response(response_text, coordinates)

    def _build_region_context_prompt(
        self,
        theme: str,
        world_context: "WorldContext",
        coordinates: tuple[int, int],
        terrain_hint: str
    ) -> str:
        """Build prompt for region context generation.

        Args:
            theme: Base theme keyword
            world_context: Layer 1 context for consistency
            coordinates: Center coordinates of the region
            terrain_hint: Terrain type hint

        Returns:
            Formatted prompt string
        """
        return self.config.region_context_prompt.format(
            theme=theme,
            theme_essence=world_context.theme_essence,
            naming_style=world_context.naming_style,
            tone=world_context.tone,
            coordinates=f"({coordinates[0]}, {coordinates[1]})",
            terrain_hint=terrain_hint
        )

    def _parse_region_context_response(
        self,
        response_text: str,
        coordinates: tuple[int, int]
    ) -> "RegionContext":
        """Parse and validate LLM response for region context generation.

        Args:
            response_text: Raw response text from LLM
            coordinates: Center coordinates for the RegionContext

        Returns:
            RegionContext instance with validated data

        Raises:
            AIGenerationError: If parsing fails or validation fails
        """
        from datetime import datetime
        from cli_rpg.models.region_context import RegionContext

        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Attempt to parse JSON, repairing if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            # Try to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as e:
                self._log_parse_failure(response_text, e, "region_context")
                raise AIGenerationError(f"Invalid JSON in region context response: {e}")

        # Validate required fields
        required_fields = ["name", "theme", "danger_level"]
        for field in required_fields:
            if field not in data:
                raise AIGenerationError(f"Missing required field: {field}")
            if not isinstance(data[field], str) or not data[field].strip():
                raise AIGenerationError(f"Field '{field}' must be a non-empty string")

        # Validate field lengths
        name = data["name"].strip()
        theme = data["theme"].strip()

        if len(name) > 50:
            raise AIGenerationError(
                f"name exceeds 50 characters ({len(name)} chars)"
            )
        if len(theme) > 200:
            raise AIGenerationError(
                f"theme exceeds 200 characters ({len(theme)} chars)"
            )

        # Validate danger_level mapping
        # LLM returns: low, medium, high, deadly
        # RegionContext uses: safe, moderate, dangerous, deadly
        danger_level_map = {
            "low": "safe",
            "medium": "moderate",
            "high": "dangerous",
            "deadly": "deadly"
        }
        raw_danger = data["danger_level"].strip().lower()
        if raw_danger not in danger_level_map:
            raise AIGenerationError(
                f"Invalid danger_level '{raw_danger}'. Must be one of: low, medium, high, deadly"
            )
        danger_level = danger_level_map[raw_danger]

        # Validate landmarks (optional, default to empty list)
        landmarks = data.get("landmarks", [])
        if not isinstance(landmarks, list):
            landmarks = []
        # Filter and validate landmarks
        validated_landmarks = []
        for lm in landmarks[:5]:  # Max 5 landmarks
            if isinstance(lm, str) and lm.strip():
                lm_stripped = lm.strip()
                if len(lm_stripped) <= 50:
                    validated_landmarks.append(lm_stripped)

        return RegionContext(
            name=name,
            theme=theme,
            danger_level=danger_level,
            landmarks=validated_landmarks,
            coordinates=coordinates,
            generated_at=datetime.now()
        )

    def generate_location_with_context(
        self,
        world_context: "WorldContext",
        region_context: "RegionContext",
        source_location: Optional[str] = None,
        direction: Optional[str] = None,
        terrain_type: Optional[str] = None,
        neighboring_locations: Optional[list[dict]] = None
    ) -> dict:
        """Generate a new location using layered context (Layer 3).

        This method uses the minimal location prompt that expects world and region
        context to be provided. It does NOT generate NPCs - use generate_npcs_for_location
        separately for NPC generation (Layer 4).

        Args:
            world_context: Layer 1 WorldContext with theme essence, naming style, tone
            region_context: Layer 2 RegionContext with region name, theme, danger level
            source_location: Optional location to expand from
            direction: Optional direction of expansion from source
            terrain_type: Optional terrain type (e.g., "desert", "forest") for coherent generation
            neighboring_locations: Optional list of dicts with name and direction for spatial coherence

        Returns:
            Dictionary with keys: name, description, category, npcs (empty list)

        Raises:
            AIGenerationError: If generation fails or response is invalid
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt using minimal template with context
        prompt = self._build_location_with_context_prompt(
            world_context=world_context,
            region_context=region_context,
            source_location=source_location,
            direction=direction,
            terrain_type=terrain_type,
            neighboring_locations=neighboring_locations
        )

        # Check cache if enabled
        if self.config.enable_caching:
            cached_result = self._get_cached(prompt)
            if cached_result is not None:
                # Ensure npcs is empty for cached results
                cached_result["npcs"] = []
                return cached_result

        # Define the generation function that will be retried on parse failures
        def _do_generate() -> dict:
            response_text = self._call_llm(prompt, generation_type="location")
            result = self._parse_location_response(response_text)
            # Override npcs with empty list (Layer 3 doesn't generate NPCs)
            result["npcs"] = []
            return result

        # Call with retry wrapper for parse/validation failures
        location_data = self._generate_with_retry(_do_generate)

        # Cache result if enabled
        if self.config.enable_caching:
            self._set_cached(prompt, location_data)

        return location_data

    def _build_location_with_context_prompt(
        self,
        world_context: "WorldContext",
        region_context: "RegionContext",
        source_location: Optional[str],
        direction: Optional[str],
        terrain_type: Optional[str] = None,
        neighboring_locations: Optional[list[dict]] = None
    ) -> str:
        """Build prompt for location generation using layered context.

        Args:
            world_context: Layer 1 context
            region_context: Layer 2 context
            source_location: Deprecated, kept for API compatibility
            direction: Deprecated, kept for API compatibility
            terrain_type: Optional terrain type for coherent generation
            neighboring_locations: Optional list of dicts with name and direction for spatial coherence

        Returns:
            Formatted prompt string using minimal template
        """
        # Format terrain type (source_location and direction no longer used)
        terrain_text = terrain_type if terrain_type else "wilderness"

        # Format neighboring locations as comma-separated "Name (direction)" or "none yet"
        if neighboring_locations:
            neighbors_text = ", ".join(
                f"{loc['name']} ({loc['direction']})" for loc in neighboring_locations
            )
        else:
            neighbors_text = "none yet"

        # Use minimal template from config
        prompt = self.config.location_prompt_minimal.format(
            theme=world_context.theme,
            theme_essence=world_context.theme_essence,
            region_name=region_context.name,
            region_theme=region_context.theme,
            terrain_type=terrain_text,
            neighboring_locations=neighbors_text
        )

        return prompt

    def generate_npcs_for_location(
        self,
        world_context: "WorldContext",
        location_name: str,
        location_description: str,
        location_category: Optional[str] = None
    ) -> list[dict]:
        """Generate NPCs for a location using layered context (Layer 4).

        This is a separate API call for NPC generation, allowing NPCs to be
        generated after the location is created.

        Args:
            world_context: Layer 1 WorldContext with theme essence, naming style, tone
            location_name: Name of the location to generate NPCs for
            location_description: Description of the location for context
            location_category: Optional category (town, dungeon, etc.)

        Returns:
            List of NPC dictionaries: [{name, description, dialogue, role}]
            Empty list if no NPCs generated or on validation failure

        Raises:
            AIGenerationError: If generation fails
            AIServiceError: If API call fails
            AITimeoutError: If request times out
        """
        # Build prompt for NPC generation
        prompt = self._build_npc_prompt(
            world_context=world_context,
            location_name=location_name,
            location_description=location_description,
            location_category=location_category
        )

        # Call LLM
        response_text = self._call_llm(prompt, generation_type="npc")

        # Parse and validate NPCs
        npcs = self._parse_npc_only_response(response_text, location_name)

        return npcs

    def _build_npc_prompt(
        self,
        world_context: "WorldContext",
        location_name: str,
        location_description: str,
        location_category: Optional[str]
    ) -> str:
        """Build prompt for NPC-only generation.

        Args:
            world_context: Layer 1 context
            location_name: Name of the location
            location_description: Description of the location
            location_category: Category of the location

        Returns:
            Formatted prompt string using NPC minimal template
        """
        prompt = self.config.npc_prompt_minimal.format(
            theme=world_context.theme,
            theme_essence=world_context.theme_essence,
            naming_style=world_context.naming_style,
            location_name=location_name,
            location_description=location_description,
            location_category=location_category or "unknown"
        )

        return prompt

    def _parse_npc_only_response(self, response_text: str, location_name: str) -> list[dict]:
        """Parse and validate LLM response for NPC-only generation.

        Args:
            response_text: Raw response text from LLM
            location_name: Name of the location (for logging)

        Returns:
            List of validated NPC dictionaries
        """
        # Extract JSON from markdown code blocks if present
        json_text = self._extract_json_from_response(response_text)

        # Try to parse JSON, attempting repair if truncated
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON
            repaired = self._repair_truncated_json(json_text)
            if repaired != json_text:
                try:
                    data = json.loads(repaired)
                except json.JSONDecodeError:
                    self._log_parse_failure(response_text, e, "npc_only")
                    return []  # Return empty list on parse failure
            else:
                self._log_parse_failure(response_text, e, "npc_only")
                return []

        # Get npcs list from response
        npcs_data = data.get("npcs", [])

        # Use existing NPC validation
        return self._parse_npcs(npcs_data, location_name)

    def generate_area_with_context(
        self,
        world_context: "WorldContext",
        region_context: "RegionContext",
        entry_direction: str,
        size: int = 5,
        terrain_type: Optional[str] = None
    ) -> list[dict]:
        """Generate an area of connected locations using layered context.

        Orchestrates Layer 3 (location) and Layer 4 (NPC) generation for
        each location in the area, ensuring coherence with world/region themes.

        Args:
            world_context: Layer 1 WorldContext with theme essence, naming style, tone
            region_context: Layer 2 RegionContext with region name, theme, danger level
            entry_direction: Direction player is coming from
            size: Target number of locations (4-7, default 5)
            terrain_type: Optional terrain type for coherent generation

        Returns:
            List of location dicts with relative_coords, name, description, category, npcs
        """
        # Clamp size to valid range
        size = max(4, min(7, size))

        # Generate area layout coordinates
        layout = self._generate_area_layout(size, entry_direction)

        # Generate each location using layered context
        area_locations = []
        for rel_coords in layout:
            # Layer 3: Generate location
            location_data = self.generate_location_with_context(
                world_context=world_context,
                region_context=region_context,
                terrain_type=terrain_type
            )

            # Layer 4: Generate NPCs for this location
            npcs = self.generate_npcs_for_location(
                world_context=world_context,
                location_name=location_data["name"],
                location_description=location_data["description"],
                location_category=location_data.get("category")
            )

            # Combine location with NPCs and coordinates
            location_data["npcs"] = npcs
            location_data["relative_coords"] = list(rel_coords)
            area_locations.append(location_data)

        return area_locations

    def _generate_area_layout(
        self,
        size: int,
        entry_direction: str,
        category: Optional[str] = None
    ) -> list[tuple[int, int]]:
        """Generate relative coordinates for area locations.

        Dispatches to category-specific layout generator.

        Args:
            size: Number of locations to generate
            entry_direction: Direction player entered from
            category: Location category for layout selection

        Returns:
            List of (x, y) coordinate tuples, with entry at (0, 0)
        """
        layout_type = (
            CATEGORY_LAYOUTS.get(category.lower(), LayoutType.BRANCHING)
            if category
            else LayoutType.BRANCHING
        )

        if layout_type == LayoutType.LINEAR:
            return self._generate_linear_layout(size, entry_direction)
        elif layout_type == LayoutType.HUB:
            return self._generate_hub_layout(size, entry_direction)
        elif layout_type == LayoutType.MAZE:
            return self._generate_maze_layout(size, entry_direction)
        else:
            return self._generate_branching_layout(size, entry_direction)

    def _generate_linear_layout(
        self, size: int, entry_direction: str
    ) -> list[tuple[int, int]]:
        """Generate linear corridor layout for caves/mines.

        Creates a straight line of rooms extending away from entry.
        Entry at (0,0), extending in opposite direction from entry.

        Args:
            size: Number of locations to generate
            entry_direction: Direction player entered from

        Returns:
            List of (x, y) coordinate tuples in a straight line
        """
        opposite_map = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (-1, 0),
            "west": (1, 0),
        }
        direction = opposite_map.get(entry_direction, (0, 1))

        coords = [(0, 0)]
        for i in range(1, size):
            coords.append((direction[0] * i, direction[1] * i))
        return coords

    def _generate_hub_layout(
        self, size: int, entry_direction: str
    ) -> list[tuple[int, int]]:
        """Generate hub layout for temples/shrines.

        Central room at (0,0) with 4 spokes in cardinal directions.
        Distributes rooms evenly across spokes, extending outward.

        Args:
            size: Number of locations to generate
            entry_direction: Direction player entered from

        Returns:
            List of (x, y) coordinate tuples with central hub and spokes
        """
        coords = [(0, 0)]  # Central hub

        if size <= 1:
            return coords

        # Four spokes: N, S, E, W
        spokes = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        rooms_per_spoke = (size - 1) // 4
        extra = (size - 1) % 4

        for i, (dx, dy) in enumerate(spokes):
            spoke_rooms = rooms_per_spoke + (1 if i < extra else 0)
            for dist in range(1, spoke_rooms + 1):
                coords.append((dx * dist, dy * dist))
                if len(coords) >= size:
                    return coords

        return coords

    def _generate_maze_layout(
        self, size: int, entry_direction: str
    ) -> list[tuple[int, int]]:
        """Generate maze layout for dungeons.

        Uses random walk with backtracking to create exploration-focused layout.
        Creates multiple branches, dead ends, and optional loops.

        Args:
            size: Number of locations to generate
            entry_direction: Direction player entered from

        Returns:
            List of (x, y) coordinate tuples forming a maze pattern
        """
        coords = [(0, 0)]
        coord_set = {(0, 0)}
        stack = [(0, 0)]  # For backtracking
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while len(coords) < size and stack:
            current = stack[-1]

            # Find unvisited neighbors
            neighbors = []
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor not in coord_set:
                    neighbors.append(neighbor)

            if neighbors:
                # Random walk to a neighbor
                next_coord = random.choice(neighbors)
                coords.append(next_coord)
                coord_set.add(next_coord)
                stack.append(next_coord)
            else:
                # Dead end - backtrack
                stack.pop()

        return coords

    def _generate_branching_layout(
        self, size: int, entry_direction: str
    ) -> list[tuple[int, int]]:
        """Generate branching layout - perpendicular branches from primary direction.

        This is the original/default layout algorithm used for forests, ruins, etc.

        Args:
            size: Number of locations to generate
            entry_direction: Direction player entered from

        Returns:
            List of (x, y) coordinate tuples in a branching pattern
        """
        # Start with entry point at origin
        coords = [(0, 0)]

        # Define expansion directions (prioritize away from entry)
        opposite_map = {
            "north": (0, 1),   # Expand north (away from player coming from south)
            "south": (0, -1),  # Expand south
            "east": (1, 0),    # Expand east
            "west": (-1, 0),   # Expand west
        }
        primary_dir = opposite_map.get(entry_direction, (0, 1))

        # Add locations in a branching pattern
        current_x, current_y = 0, 0
        while len(coords) < size:
            # First, extend in primary direction
            if len(coords) < 2:
                current_x += primary_dir[0]
                current_y += primary_dir[1]
                coords.append((current_x, current_y))
            else:
                # Branch out perpendicular to primary
                if primary_dir[0] == 0:  # Primary is vertical
                    # Branch east and west
                    if len(coords) % 2 == 0:
                        new_coord = (coords[-1][0] + 1, coords[-1][1])
                    else:
                        new_coord = (coords[-1][0] - 1, coords[-1][1])
                else:  # Primary is horizontal
                    # Branch north and south
                    if len(coords) % 2 == 0:
                        new_coord = (coords[-1][0], coords[-1][1] + 1)
                    else:
                        new_coord = (coords[-1][0], coords[-1][1] - 1)

                # Avoid duplicates
                if new_coord not in coords:
                    coords.append(new_coord)
                else:
                    # Continue in primary direction from last point
                    current_x = coords[-1][0] + primary_dir[0]
                    current_y = coords[-1][1] + primary_dir[1]
                    if (current_x, current_y) not in coords:
                        coords.append((current_x, current_y))
                    else:
                        # Fallback: find any adjacent empty spot
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            new_x = coords[-1][0] + dx
                            new_y = coords[-1][1] + dy
                            if (new_x, new_y) not in coords:
                                coords.append((new_x, new_y))
                                break

        return coords

    def _generate_secret_passage(
        self,
        coords: list[tuple[int, int]],
        probability: float = 0.15
    ) -> Optional[dict]:
        """Potentially generate a secret passage connecting non-adjacent rooms.

        Args:
            coords: List of room coordinates
            probability: Chance to generate a passage (0.0 to 1.0)

        Returns:
            Dict with from_coord, to_coord, is_secret_passage or None
        """
        if random.random() > probability or len(coords) < 3:
            return None

        # Find pairs of non-adjacent coords (Manhattan distance >= 2)
        valid_pairs = []
        for i, c1 in enumerate(coords):
            for c2 in coords[i + 1:]:
                dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                if dist >= 2:
                    valid_pairs.append((c1, c2))

        if not valid_pairs:
            return None

        from_coord, to_coord = random.choice(valid_pairs)
        return {
            "from_coord": from_coord,
            "to_coord": to_coord,
            "is_secret_passage": True,
        }

    def _generate_area_layout_3d(
        self,
        size: int,
        entry_direction: str,
        category: Optional[str] = None
    ) -> list[tuple[int, int, int]]:
        """Generate 3D coordinates for multi-level areas.

        For categories with z-depth (dungeon, cave, ruins), generates
        coords descending from z=0 to min_z with stairs connecting levels.

        Args:
            size: Number of locations to generate
            entry_direction: Direction player entered from
            category: Location category (dungeon, cave, etc.)

        Returns:
            List of (x, y, z) coordinate tuples
        """
        from cli_rpg.world_grid import get_subgrid_bounds

        # Get z bounds from category
        bounds = get_subgrid_bounds(category)
        min_z = bounds[4]
        max_z = bounds[5]

        # If single-level (min_z == max_z == 0), use 2D layout with z=0
        if min_z == max_z == 0:
            coords_2d = self._generate_area_layout(size, entry_direction, category)
            return [(x, y, 0) for x, y in coords_2d]

        # Multi-level layout
        # Start with entry point at origin (0, 0, 0)
        coords: list[tuple[int, int, int]] = [(0, 0, 0)]

        # Define expansion directions (prioritize away from entry)
        opposite_map = {
            "north": (0, 1),   # Expand north
            "south": (0, -1),  # Expand south
            "east": (1, 0),    # Expand east
            "west": (-1, 0),   # Expand west
        }
        primary_dir = opposite_map.get(entry_direction, (0, 1))

        # Calculate z-levels to use
        # For dungeons (min_z < 0), we descend: 0, -1, -2, ...
        # For towers (max_z > 0), we ascend: 0, 1, 2, ...
        if min_z < 0:
            z_levels = list(range(0, min_z - 1, -1))  # [0, -1, -2]
        else:
            z_levels = list(range(0, max_z + 1))  # [0, 1, 2, 3]

        # Distribute locations across z-levels
        # Aim for roughly equal distribution with stairs connecting levels
        current_z = 0
        current_x, current_y = 0, 0
        level_count = {z: 0 for z in z_levels}
        level_count[0] = 1  # Entry already at z=0

        # Target locations per level (roughly equal)
        locs_per_level = max(1, size // len(z_levels))

        # Generate locations
        while len(coords) < size:
            # Check if we should descend/ascend to next level
            if level_count[current_z] >= locs_per_level and len(z_levels) > 1:
                # Find next z-level to explore
                z_idx = z_levels.index(current_z)
                if z_idx < len(z_levels) - 1:
                    next_z = z_levels[z_idx + 1]
                    # Add stair location at shared (x, y) but new z
                    stair_coord = (current_x, current_y, next_z)
                    if stair_coord not in coords:
                        coords.append(stair_coord)
                        level_count[next_z] = level_count.get(next_z, 0) + 1
                        current_z = next_z
                        if len(coords) >= size:
                            break
                        continue

            # Extend in primary direction on current level
            if level_count[current_z] < 2:
                new_x = current_x + primary_dir[0]
                new_y = current_y + primary_dir[1]
                new_coord = (new_x, new_y, current_z)
                if new_coord not in coords:
                    coords.append(new_coord)
                    level_count[current_z] += 1
                    current_x, current_y = new_x, new_y
                    continue

            # Branch perpendicular to primary on current level
            if primary_dir[0] == 0:  # Primary is vertical
                if level_count[current_z] % 2 == 0:
                    new_coord = (current_x + 1, current_y, current_z)
                else:
                    new_coord = (current_x - 1, current_y, current_z)
            else:  # Primary is horizontal
                if level_count[current_z] % 2 == 0:
                    new_coord = (current_x, current_y + 1, current_z)
                else:
                    new_coord = (current_x, current_y - 1, current_z)

            if new_coord not in coords:
                coords.append(new_coord)
                level_count[current_z] += 1
                current_x, current_y = new_coord[0], new_coord[1]
            else:
                # Find any adjacent empty spot on current level
                found = False
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_coord = (current_x + dx, current_y + dy, current_z)
                    if new_coord not in coords:
                        coords.append(new_coord)
                        level_count[current_z] += 1
                        current_x, current_y = new_coord[0], new_coord[1]
                        found = True
                        break

                if not found:
                    # Move to next z-level if stuck
                    z_idx = z_levels.index(current_z)
                    if z_idx < len(z_levels) - 1:
                        next_z = z_levels[z_idx + 1]
                        stair_coord = (current_x, current_y, next_z)
                        if stair_coord not in coords:
                            coords.append(stair_coord)
                            level_count[next_z] = level_count.get(next_z, 0) + 1
                            current_z = next_z
                    else:
                        # Can't expand further, break to avoid infinite loop
                        break

        return coords
