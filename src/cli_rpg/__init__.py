"""CLI RPG - An AI-generated role-playing game."""

import logging

# Add NullHandler to silence log output by default per Python logging best practices.
# This prevents WARNING+ messages from leaking to stderr via Python's "last resort" handler.
# Applications that want logging can configure their own handlers.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"

from cli_rpg.models.character import Character

__all__ = ["Character", "__version__"]
