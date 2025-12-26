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
3. Suggest 1-4 connections to other locations using valid directions: north, south, east, west
4. If expanding from a location, include a connection back to {source_location} via the opposite direction
5. Ensure the location fits the {theme} theme
6. Make the location interesting and explorable
7. Include a category for the location type (one of: town, dungeon, wilderness, settlement, ruins, cave, forest, mountain, village)
8. Generate 0-2 NPCs appropriate for this location (optional)
   - Each NPC needs: name (2-30 chars), description (1-200 chars), dialogue (a greeting), role (villager, merchant, or quest_giver)

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Location Name",
  "description": "A detailed description of the location.",
  "connections": {{
    "direction": "location_name"
  }},
  "category": "wilderness",
  "npcs": [
    {{
      "name": "NPC Name",
      "description": "Brief description of the NPC.",
      "dialogue": "What the NPC says when greeted.",
      "role": "villager"
    }}
  ]
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

IMPORTANT for KILL quests - use ONLY these enemy types as targets:
- Wolf, Bear, Wild Boar, Giant Spider (for forest/wilderness)
- Bat, Goblin, Troll, Cave Dweller (for caves)
- Skeleton, Zombie, Ghost, Dark Knight (for dungeons/ruins)
- Eagle, Goat, Mountain Lion, Yeti (for mountains)
- Bandit, Thief, Ruffian, Outlaw (for towns/villages)

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


# Default prompt template for ASCII art generation (enemies)
DEFAULT_ASCII_ART_GENERATION_PROMPT = """Generate ASCII art for a {theme} RPG enemy.

Enemy Name: {enemy_name}
Description: {enemy_description}

Requirements:
1. Create ASCII art that is 5-8 lines tall
2. Maximum 40 characters wide per line
3. Use only ASCII characters (letters, numbers, symbols)
4. Make it visually represent the enemy's appearance
5. Keep it simple but recognizable

Respond with ONLY the ASCII art, no explanation or formatting."""


# Default prompt template for location ASCII art generation
DEFAULT_LOCATION_ASCII_ART_PROMPT = """Generate ASCII art for a {theme} RPG location.

Location Name: {location_name}
Category: {location_category}
Description: {location_description}

Requirements:
1. Create ASCII art that is 6-10 lines tall
2. Maximum 50 characters wide per line
3. Use only ASCII characters (letters, numbers, symbols)
4. Represent the location's key visual features
5. Keep it simple but atmospheric

Respond with ONLY the ASCII art, no explanation or formatting."""


# Default prompt template for NPC ASCII art generation
DEFAULT_NPC_ASCII_ART_PROMPT = """Generate ASCII art for a {theme} RPG character.

NPC Name: {npc_name}
Role: {npc_role}
Description: {npc_description}

Requirements:
1. Create ASCII art that is 5-7 lines tall
2. Maximum 40 characters wide per line
3. Use only ASCII characters (letters, numbers, symbols)
4. Make it visually represent the character's appearance and role
5. Keep it simple but recognizable

Respond with ONLY the ASCII art, no explanation or formatting."""


# Default prompt template for whisper generation
DEFAULT_WHISPER_GENERATION_PROMPT = """Generate a single atmospheric whisper for a {theme} RPG.

Location Category: {location_category}

Requirements:
1. Write exactly ONE short, evocative sentence (10-100 characters)
2. The whisper should hint at hidden secrets, atmosphere, or subtle danger
3. Match the {theme} setting and {location_category} location type
4. Be atmospheric and mysterious, not direct or obvious
5. Use second person perspective is optional

Respond with ONLY the whisper text, no quotes or formatting."""


# Default prompt template for dream generation
DEFAULT_DREAM_GENERATION_PROMPT = """Generate a short, atmospheric dream sequence for a {theme} RPG.

Context:
- Location: {location_name}
- Dread Level: {dread}% (psychological horror meter, 0=calm, 100=terrified)
- Recent Player Choices: {choices_summary}
- Dream Type: {dream_type}

Requirements:
1. Write a single, evocative dream fragment (20-300 characters)
2. Use second person ("You dream..." or "You see...")
3. Match the {theme} setting and atmosphere
4. If nightmare (dread 50%+), make it unsettling but not gratuitously violent
5. Reference player choices if relevant (fleeing = chase dreams, killing = haunted dreams)
6. Keep it surreal and dreamlike, not literal

Respond with ONLY the dream text, no quotes or formatting."""


# Default prompt template for NPC conversation responses
DEFAULT_NPC_CONVERSATION_PROMPT = """You are roleplaying as {npc_name} in a {theme} RPG.

Character Information:
- Name: {npc_name}
- Description: {npc_description}
- Role: {npc_role}
- Location: {location_name}

Conversation History:
{conversation_history}

Player says: "{player_input}"

Instructions:
- Respond in-character as {npc_name}
- Keep your response to 1-2 sentences (10-200 characters)
- Stay consistent with your role and the {theme} setting
- Reference the conversation history if relevant

Respond with ONLY the dialogue text, no quotes or formatting."""


@dataclass
class AIConfig:
    """Configuration for AI services.

    Attributes:
        api_key: API key for the LLM provider (required)
        provider: AI provider - "openai", "anthropic", or "ollama" (default: "openai")
        model: Model identifier (default: "gpt-3.5-turbo" for openai, "claude-3-5-sonnet-latest" for anthropic, "llama3.2" for ollama)
        temperature: Generation randomness 0.0-2.0 (default: 0.7)
        max_tokens: Maximum response length (default: 2000)
        max_retries: Retry attempts for API failures (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)
        enable_caching: Enable response caching (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 3600)
        cache_file: Path to persistent cache file (default: ~/.cli_rpg/cache/ai_cache.json when caching enabled)
        ollama_base_url: Base URL for Ollama API (default: http://localhost:11434/v1)
        location_generation_prompt: Prompt template for location generation
    """

    api_key: str
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_caching: bool = True
    cache_ttl: int = 3600
    cache_file: Optional[str] = None
    ollama_base_url: Optional[str] = None
    location_generation_prompt: str = field(default=DEFAULT_LOCATION_PROMPT)
    npc_dialogue_prompt: str = field(default=DEFAULT_NPC_DIALOGUE_PROMPT)
    enemy_generation_prompt: str = field(default=DEFAULT_ENEMY_GENERATION_PROMPT)
    item_generation_prompt: str = field(default=DEFAULT_ITEM_GENERATION_PROMPT)
    lore_generation_prompt: str = field(default=DEFAULT_LORE_GENERATION_PROMPT)
    quest_generation_prompt: str = field(default=DEFAULT_QUEST_GENERATION_PROMPT)
    npc_conversation_prompt: str = field(default=DEFAULT_NPC_CONVERSATION_PROMPT)
    ascii_art_generation_prompt: str = field(default=DEFAULT_ASCII_ART_GENERATION_PROMPT)
    location_ascii_art_generation_prompt: str = field(default=DEFAULT_LOCATION_ASCII_ART_PROMPT)
    npc_ascii_art_generation_prompt: str = field(default=DEFAULT_NPC_ASCII_ART_PROMPT)
    dream_generation_prompt: str = field(default=DEFAULT_DREAM_GENERATION_PROMPT)
    whisper_generation_prompt: str = field(default=DEFAULT_WHISPER_GENERATION_PROMPT)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate API key (allow placeholder for Ollama provider)
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
        ollama_base_url = None
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
            elif explicit_provider == "ollama":
                # Ollama runs locally, no API key required
                provider = "ollama"
                api_key = "ollama"  # Placeholder for OpenAI client
                ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            else:
                raise AIConfigError(f"Invalid AI_PROVIDER: {explicit_provider}. Must be 'openai', 'anthropic', or 'ollama'")
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
        if provider == "anthropic":
            default_model = "claude-3-5-sonnet-latest"
        elif provider == "ollama":
            # Check for OLLAMA_MODEL first, then AI_MODEL, then default
            default_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        else:
            default_model = "gpt-3.5-turbo"

        # Read optional environment variables with defaults
        # For Ollama, OLLAMA_MODEL takes precedence over AI_MODEL
        if provider == "ollama":
            model = os.getenv("OLLAMA_MODEL", os.getenv("AI_MODEL", default_model))
        else:
            model = os.getenv("AI_MODEL", default_model)
        temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("AI_MAX_TOKENS", "2000"))
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
            cache_file=cache_file,
            ollama_base_url=ollama_base_url
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
            "ollama_base_url": self.ollama_base_url,
            "location_generation_prompt": self.location_generation_prompt,
            "npc_dialogue_prompt": self.npc_dialogue_prompt,
            "enemy_generation_prompt": self.enemy_generation_prompt,
            "item_generation_prompt": self.item_generation_prompt,
            "lore_generation_prompt": self.lore_generation_prompt,
            "quest_generation_prompt": self.quest_generation_prompt,
            "npc_conversation_prompt": self.npc_conversation_prompt,
            "ascii_art_generation_prompt": self.ascii_art_generation_prompt,
            "location_ascii_art_generation_prompt": self.location_ascii_art_generation_prompt,
            "npc_ascii_art_generation_prompt": self.npc_ascii_art_generation_prompt,
            "dream_generation_prompt": self.dream_generation_prompt,
            "whisper_generation_prompt": self.whisper_generation_prompt,
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
            max_tokens=data.get("max_tokens", 2000),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
            enable_caching=data.get("enable_caching", True),
            cache_ttl=data.get("cache_ttl", 3600),
            cache_file=data.get("cache_file"),
            ollama_base_url=data.get("ollama_base_url"),
            location_generation_prompt=data.get("location_generation_prompt", DEFAULT_LOCATION_PROMPT),
            npc_dialogue_prompt=data.get("npc_dialogue_prompt", DEFAULT_NPC_DIALOGUE_PROMPT),
            enemy_generation_prompt=data.get("enemy_generation_prompt", DEFAULT_ENEMY_GENERATION_PROMPT),
            item_generation_prompt=data.get("item_generation_prompt", DEFAULT_ITEM_GENERATION_PROMPT),
            lore_generation_prompt=data.get("lore_generation_prompt", DEFAULT_LORE_GENERATION_PROMPT),
            quest_generation_prompt=data.get("quest_generation_prompt", DEFAULT_QUEST_GENERATION_PROMPT),
            npc_conversation_prompt=data.get("npc_conversation_prompt", DEFAULT_NPC_CONVERSATION_PROMPT),
            ascii_art_generation_prompt=data.get(
                "ascii_art_generation_prompt", DEFAULT_ASCII_ART_GENERATION_PROMPT
            ),
            location_ascii_art_generation_prompt=data.get(
                "location_ascii_art_generation_prompt", DEFAULT_LOCATION_ASCII_ART_PROMPT
            ),
            npc_ascii_art_generation_prompt=data.get(
                "npc_ascii_art_generation_prompt", DEFAULT_NPC_ASCII_ART_PROMPT
            ),
            dream_generation_prompt=data.get(
                "dream_generation_prompt", DEFAULT_DREAM_GENERATION_PROMPT
            ),
            whisper_generation_prompt=data.get(
                "whisper_generation_prompt", DEFAULT_WHISPER_GENERATION_PROMPT
            ),
        )
