"""Feature coverage tracking for automated playtesting.

This module provides a system to track which game features have been exercised
during playtesting, enabling identification of coverage gaps.

Classes:
    FeatureCategory: Enum of feature categories matching ISSUES.md
    FeatureEvent: Dataclass representing a single feature exercise event
    CoverageStats: Dataclass with coverage statistics for a category
    FeatureCoverage: Main tracker class for recording and analyzing coverage
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, Set
import time


class FeatureCategory(Enum):
    """Categories of game features to track coverage for.

    These categories match the "Features to Cover" section in ISSUES.md.
    """

    CHARACTER_CREATION = auto()  # All 5 classes
    MOVEMENT = auto()  # Overworld, subgrid, vertical z-levels
    COMBAT = auto()  # Attack, abilities, flee, stealth, companions
    NPC_INTERACTION = auto()  # Dialogue, shops, quests, arc progression
    INVENTORY = auto()  # Equip, unequip, use, drop, restrictions
    QUESTS = auto()  # Accept, track, complete, world effects, chains
    CRAFTING = auto()  # Gather, craft, skill progression, recipes
    EXPLORATION = auto()  # Map, secrets, puzzles, treasures
    REST_CAMPING = auto()  # Rest, camp, forage, hunt, dreams
    ECONOMY = auto()  # Buy, sell, price modifiers, supply/demand
    ENVIRONMENTAL = auto()  # Hazards, interior events
    RANGER_COMPANION = auto()  # Tame, summon, feed, combat
    SOCIAL_SKILLS = auto()  # Persuade, intimidate, bribe
    PERSISTENCE = auto()  # Save, load


# Feature definitions for each category
FEATURE_DEFINITIONS: Dict[FeatureCategory, Set[str]] = {
    FeatureCategory.CHARACTER_CREATION: {
        "character.warrior",
        "character.mage",
        "character.rogue",
        "character.ranger",
        "character.cleric",
    },
    FeatureCategory.MOVEMENT: {
        "movement.overworld",
        "movement.subgrid_entry",
        "movement.subgrid_exit",
        "movement.vertical",
    },
    FeatureCategory.COMBAT: {
        "combat.attack",
        "combat.ability",
        "combat.flee",
        "combat.stealth_kill",
        "combat.companion_attack",
    },
    FeatureCategory.NPC_INTERACTION: {
        "npc.dialogue",
        "npc.shop_browse",
        "npc.quest_accept",
        "npc.arc_progress",
    },
    FeatureCategory.INVENTORY: {
        "inventory.equip",
        "inventory.unequip",
        "inventory.use",
        "inventory.drop",
        "inventory.armor_restriction",
    },
    FeatureCategory.QUESTS: {
        "quests.accept",
        "quests.track",
        "quests.complete",
        "quests.world_effect",
        "quests.chain",
    },
    FeatureCategory.CRAFTING: {
        "crafting.gather",
        "crafting.craft",
        "crafting.skill_progression",
        "crafting.recipes",
    },
    FeatureCategory.EXPLORATION: {
        "exploration.map",
        "exploration.secrets",
        "exploration.puzzles",
        "exploration.treasures",
    },
    FeatureCategory.REST_CAMPING: {
        "rest.rest",
        "rest.camp",
        "rest.forage",
        "rest.hunt",
        "rest.dreams",
    },
    FeatureCategory.ECONOMY: {
        "economy.buy",
        "economy.sell",
        "economy.price_modifiers",
        "economy.supply_demand",
    },
    FeatureCategory.ENVIRONMENTAL: {
        "environmental.hazards",
        "environmental.interior_events",
    },
    FeatureCategory.RANGER_COMPANION: {
        "ranger.tame",
        "ranger.summon",
        "ranger.feed",
        "ranger.companion_combat",
    },
    FeatureCategory.SOCIAL_SKILLS: {
        "social.persuade",
        "social.intimidate",
        "social.bribe",
    },
    FeatureCategory.PERSISTENCE: {
        "persistence.save",
        "persistence.load",
    },
}


@dataclass
class FeatureEvent:
    """Record of a single feature being exercised during playtesting.

    Attributes:
        feature: Feature identifier (e.g., "combat.attack")
        category: FeatureCategory this feature belongs to
        timestamp: Unix timestamp when the feature was exercised
        command: The command that triggered this feature
        context: Optional metadata about the event
    """

    feature: str
    category: FeatureCategory
    timestamp: float
    command: str
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "feature": self.feature,
            "category": self.category.name,
            "timestamp": self.timestamp,
            "command": self.command,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureEvent":
        """Deserialize event from dictionary."""
        return cls(
            feature=data["feature"],
            category=FeatureCategory[data["category"]],
            timestamp=data["timestamp"],
            command=data["command"],
            context=data.get("context"),
        )


@dataclass
class CoverageStats:
    """Statistics for a single feature category.

    Attributes:
        total: Total number of features in this category
        covered: Number of features that have been exercised
        events: Total number of events recorded for this category
        features: Set of feature identifiers that were hit
    """

    total: int
    covered: int
    events: int
    features: Set[str] = field(default_factory=set)


class FeatureCoverage:
    """Tracks which game features have been exercised during playtesting.

    This class records feature events and provides methods to analyze
    coverage across all feature categories.
    """

    def __init__(self) -> None:
        """Initialize an empty coverage tracker."""
        self.events: list[FeatureEvent] = []
        self._feature_definitions: Dict[FeatureCategory, Set[str]] = FEATURE_DEFINITIONS.copy()

    def record(
        self,
        feature: str,
        category: FeatureCategory,
        command: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a feature being exercised.

        Args:
            feature: Feature identifier (e.g., "combat.attack")
            category: FeatureCategory this feature belongs to
            command: The command that triggered this feature
            context: Optional metadata about the event
        """
        event = FeatureEvent(
            feature=feature,
            category=category,
            timestamp=time.time(),
            command=command,
            context=context,
        )
        self.events.append(event)

    def get_coverage_by_category(self) -> Dict[FeatureCategory, CoverageStats]:
        """Get coverage statistics for each category.

        Returns:
            Dict mapping each FeatureCategory to its CoverageStats
        """
        # Initialize stats for all categories
        stats: Dict[FeatureCategory, CoverageStats] = {}
        for category in FeatureCategory:
            total_features = len(self._feature_definitions.get(category, set()))
            stats[category] = CoverageStats(
                total=total_features,
                covered=0,
                events=0,
                features=set(),
            )

        # Count events and covered features
        for event in self.events:
            if event.category in stats:
                stats[event.category].events += 1
                stats[event.category].features.add(event.feature)

        # Update covered counts
        for category in stats:
            stats[category].covered = len(stats[category].features)

        return stats

    def get_uncovered_features(self) -> Dict[FeatureCategory, Set[str]]:
        """Get features that have not been exercised.

        Returns:
            Dict mapping each FeatureCategory to the set of uncovered features
        """
        stats = self.get_coverage_by_category()
        uncovered: Dict[FeatureCategory, Set[str]] = {}

        for category in FeatureCategory:
            defined_features = self._feature_definitions.get(category, set())
            covered_features = stats[category].features
            uncovered[category] = defined_features - covered_features

        return uncovered

    def get_coverage_percentage(self) -> float:
        """Get the overall coverage percentage.

        Returns:
            Percentage of features covered (0.0 to 100.0)
        """
        total_features = sum(len(features) for features in self._feature_definitions.values())
        if total_features == 0:
            return 0.0

        # Count unique covered features
        covered_features: Set[str] = set()
        for event in self.events:
            covered_features.add(event.feature)

        return (len(covered_features) / total_features) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Serialize coverage tracker to dictionary.

        Returns:
            Dict representation suitable for JSON serialization
        """
        return {
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureCoverage":
        """Deserialize coverage tracker from dictionary.

        Args:
            data: Dict representation from to_dict()

        Returns:
            FeatureCoverage instance
        """
        coverage = cls()
        coverage.events = [FeatureEvent.from_dict(e) for e in data.get("events", [])]
        return coverage
