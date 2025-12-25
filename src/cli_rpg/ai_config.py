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


# Default prompt template for enemy generation
DEFAULT_ENEMY_GENERATION_PROMPT = """Generate an enemy for a {theme} RPG.
Location: {location_name}
Player Level: {player_level}

Requirements:
1. Create a unique enemy name (2-30 characters) that fits the theme and location
2. Write a vivid description (10-150 characters) of the enemy's appearance
3. Create attack flavor text (10-100 characters) describing how it attacks
4. Generate balanced stats scaled to the player level

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Enemy Name",
  "description": "A brief description of the enemy's appearance.",
  "attack_flavor": "describes the attack action",
  "health": <number>,
  "attack_power": <number>,
  "defense": <number>,
  "xp_reward": <number>
}}

Stats scaling guidelines (based on player level {player_level}):
- health: 20 + (player_level * 10) with some variance
- attack_power: 3 + (player_level * 2) with some variance
- defense: 1 + player_level with some variance
- xp_reward: 20 + (player_level * 10) with some variance"""


# Default prompt template for item generation
DEFAULT_ITEM_GENERATION_PROMPT = """Generate an item for a {theme} RPG.
Location: {location_name}
Player Level: {player_level}
Item Type Hint: {item_type_hint}

Requirements:
1. Create a unique item name (2-30 characters) that fits the theme and location
2. Write a description (1-200 characters) of the item
3. Set appropriate stats based on item type and player level
4. Suggest a fair price for the item

Item types: weapon, armor, consumable, misc
- Weapons should have damage_bonus (scaled to level)
- Armor should have defense_bonus (scaled to level)
- Consumables should have heal_amount (scaled to level)
- Misc items have no stat bonuses

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Item Name",
  "description": "A brief description of the item.",
  "item_type": "weapon|armor|consumable|misc",
  "damage_bonus": <number>,
  "defense_bonus": <number>,
  "heal_amount": <number>,
  "suggested_price": <number>
}}

Stats scaling guidelines (based on player level {player_level}):
- damage_bonus: 2 + (player_level * 1) for weapons
- defense_bonus: 1 + (player_level * 1) for armor
- heal_amount: 10 + (player_level * 5) for consumables
- suggested_price: 20 + (player_level * 15) with variance"""


# Default prompt template for NPC dialogue generation
DEFAULT_NPC_DIALOGUE_PROMPT = """Generate a single conversational greeting for an NPC in a {theme} RPG.

NPC: {npc_name}
Description: {npc_description}
Role: {npc_role}
Location: {location_name}

Write 1-2 sentences that:
- Match the {theme} setting
- Reflect the NPC's personality and role
- Sound natural and immersive

Respond with ONLY the dialogue text, no quotes or formatting."""


# Default prompt template for lore generation
DEFAULT_LORE_GENERATION_PROMPT = """Generate a {lore_category} snippet for a {theme} RPG world.

Location context: {location_name}

Write a 50-500 character piece of world lore that:
- Fits the {theme} setting
- Is appropriate for the location context (if provided)
- Provides immersive world-building content
- Could be a {lore_category} about the world's past, legends, or secrets

Types of lore:
- history: Past events, fallen kingdoms, ancient wars, founding stories
- legend: Myths, prophecies, tales of heroes or monsters
- secret: Hidden knowledge, forbidden lore, mysterious occurrences

Respond with ONLY the lore text, no quotes or formatting."""


# Default prompt template for quest generation
DEFAULT_QUEST_GENERATION_PROMPT = """Generate a quest for a {theme} RPG.
NPC Quest Giver: {npc_name}
Location: {location_name}
Player Level: {player_level}

Requirements:
1. Create a unique quest name (2-30 characters)
2. Write a quest description (1-200 characters)
3. Choose an appropriate objective type
4. Set target and target_count for the objective
5. Calculate balanced rewards for the player level

Objective types:
- kill: Defeat enemy type (target = enemy name, target_count = how many)
- collect: Gather items (target = item name, target_count = how many)
- explore: Visit location (target = location name, target_count = 1)
- talk: Speak to NPC (target = NPC name, target_count = 1)
- drop: Deliver item (target = item name, target_count = 1)

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Quest Name",
  "description": "A brief description of the quest objective.",
  "objective_type": "kill|collect|explore|talk|drop",
  "target": "target name",
  "target_count": <number>,
  "gold_reward": <number>,
  "xp_reward": <number>
}}

Rewards scaling guidelines (based on player level {player_level}):
- gold_reward: 30 + (player_level * 15) with some variance
- xp_reward: 25 + (player_level * 12) with some variance"""


@dataclass
class AIConfig:
    """Configuration for AI services.

    Attributes:
        api_key: API key for the LLM provider (required)
        provider: AI provider - "openai" or "anthropic" (default: "openai")
        model: Model identifier (default: "gpt-3.5-turbo" for openai, "claude-3-5-sonnet-latest" for anthropic)
        temperature: Generation randomness 0.0-2.0 (default: 0.7)
        max_tokens: Maximum response length (default: 500)
        max_retries: Retry attempts for API failures (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)
        enable_caching: Enable response caching (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 3600)
        cache_file: Path to persistent cache file (default: ~/.cli_rpg/cache/ai_cache.json when caching enabled)
        location_generation_prompt: Prompt template for location generation
    """

    api_key: str
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 500
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_caching: bool = True
    cache_ttl: int = 3600
    cache_file: Optional[str] = None
    location_generation_prompt: str = field(default=DEFAULT_LOCATION_PROMPT)
    npc_dialogue_prompt: str = field(default=DEFAULT_NPC_DIALOGUE_PROMPT)
    enemy_generation_prompt: str = field(default=DEFAULT_ENEMY_GENERATION_PROMPT)
    item_generation_prompt: str = field(default=DEFAULT_ITEM_GENERATION_PROMPT)
    lore_generation_prompt: str = field(default=DEFAULT_LORE_GENERATION_PROMPT)
    quest_generation_prompt: str = field(default=DEFAULT_QUEST_GENERATION_PROMPT)
    
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

        # Set default cache_file when caching is enabled and no explicit path provided
        if self.enable_caching and self.cache_file is None:
            self.cache_file = os.path.expanduser("~/.cli_rpg/cache/ai_cache.json")
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """Create AIConfig from environment variables.

        Environment variables:
            OPENAI_API_KEY: OpenAI API key
            ANTHROPIC_API_KEY: Anthropic API key
            AI_PROVIDER: Explicit provider selection ("openai" or "anthropic")
            AI_MODEL: Model identifier
            AI_TEMPERATURE: Temperature value
            AI_MAX_TOKENS: Maximum tokens
            AI_MAX_RETRIES: Maximum retry attempts
            AI_RETRY_DELAY: Retry delay in seconds
            AI_ENABLE_CACHING: Enable caching (true/false)
            AI_CACHE_TTL: Cache TTL in seconds

        Provider selection priority:
        1. If AI_PROVIDER is set, use that provider (must have corresponding API key)
        2. If both keys are set, prefer Anthropic
        3. Use whichever key is available

        Returns:
            AIConfig instance

        Raises:
            AIConfigError: If no API key is available
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        explicit_provider = os.getenv("AI_PROVIDER", "").lower()

        # Determine provider and API key
        if explicit_provider:
            # Explicit provider selection
            if explicit_provider == "anthropic":
                if not anthropic_key:
                    raise AIConfigError("AI_PROVIDER=anthropic but ANTHROPIC_API_KEY not set")
                provider = "anthropic"
                api_key = anthropic_key
            elif explicit_provider == "openai":
                if not openai_key:
                    raise AIConfigError("AI_PROVIDER=openai but OPENAI_API_KEY not set")
                provider = "openai"
                api_key = openai_key
            else:
                raise AIConfigError(f"Invalid AI_PROVIDER: {explicit_provider}. Must be 'openai' or 'anthropic'")
        elif anthropic_key:
            # Prefer Anthropic when both keys are available
            provider = "anthropic"
            api_key = anthropic_key
        elif openai_key:
            provider = "openai"
            api_key = openai_key
        else:
            raise AIConfigError("No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

        # Set default model based on provider
        default_model = "claude-3-5-sonnet-latest" if provider == "anthropic" else "gpt-3.5-turbo"

        # Read optional environment variables with defaults
        model = os.getenv("AI_MODEL", default_model)
        temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("AI_MAX_TOKENS", "500"))
        max_retries = int(os.getenv("AI_MAX_RETRIES", "3"))
        retry_delay = float(os.getenv("AI_RETRY_DELAY", "1.0"))
        enable_caching = os.getenv("AI_ENABLE_CACHING", "true").lower() == "true"
        cache_ttl = int(os.getenv("AI_CACHE_TTL", "3600"))
        cache_file = os.getenv("AI_CACHE_FILE")  # None if not set, __post_init__ will set default

        return cls(
            api_key=api_key,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            retry_delay=retry_delay,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl,
            cache_file=cache_file
        )
    
    def to_dict(self) -> dict:
        """Serialize configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "api_key": self.api_key,
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "cache_file": self.cache_file,
            "location_generation_prompt": self.location_generation_prompt,
            "npc_dialogue_prompt": self.npc_dialogue_prompt,
            "enemy_generation_prompt": self.enemy_generation_prompt,
            "item_generation_prompt": self.item_generation_prompt,
            "lore_generation_prompt": self.lore_generation_prompt,
            "quest_generation_prompt": self.quest_generation_prompt
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
            provider=data.get("provider", "openai"),
            model=data.get("model", "gpt-3.5-turbo"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 500),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
            enable_caching=data.get("enable_caching", True),
            cache_ttl=data.get("cache_ttl", 3600),
            cache_file=data.get("cache_file"),
            location_generation_prompt=data.get("location_generation_prompt", DEFAULT_LOCATION_PROMPT),
            npc_dialogue_prompt=data.get("npc_dialogue_prompt", DEFAULT_NPC_DIALOGUE_PROMPT),
            enemy_generation_prompt=data.get("enemy_generation_prompt", DEFAULT_ENEMY_GENERATION_PROMPT),
            item_generation_prompt=data.get("item_generation_prompt", DEFAULT_ITEM_GENERATION_PROMPT),
            lore_generation_prompt=data.get("lore_generation_prompt", DEFAULT_LORE_GENERATION_PROMPT),
            quest_generation_prompt=data.get("quest_generation_prompt", DEFAULT_QUEST_GENERATION_PROMPT)
        )
