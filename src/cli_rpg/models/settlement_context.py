"""SettlementContext model for caching settlement-level information.

SettlementContext stores settlement character networks, politics, and trade
(Layer 5 in the hierarchy) for richer settlement generation with NPC relationships,
guilds, political figures, and trade routes. This sits below RegionContext (Layer 2)
and Location (Layer 3) in the layered query architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Default values for fallback context when AI is unavailable
DEFAULT_GOVERNMENT_TYPES = ["council", "monarchy", "theocracy", "oligarchy", "democracy", "anarchy"]

DEFAULT_POPULATION_SIZES = ["hamlet", "village", "town", "city", "metropolis"]

DEFAULT_PROSPERITY_LEVELS = ["poor", "modest", "prosperous", "wealthy"]


@dataclass
class SettlementContext:
    """Stores cached settlement information for character networks, politics, and trade.

    Attributes:
        settlement_name: Name of the settlement
        location_coordinates: Coordinates of the settlement as (x, y) tuple
        generated_at: When context was AI-generated (None if not AI-generated)

        Character Networks:
        notable_families: Prominent families in the settlement
        npc_relationships: NPC relationship data [{npc_a, npc_b, type, strength}]

        Economic Connections:
        trade_routes: Trade route data [{origin, destination, goods, status}]
        local_guilds: Guilds operating in the settlement
        market_specialty: Settlement's market focus/specialty

        Political Structure:
        government_type: Type of government (council, monarchy, theocracy, etc.)
        political_figures: Political figure data [{name, title, faction}]
        current_tensions: Ongoing political tensions/conflicts

        Social Atmosphere:
        population_size: Settlement size (hamlet, village, town, city, metropolis)
        prosperity_level: Economic prosperity (poor, modest, prosperous, wealthy)
        social_issues: Social problems affecting the settlement
    """

    # Required identifiers
    settlement_name: str
    location_coordinates: tuple[int, int]
    generated_at: Optional[datetime] = None

    # Character Networks
    notable_families: list[str] = field(default_factory=list)
    npc_relationships: list[dict] = field(default_factory=list)

    # Economic Connections
    trade_routes: list[dict] = field(default_factory=list)
    local_guilds: list[str] = field(default_factory=list)
    market_specialty: str = ""

    # Political Structure
    government_type: str = ""
    political_figures: list[dict] = field(default_factory=list)
    current_tensions: list[str] = field(default_factory=list)

    # Social Atmosphere
    population_size: str = ""
    prosperity_level: str = ""
    social_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize SettlementContext to dictionary for save/load.

        Returns:
            Dictionary containing all context attributes with datetime as ISO string
            and coordinates as list (for JSON compatibility).
        """
        return {
            "settlement_name": self.settlement_name,
            "location_coordinates": list(self.location_coordinates),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            # Character Networks
            "notable_families": self.notable_families,
            "npc_relationships": self.npc_relationships,
            # Economic Connections
            "trade_routes": self.trade_routes,
            "local_guilds": self.local_guilds,
            "market_specialty": self.market_specialty,
            # Political Structure
            "government_type": self.government_type,
            "political_figures": self.political_figures,
            "current_tensions": self.current_tensions,
            # Social Atmosphere
            "population_size": self.population_size,
            "prosperity_level": self.prosperity_level,
            "social_issues": self.social_issues,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SettlementContext":
        """Deserialize SettlementContext from dictionary.

        Args:
            data: Dictionary containing context attributes

        Returns:
            SettlementContext instance with restored data
        """
        generated_at = None
        if data.get("generated_at"):
            generated_at = datetime.fromisoformat(data["generated_at"])

        return cls(
            settlement_name=data["settlement_name"],
            location_coordinates=tuple(data["location_coordinates"]),
            generated_at=generated_at,
            # Character Networks (with backward-compatible defaults)
            notable_families=data.get("notable_families", []),
            npc_relationships=data.get("npc_relationships", []),
            # Economic Connections (with backward-compatible defaults)
            trade_routes=data.get("trade_routes", []),
            local_guilds=data.get("local_guilds", []),
            market_specialty=data.get("market_specialty", ""),
            # Political Structure (with backward-compatible defaults)
            government_type=data.get("government_type", ""),
            political_figures=data.get("political_figures", []),
            current_tensions=data.get("current_tensions", []),
            # Social Atmosphere (with backward-compatible defaults)
            population_size=data.get("population_size", ""),
            prosperity_level=data.get("prosperity_level", ""),
            social_issues=data.get("social_issues", []),
        )

    @classmethod
    def default(cls, name: str, coordinates: tuple[int, int]) -> "SettlementContext":
        """Create a default SettlementContext when AI generation is unavailable.

        Args:
            name: Settlement name/identifier
            coordinates: Coordinates of the settlement

        Returns:
            SettlementContext with sensible defaults
        """
        return cls(
            settlement_name=name,
            location_coordinates=coordinates,
            generated_at=None,
        )
