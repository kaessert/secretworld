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

from cli_rpg.ai_config import AIConfig
from cli_rpg.models.location import Location


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
        
        for direction in connections.keys():
            if direction not in Location.VALID_DIRECTIONS:
                raise AIGenerationError(
                    f"Invalid direction '{direction}'. Must be one of: "
                    f"{', '.join(sorted(Location.VALID_DIRECTIONS))}"
                )
        
        # Return validated data
        return {
            "name": name,
            "description": description,
            "connections": connections
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
