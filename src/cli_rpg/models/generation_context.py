"""GenerationContext model for aggregating all context layers.

GenerationContext combines all 6 context layers (WorldContext, RegionContext,
SettlementContext, LoreContext) into a single object for prompt generation.
This enables AI generation methods to access all available context through
a unified `to_prompt_context()` method.
"""

from dataclasses import dataclass
from typing import Optional

from cli_rpg.models.world_context import WorldContext
from cli_rpg.models.region_context import RegionContext
from cli_rpg.models.settlement_context import SettlementContext
from cli_rpg.models.lore_context import LoreContext


@dataclass
class GenerationContext:
    """Aggregates all context layers for AI prompt generation.

    Attributes:
        world: Layer 1 - World theme context (always required)
        region: Layer 2 - Region theme context (optional)
        settlement: Layer 5 - Settlement context (optional)
        world_lore: Layer 6 - World-level lore context (optional)
        region_lore: Layer 6 - Region-level lore context (optional)
    """

    world: WorldContext  # Layer 1 - always required
    region: Optional[RegionContext] = None  # Layer 2
    settlement: Optional[SettlementContext] = None  # Layer 5
    world_lore: Optional[LoreContext] = None  # Layer 6 (world-level)
    region_lore: Optional[LoreContext] = None  # Layer 6 (region-level)

    def to_prompt_context(self) -> dict:
        """Aggregate all layers into a prompt-ready dictionary.

        Returns:
            Dictionary containing flattened context from all available layers,
            suitable for injection into AI prompts.
        """
        context = {}

        # Layer 1: WorldContext (always present)
        context["theme"] = self.world.theme
        context["theme_essence"] = self.world.theme_essence
        context["naming_style"] = self.world.naming_style
        context["tone"] = self.world.tone
        context["creation_myth"] = self.world.creation_myth
        context["major_conflicts"] = self.world.major_conflicts
        context["legendary_artifacts"] = self.world.legendary_artifacts
        context["prophecies"] = self.world.prophecies
        context["major_factions"] = self.world.major_factions
        context["faction_tensions"] = self.world.faction_tensions
        context["economic_era"] = self.world.economic_era

        # Layer 2: RegionContext (optional)
        if self.region is not None:
            context["region_name"] = self.region.name
            context["region_theme"] = self.region.theme
            context["danger_level"] = self.region.danger_level
            context["landmarks"] = self.region.landmarks
            context["region_coordinates"] = self.region.coordinates
            # Economy fields
            context["primary_resources"] = self.region.primary_resources
            context["scarce_resources"] = self.region.scarce_resources
            context["trade_goods"] = self.region.trade_goods
            context["price_modifier"] = self.region.price_modifier
            # History fields
            context["founding_story"] = self.region.founding_story
            context["historical_events"] = self.region.historical_events
            context["ruined_civilizations"] = self.region.ruined_civilizations
            context["legendary_locations"] = self.region.legendary_locations
            # Atmosphere fields
            context["common_creatures"] = self.region.common_creatures
            context["weather_tendency"] = self.region.weather_tendency
            context["ambient_sounds"] = self.region.ambient_sounds

        # Layer 5: SettlementContext (optional)
        if self.settlement is not None:
            context["settlement_name"] = self.settlement.settlement_name
            context["settlement_coordinates"] = self.settlement.location_coordinates
            # Character Networks
            context["notable_families"] = self.settlement.notable_families
            context["npc_relationships"] = self.settlement.npc_relationships
            # Economic Connections
            context["trade_routes"] = self.settlement.trade_routes
            context["local_guilds"] = self.settlement.local_guilds
            context["market_specialty"] = self.settlement.market_specialty
            # Political Structure
            context["government_type"] = self.settlement.government_type
            context["political_figures"] = self.settlement.political_figures
            context["current_tensions"] = self.settlement.current_tensions
            # Social Atmosphere
            context["population_size"] = self.settlement.population_size
            context["prosperity_level"] = self.settlement.prosperity_level
            context["social_issues"] = self.settlement.social_issues

        # Layer 6: LoreContext - world-level (optional)
        if self.world_lore is not None:
            context["world_historical_events"] = self.world_lore.historical_events
            context["world_legendary_items"] = self.world_lore.legendary_items
            context["world_legendary_places"] = self.world_lore.legendary_places
            context["world_prophecies"] = self.world_lore.prophecies
            context["world_ancient_civilizations"] = self.world_lore.ancient_civilizations
            context["world_creation_myths"] = self.world_lore.creation_myths
            context["world_deities"] = self.world_lore.deities

        # Layer 6: LoreContext - region-level (optional)
        if self.region_lore is not None:
            context["region_historical_events"] = self.region_lore.historical_events
            context["region_legendary_items"] = self.region_lore.legendary_items
            context["region_legendary_places"] = self.region_lore.legendary_places
            context["region_prophecies"] = self.region_lore.prophecies
            context["region_ancient_civilizations"] = self.region_lore.ancient_civilizations
            context["region_creation_myths"] = self.region_lore.creation_myths
            context["region_deities"] = self.region_lore.deities

        return context

    def to_dict(self) -> dict:
        """Serialize GenerationContext to dictionary for save/load.

        Returns:
            Dictionary containing all context layers, each serialized.
        """
        data = {
            "world": self.world.to_dict(),
        }
        if self.region is not None:
            data["region"] = self.region.to_dict()
        if self.settlement is not None:
            data["settlement"] = self.settlement.to_dict()
        if self.world_lore is not None:
            data["world_lore"] = self.world_lore.to_dict()
        if self.region_lore is not None:
            data["region_lore"] = self.region_lore.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GenerationContext":
        """Deserialize GenerationContext from dictionary.

        Args:
            data: Dictionary containing context layer data

        Returns:
            GenerationContext instance with restored data
        """
        world = WorldContext.from_dict(data["world"])

        region = None
        if "region" in data:
            region = RegionContext.from_dict(data["region"])

        settlement = None
        if "settlement" in data:
            settlement = SettlementContext.from_dict(data["settlement"])

        world_lore = None
        if "world_lore" in data:
            world_lore = LoreContext.from_dict(data["world_lore"])

        region_lore = None
        if "region_lore" in data:
            region_lore = LoreContext.from_dict(data["region_lore"])

        return cls(
            world=world,
            region=region,
            settlement=settlement,
            world_lore=world_lore,
            region_lore=region_lore,
        )
