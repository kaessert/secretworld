"""RegionContext model for caching region theme information.

RegionContext stores region-level theme information (Layer 2 in the hierarchy)
for consistent AI-generated content within a geographic area. This sits between
WorldContext (Layer 1) and Location (Layer 3) in the layered query architecture.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# Default values for fallback context when AI is unavailable
DEFAULT_REGION_THEMES = {
    "wilderness": "untamed nature, ancient forests, hidden paths",
    "urban": "bustling streets, merchants, city life",
    "industrial": "factory smoke, rust, labor",
    "ruins": "crumbling stone, forgotten history, decay",
    "coastal": "salt spray, fishing villages, sea trade",
    "mountains": "steep cliffs, thin air, isolated settlements",
    "swamp": "murky water, twisted trees, hidden dangers",
    "desert": "endless sand, scorching heat, mirages",
}

DEFAULT_DANGER_LEVELS = ["safe", "moderate", "dangerous", "deadly"]


@dataclass
class RegionContext:
    """Stores cached region theme information for consistent AI generation.

    Attributes:
        name: Region identifier (e.g., "Industrial District")
        theme: Sub-theme describing the region's character (e.g., "factory smoke, rust, labor")
        danger_level: Threat level of the region (safe/moderate/dangerous/deadly)
        landmarks: Key points of interest in the region (e.g., ["Rust Tower", "The Vats"])
        coordinates: Center coordinates of the region as (x, y) tuple
        generated_at: When context was AI-generated (None if not AI-generated)
    """

    name: str
    theme: str
    danger_level: str
    landmarks: list[str]
    coordinates: tuple[int, int]
    generated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize RegionContext to dictionary for save/load.

        Returns:
            Dictionary containing all context attributes with datetime as ISO string
            and coordinates as list (for JSON compatibility).
        """
        return {
            "name": self.name,
            "theme": self.theme,
            "danger_level": self.danger_level,
            "landmarks": self.landmarks,
            "coordinates": list(self.coordinates),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegionContext":
        """Deserialize RegionContext from dictionary.

        Args:
            data: Dictionary containing context attributes

        Returns:
            RegionContext instance with restored data
        """
        generated_at = None
        if data.get("generated_at"):
            generated_at = datetime.fromisoformat(data["generated_at"])

        return cls(
            name=data["name"],
            theme=data["theme"],
            danger_level=data["danger_level"],
            landmarks=data["landmarks"],
            coordinates=tuple(data["coordinates"]),
            generated_at=generated_at,
        )

    @classmethod
    def default(cls, name: str, coordinates: tuple[int, int]) -> "RegionContext":
        """Create a default RegionContext when AI generation is unavailable.

        Args:
            name: Region name/identifier
            coordinates: Center coordinates of the region

        Returns:
            RegionContext with sensible defaults
        """
        return cls(
            name=name,
            theme=DEFAULT_REGION_THEMES.get("wilderness", "untamed lands, mystery"),
            danger_level="moderate",
            landmarks=[],
            coordinates=coordinates,
            generated_at=None,
        )
