"""Configuration loading utilities."""

import logging
from typing import Optional
from cli_rpg.ai_config import AIConfig, AIConfigError


logger = logging.getLogger(__name__)


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
