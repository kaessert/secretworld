"""Tests for FeatureCoverage tracking system.

Tests the feature coverage tracking functionality that identifies
which game features have been exercised during playtesting.
"""

import time
import pytest

from scripts.validation.coverage import (
    FeatureCategory,
    FeatureEvent,
    CoverageStats,
    FeatureCoverage,
    FEATURE_DEFINITIONS,
)


class TestFeatureCategory:
    """Tests for FeatureCategory enum."""

    def test_feature_category_has_all_categories(self):
        """Spec: 14 categories defined matching ISSUES.md 'Features to Cover'."""
        expected_categories = {
            "CHARACTER_CREATION",
            "MOVEMENT",
            "COMBAT",
            "NPC_INTERACTION",
            "INVENTORY",
            "QUESTS",
            "CRAFTING",
            "EXPLORATION",
            "REST_CAMPING",
            "ECONOMY",
            "ENVIRONMENTAL",
            "RANGER_COMPANION",
            "SOCIAL_SKILLS",
            "PERSISTENCE",
        }

        actual_categories = {cat.name for cat in FeatureCategory}
        assert actual_categories == expected_categories
        assert len(FeatureCategory) == 14


class TestFeatureEvent:
    """Tests for FeatureEvent dataclass."""

    def test_feature_event_creation(self):
        """Spec: FeatureEvent has all required fields populated."""
        ts = time.time()
        event = FeatureEvent(
            feature="combat.attack",
            category=FeatureCategory.COMBAT,
            timestamp=ts,
            command="attack goblin",
            context={"target": "goblin", "damage": 15},
        )

        assert event.feature == "combat.attack"
        assert event.category == FeatureCategory.COMBAT
        assert event.timestamp == ts
        assert event.command == "attack goblin"
        assert event.context == {"target": "goblin", "damage": 15}

    def test_feature_event_default_context(self):
        """FeatureEvent context defaults to None."""
        event = FeatureEvent(
            feature="movement.overworld",
            category=FeatureCategory.MOVEMENT,
            timestamp=time.time(),
            command="go north",
        )

        assert event.context is None

    def test_feature_event_serialization(self):
        """Spec: to_dict/from_dict roundtrip for FeatureEvent."""
        ts = time.time()
        original = FeatureEvent(
            feature="npc.dialogue",
            category=FeatureCategory.NPC_INTERACTION,
            timestamp=ts,
            command="talk to merchant",
            context={"npc_name": "Bob"},
        )

        serialized = original.to_dict()
        restored = FeatureEvent.from_dict(serialized)

        assert restored.feature == original.feature
        assert restored.category == original.category
        assert restored.timestamp == original.timestamp
        assert restored.command == original.command
        assert restored.context == original.context


class TestCoverageStats:
    """Tests for CoverageStats dataclass."""

    def test_coverage_stats_creation(self):
        """CoverageStats has all required fields."""
        stats = CoverageStats(
            total=5,
            covered=3,
            events=10,
            features={"combat.attack", "combat.flee", "combat.ability"},
        )

        assert stats.total == 5
        assert stats.covered == 3
        assert stats.events == 10
        assert len(stats.features) == 3


class TestFeatureCoverage:
    """Tests for FeatureCoverage class."""

    def test_coverage_record_event(self):
        """Spec: Recording adds to events list."""
        coverage = FeatureCoverage()

        coverage.record(
            feature="combat.attack",
            category=FeatureCategory.COMBAT,
            command="attack goblin",
        )

        assert len(coverage.events) == 1
        assert coverage.events[0].feature == "combat.attack"
        assert coverage.events[0].category == FeatureCategory.COMBAT
        assert coverage.events[0].command == "attack goblin"

    def test_coverage_record_with_context(self):
        """Recording with context stores metadata."""
        coverage = FeatureCoverage()

        coverage.record(
            feature="inventory.equip",
            category=FeatureCategory.INVENTORY,
            command="equip sword",
            context={"item": "sword", "slot": "weapon"},
        )

        assert coverage.events[0].context == {"item": "sword", "slot": "weapon"}

    def test_coverage_record_multiple_same_feature(self):
        """Spec: Multiple events for same feature are recorded separately."""
        coverage = FeatureCoverage()

        coverage.record("combat.attack", FeatureCategory.COMBAT, "attack goblin")
        coverage.record("combat.attack", FeatureCategory.COMBAT, "attack orc")
        coverage.record("combat.attack", FeatureCategory.COMBAT, "attack troll")

        assert len(coverage.events) == 3

        # But should only count as 1 covered feature
        stats = coverage.get_coverage_by_category()
        assert stats[FeatureCategory.COMBAT].covered == 1
        assert stats[FeatureCategory.COMBAT].events == 3

    def test_coverage_by_category(self):
        """Spec: Stats calculated per category."""
        coverage = FeatureCoverage()

        # Add some combat features
        coverage.record("combat.attack", FeatureCategory.COMBAT, "attack")
        coverage.record("combat.flee", FeatureCategory.COMBAT, "flee")

        # Add some movement features
        coverage.record("movement.overworld", FeatureCategory.MOVEMENT, "go north")

        stats = coverage.get_coverage_by_category()

        # Combat: 2 covered out of 5 total
        combat_stats = stats[FeatureCategory.COMBAT]
        assert combat_stats.covered == 2
        assert combat_stats.events == 2
        assert "combat.attack" in combat_stats.features
        assert "combat.flee" in combat_stats.features

        # Movement: 1 covered out of 4 total
        movement_stats = stats[FeatureCategory.MOVEMENT]
        assert movement_stats.covered == 1
        assert movement_stats.events == 1
        assert "movement.overworld" in movement_stats.features

    def test_uncovered_features(self):
        """Spec: Returns unexercised features per category."""
        coverage = FeatureCoverage()

        # Cover some but not all combat features
        coverage.record("combat.attack", FeatureCategory.COMBAT, "attack")
        coverage.record("combat.flee", FeatureCategory.COMBAT, "flee")

        uncovered = coverage.get_uncovered_features()

        # Combat should have uncovered features
        combat_uncovered = uncovered[FeatureCategory.COMBAT]
        assert "combat.attack" not in combat_uncovered
        assert "combat.flee" not in combat_uncovered
        assert "combat.ability" in combat_uncovered
        assert "combat.stealth_kill" in combat_uncovered
        assert "combat.companion_attack" in combat_uncovered

    def test_coverage_percentage(self):
        """Spec: Total percentage calculation across all categories."""
        coverage = FeatureCoverage()

        # Get total features across all categories
        total_features = sum(len(features) for features in FEATURE_DEFINITIONS.values())

        # Cover exactly 10 unique features
        features_to_cover = [
            ("combat.attack", FeatureCategory.COMBAT),
            ("combat.flee", FeatureCategory.COMBAT),
            ("movement.overworld", FeatureCategory.MOVEMENT),
            ("movement.subgrid_entry", FeatureCategory.MOVEMENT),
            ("inventory.equip", FeatureCategory.INVENTORY),
            ("inventory.use", FeatureCategory.INVENTORY),
            ("quests.accept", FeatureCategory.QUESTS),
            ("crafting.gather", FeatureCategory.CRAFTING),
            ("exploration.map", FeatureCategory.EXPLORATION),
            ("economy.buy", FeatureCategory.ECONOMY),
        ]

        for feature, category in features_to_cover:
            coverage.record(feature, category, f"test {feature}")

        expected_percentage = (10 / total_features) * 100
        actual_percentage = coverage.get_coverage_percentage()

        assert abs(actual_percentage - expected_percentage) < 0.01

    def test_coverage_empty(self):
        """Spec: 0% coverage when no events recorded."""
        coverage = FeatureCoverage()

        assert coverage.get_coverage_percentage() == 0.0
        assert len(coverage.events) == 0

        stats = coverage.get_coverage_by_category()
        for category_stats in stats.values():
            assert category_stats.covered == 0
            assert category_stats.events == 0

    def test_coverage_serialization(self):
        """Spec: to_dict/from_dict roundtrip for FeatureCoverage."""
        coverage = FeatureCoverage()

        coverage.record("combat.attack", FeatureCategory.COMBAT, "attack", {"damage": 10})
        coverage.record("movement.overworld", FeatureCategory.MOVEMENT, "go north")
        coverage.record("combat.flee", FeatureCategory.COMBAT, "flee")

        serialized = coverage.to_dict()
        restored = FeatureCoverage.from_dict(serialized)

        assert len(restored.events) == 3
        assert restored.get_coverage_percentage() == coverage.get_coverage_percentage()

        # Verify events match
        for i, event in enumerate(coverage.events):
            assert restored.events[i].feature == event.feature
            assert restored.events[i].category == event.category
            assert restored.events[i].command == event.command


class TestFeatureDefinitions:
    """Tests for FEATURE_DEFINITIONS constant."""

    def test_feature_definitions_complete(self):
        """Spec: All categories have definitions in FEATURE_DEFINITIONS."""
        for category in FeatureCategory:
            assert category in FEATURE_DEFINITIONS, f"Missing definition for {category.name}"
            assert len(FEATURE_DEFINITIONS[category]) > 0, f"Empty definition for {category.name}"

    def test_feature_definitions_have_expected_features(self):
        """FEATURE_DEFINITIONS contains expected features per category."""
        # Spot check some expected features
        assert "combat.attack" in FEATURE_DEFINITIONS[FeatureCategory.COMBAT]
        assert "combat.flee" in FEATURE_DEFINITIONS[FeatureCategory.COMBAT]

        assert "movement.overworld" in FEATURE_DEFINITIONS[FeatureCategory.MOVEMENT]
        assert "movement.vertical" in FEATURE_DEFINITIONS[FeatureCategory.MOVEMENT]

        assert "inventory.equip" in FEATURE_DEFINITIONS[FeatureCategory.INVENTORY]

        assert "quests.accept" in FEATURE_DEFINITIONS[FeatureCategory.QUESTS]
        assert "quests.complete" in FEATURE_DEFINITIONS[FeatureCategory.QUESTS]
