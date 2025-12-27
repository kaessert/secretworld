"""District model for themed sub-areas within large settlements.

The district system organizes mega-settlements (cities, metropolises, capitals)
into themed districts like market quarters, temple districts, residential areas, etc.
Each district has its own atmosphere, prosperity level, and notable features that
influence NPC generation, shop types, and random encounters within its boundaries.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class DistrictType(Enum):
    """Types of districts found within large settlements.

    Each district type represents a functional area of the settlement:
    - MARKET: Commercial center with shops and traders
    - TEMPLE: Religious quarter with temples and shrines
    - RESIDENTIAL: Housing areas for common citizens
    - NOBLE: Upper-class district with mansions and gardens
    - SLUMS: Poor district with crime and desperation
    - CRAFTSMEN: Artisan quarter with workshops and guilds
    - DOCKS: Harbor area with warehouses and sailors
    - ENTERTAINMENT: Taverns, theaters, and gambling dens
    - MILITARY: Barracks, training grounds, and armories
    """

    MARKET = "Market"
    TEMPLE = "Temple"
    RESIDENTIAL = "Residential"
    NOBLE = "Noble"
    SLUMS = "Slums"
    CRAFTSMEN = "Craftsmen"
    DOCKS = "Docks"
    ENTERTAINMENT = "Entertainment"
    MILITARY = "Military"


@dataclass
class District:
    """Represents a themed district within a large settlement.

    Districts partition mega-settlements into distinct areas, each with
    its own character, atmosphere, and types of NPCs/shops.

    Attributes:
        name: Display name of the district (e.g., "The Golden Market")
        district_type: Category from DistrictType enum
        description: Thematic description of the district
        bounds: (min_x, max_x, min_y, max_y) within parent SubGrid
        atmosphere: Mood/feeling (e.g., "bustling", "quiet", "dangerous")
        prosperity: Economic level (poor, modest, prosperous, wealthy)
        notable_features: Key landmarks within the district
    """

    name: str
    district_type: DistrictType
    description: str
    bounds: tuple[int, int, int, int]  # (min_x, max_x, min_y, max_y)
    atmosphere: str = "neutral"
    prosperity: str = "modest"
    notable_features: List[str] = field(default_factory=list)

    def contains(self, x: int, y: int) -> bool:
        """Check if coordinates are within this district's bounds.

        Args:
            x: X coordinate to check
            y: Y coordinate to check

        Returns:
            True if coordinates are within bounds, False otherwise
        """
        min_x, max_x, min_y, max_y = self.bounds
        return min_x <= x <= max_x and min_y <= y <= max_y

    def to_dict(self) -> dict:
        """Serialize district to dictionary.

        Returns:
            Dictionary containing all district attributes
        """
        return {
            "name": self.name,
            "district_type": self.district_type.value,
            "description": self.description,
            "bounds": list(self.bounds),
            "atmosphere": self.atmosphere,
            "prosperity": self.prosperity,
            "notable_features": self.notable_features,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "District":
        """Deserialize district from dictionary.

        Args:
            data: Dictionary containing district attributes

        Returns:
            District instance
        """
        return cls(
            name=data["name"],
            district_type=DistrictType(data["district_type"]),
            description=data["description"],
            bounds=tuple(data["bounds"]),
            atmosphere=data.get("atmosphere", "neutral"),
            prosperity=data.get("prosperity", "modest"),
            notable_features=data.get("notable_features", []),
        )
