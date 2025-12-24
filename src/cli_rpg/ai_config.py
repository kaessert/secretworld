"""Configuration module for AI services."""

import os
from dataclasses import dataclass, field
from typing import Optional


class AIConfigError(Exception):
    """Exception raised for AI configuration errors."""
    pass


# Default prompt template for location generation
DEFAULT_LOCATION_PROMPT = """You are a creative game world designer. Generate a new location for a {theme} RPG game.

Context:
- World Theme: {theme}
- Existing Locations: {context_locations}
- Expanding from: {source_location}
- Direction: {direction}

Requirements:
1. Create a unique location name (2-50 characters)
2. Write a vivid description (1-500 characters)
3. Suggest 1-4 connections to other locations using valid directions: north, south, east, west, up, down
4. If expanding from a location, include a connection back to {source_location} via the opposite direction
5. Ensure the location fits the {theme} theme
6. Make the location interesting and explorable

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Location Name",
  "description": "A detailed description of the location.",
  "connections": {{
    "direction": "location_name"
  }}
}}"""


@dataclass
class AIConfig:
    """Configuration for AI services.
    
    Attributes:
        api_key: API key for the LLM provider (required)
        model: Model identifier (default: "gpt-3.5-turbo")
        temperature: Generation randomness 0.0-2.0 (default: 0.7)
        max_tokens: Maximum response length (default: 500)
        max_retries: Retry attempts for API failures (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)
        enable_caching: Enable response caching (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 3600)
        location_generation_prompt: Prompt template for location generation
    """
    
    api_key: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_caching: bool = True
    cache_ttl: int = 3600
    location_generation_prompt: str = field(default=DEFAULT_LOCATION_PROMPT)
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate API key
        if not self.api_key or not self.api_key.strip():
            raise AIConfigError("API key cannot be empty")
        
        # Validate temperature
        if not (0.0 <= self.temperature <= 2.0):
            raise AIConfigError("Temperature must be between 0.0 and 2.0")
        
        # Validate max_tokens
        if self.max_tokens <= 0:
            raise AIConfigError("max_tokens must be positive")
        
        # Validate max_retries
        if self.max_retries < 0:
            raise AIConfigError("max_retries must be non-negative")
        
        # Validate retry_delay
        if self.retry_delay <= 0:
            raise AIConfigError("retry_delay must be positive")
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """Create AIConfig from environment variables.
        
        Environment variables:
            OPENAI_API_KEY: API key (required)
            AI_MODEL: Model identifier
            AI_TEMPERATURE: Temperature value
            AI_MAX_TOKENS: Maximum tokens
            AI_MAX_RETRIES: Maximum retry attempts
            AI_RETRY_DELAY: Retry delay in seconds
            AI_ENABLE_CACHING: Enable caching (true/false)
            AI_CACHE_TTL: Cache TTL in seconds
        
        Returns:
            AIConfig instance
        
        Raises:
            AIConfigError: If OPENAI_API_KEY is not set
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIConfigError("OPENAI_API_KEY environment variable not set")
        
        # Read optional environment variables with defaults
        model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("AI_MAX_TOKENS", "500"))
        max_retries = int(os.getenv("AI_MAX_RETRIES", "3"))
        retry_delay = float(os.getenv("AI_RETRY_DELAY", "1.0"))
        enable_caching = os.getenv("AI_ENABLE_CACHING", "true").lower() == "true"
        cache_ttl = int(os.getenv("AI_CACHE_TTL", "3600"))
        
        return cls(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_delay=retry_delay,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl
        )
    
    def to_dict(self) -> dict:
        """Serialize configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "location_generation_prompt": self.location_generation_prompt
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AIConfig":
        """Create AIConfig from dictionary.
        
        Args:
            data: Dictionary containing configuration data
        
        Returns:
            AIConfig instance
        
        Raises:
            AIConfigError: If validation fails
        """
        return cls(
            api_key=data["api_key"],
            model=data.get("model", "gpt-3.5-turbo"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 500),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
            enable_caching=data.get("enable_caching", True),
            cache_ttl=data.get("cache_ttl", 3600),
            location_generation_prompt=data.get("location_generation_prompt", DEFAULT_LOCATION_PROMPT)
        )
