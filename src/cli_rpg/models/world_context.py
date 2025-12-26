"""WorldContext model for caching world theme information.

WorldContext stores theme information generated once at world creation,
enabling consistent AI-generated content by providing theme essence,
naming conventions, and tone to all subsequent generation calls.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# Default values for fallback context when AI is unavailable
DEFAULT_THEME_ESSENCES = {
    "fantasy": "classic high fantasy with magic and mythical creatures",
    "cyberpunk": "neon-lit dystopia with corporate warfare and technology",
    "steampunk": "Victorian-era adventure with brass and clockwork",
    "horror": "dark supernatural horror with creeping dread",
    "post-apocalyptic": "wasteland survival in a broken world",
}

DEFAULT_NAMING_STYLES = {
    "fantasy": "Old English with Celtic influence",
    "cyberpunk": "Japanese-English hybrid with tech jargon",
    "steampunk": "British Victorian with mechanical terms",
    "horror": "archaic, unsettling names with dark undertones",
    "post-apocalyptic": "rough, abbreviated survivor names",
}

DEFAULT_TONES = {
    "fantasy": "heroic, adventurous with moments of wonder",
    "cyberpunk": "noir, cynical, morally ambiguous",
    "steampunk": "adventurous, optimistic, inventive",
    "horror": "tense, atmospheric, psychologically unsettling",
    "post-apocalyptic": "desperate, gritty, with flickers of hope",
}


@dataclass
class WorldContext:
    """Stores cached world theme information for consistent AI generation.

    Attributes:
        theme: Base theme keyword (e.g., "fantasy", "cyberpunk")
        theme_essence: AI-generated theme summary describing the world's character
        naming_style: How to name locations/NPCs (e.g., "Old English with Norse influence")
        tone: Narrative tone (e.g., "gritty, morally ambiguous")
        generated_at: When context was generated (None if not AI-generated)
    """

    theme: str
    theme_essence: str = ""
    naming_style: str = ""
    tone: str = ""
    generated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize WorldContext to dictionary for save/load.

        Returns:
            Dictionary containing all context attributes with datetime as ISO string.
        """
        return {
            "theme": self.theme,
            "theme_essence": self.theme_essence,
            "naming_style": self.naming_style,
            "tone": self.tone,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldContext":
        """Deserialize WorldContext from dictionary.

        Args:
            data: Dictionary containing context attributes

        Returns:
            WorldContext instance with restored data
        """
        generated_at = None
        if data.get("generated_at"):
            generated_at = datetime.fromisoformat(data["generated_at"])

        return cls(
            theme=data["theme"],
            theme_essence=data.get("theme_essence", ""),
            naming_style=data.get("naming_style", ""),
            tone=data.get("tone", ""),
            generated_at=generated_at,
        )

    @classmethod
    def default(cls, theme: str = "fantasy") -> "WorldContext":
        """Create a default WorldContext when AI generation is unavailable.

        Args:
            theme: Base theme keyword (defaults to "fantasy")

        Returns:
            WorldContext with sensible defaults for the given theme
        """
        return cls(
            theme=theme,
            theme_essence=DEFAULT_THEME_ESSENCES.get(
                theme, DEFAULT_THEME_ESSENCES["fantasy"]
            ),
            naming_style=DEFAULT_NAMING_STYLES.get(
                theme, DEFAULT_NAMING_STYLES["fantasy"]
            ),
            tone=DEFAULT_TONES.get(theme, DEFAULT_TONES["fantasy"]),
            generated_at=None,
        )
