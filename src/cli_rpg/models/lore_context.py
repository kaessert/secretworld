"""LoreContext model for caching lore information.

LoreContext stores lore information (historical events, legendary items, legendary places,
prophecies, ancient civilizations, creation myths, deities) (Layer 6 in the hierarchy)
for richer world-building with deep narrative content. This sits below RegionContext (Layer 2)
in the layered query architecture, providing cultural and historical depth to regions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Default values for fallback context when AI is unavailable
DEFAULT_HISTORICAL_EVENT_TYPES = ["war", "plague", "discovery", "founding", "cataclysm"]

DEFAULT_DEITY_DOMAINS = ["war", "nature", "death", "knowledge", "trickery", "life"]

DEFAULT_DEITY_ALIGNMENTS = ["good", "neutral", "evil", "forgotten"]


@dataclass
class LoreContext:
    """Stores cached lore information for world-building.

    Attributes:
        region_name: Name of the region this lore belongs to
        coordinates: Coordinates of the region as (x, y) tuple
        generated_at: When context was AI-generated (None if not AI-generated)

        Historical Events:
        historical_events: Historical event data [{name, date, description, impact}]

        Legendary Items:
        legendary_items: Legendary item data [{name, description, powers, location_hint}]

        Legendary Places:
        legendary_places: Legendary place data [{name, description, danger_level, rumored_location}]

        Prophecies:
        prophecies: Prophecy data [{name, text, interpretation, fulfilled}]

        Ancient Civilizations:
        ancient_civilizations: Ancient civilization data [{name, era, achievements, downfall}]

        Creation Myths:
        creation_myths: Region-specific origin stories (list of strings)

        Deities:
        deities: Deity data [{name, domain, alignment, worship_status}]
    """

    # Required identifiers
    region_name: str
    coordinates: tuple[int, int]
    generated_at: Optional[datetime] = None

    # Historical Events (list of dicts with name, date, description, impact)
    historical_events: list[dict] = field(default_factory=list)

    # Legendary Items (list of dicts with name, description, powers, location_hint)
    legendary_items: list[dict] = field(default_factory=list)

    # Legendary Places (list of dicts with name, description, danger_level, rumored_location)
    legendary_places: list[dict] = field(default_factory=list)

    # Prophecies (list of dicts with name, text, interpretation, fulfilled)
    prophecies: list[dict] = field(default_factory=list)

    # Ancient Civilizations (list of dicts with name, era, achievements, downfall)
    ancient_civilizations: list[dict] = field(default_factory=list)

    # Creation Myths (list of strings - region-specific origin stories)
    creation_myths: list[str] = field(default_factory=list)

    # Deities (list of dicts with name, domain, alignment, worship_status)
    deities: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize LoreContext to dictionary for save/load.

        Returns:
            Dictionary containing all context attributes with datetime as ISO string
            and coordinates as list (for JSON compatibility).
        """
        return {
            "region_name": self.region_name,
            "coordinates": list(self.coordinates),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            # Lore data
            "historical_events": self.historical_events,
            "legendary_items": self.legendary_items,
            "legendary_places": self.legendary_places,
            "prophecies": self.prophecies,
            "ancient_civilizations": self.ancient_civilizations,
            "creation_myths": self.creation_myths,
            "deities": self.deities,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoreContext":
        """Deserialize LoreContext from dictionary.

        Args:
            data: Dictionary containing context attributes

        Returns:
            LoreContext instance with restored data
        """
        generated_at = None
        if data.get("generated_at"):
            generated_at = datetime.fromisoformat(data["generated_at"])

        return cls(
            region_name=data["region_name"],
            coordinates=tuple(data["coordinates"]),
            generated_at=generated_at,
            # Lore data (with backward-compatible defaults)
            historical_events=data.get("historical_events", []),
            legendary_items=data.get("legendary_items", []),
            legendary_places=data.get("legendary_places", []),
            prophecies=data.get("prophecies", []),
            ancient_civilizations=data.get("ancient_civilizations", []),
            creation_myths=data.get("creation_myths", []),
            deities=data.get("deities", []),
        )

    @classmethod
    def default(cls, region_name: str, coordinates: tuple[int, int]) -> "LoreContext":
        """Create a default LoreContext when AI generation is unavailable.

        Args:
            region_name: Name of the region
            coordinates: Coordinates of the region

        Returns:
            LoreContext with sensible defaults
        """
        return cls(
            region_name=region_name,
            coordinates=coordinates,
            generated_at=None,
        )
