"""Configuration loading utilities."""

import logging
import os
from typing import Optional
from cli_rpg.ai_config import AIConfig, AIConfigError


logger = logging.getLogger(__name__)


def is_ai_strict_mode() -> bool:
    """Check if AI strict mode is enabled.

    In strict mode, AI generation failures will raise exceptions instead of
    silently falling back to the default world.

    Returns:
        True if strict mode is enabled (default), False only if
        CLI_RPG_REQUIRE_AI environment variable is explicitly set to "false"
    """
    env_value = os.environ.get('CLI_RPG_REQUIRE_AI', 'true')
    return env_value.lower() != 'false'


def load_ai_config() -> Optional[AIConfig]:
    """Load AI configuration from environment variables.
    
    Returns:
        AIConfig instance if OPENAI_API_KEY is set, None otherwise
    """
    try:
        config = AIConfig.from_env()
        logger.info("AI configuration loaded successfully")
        return config
    except AIConfigError as e:
        logger.info(f"AI configuration not available: {e}")
        return None
