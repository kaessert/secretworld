"""Tests for agent personality system.

Tests the PersonalityType enum, PersonalityTraits dataclass, and preset values
as specified in the implementation plan.
"""

import pytest

from scripts.agent.personality import (
    PersonalityType,
    PersonalityTraits,
    PERSONALITY_PRESETS,
    get_personality_traits,
)


class TestPersonalityType:
    """Test PersonalityType enum has all required values."""

    def test_has_cautious_explorer(self):
        """Spec: PersonalityType enum with 5 values - CAUTIOUS_EXPLORER."""
        assert PersonalityType.CAUTIOUS_EXPLORER is not None

    def test_has_aggressive_fighter(self):
        """Spec: PersonalityType enum with 5 values - AGGRESSIVE_FIGHTER."""
        assert PersonalityType.AGGRESSIVE_FIGHTER is not None

    def test_has_completionist(self):
        """Spec: PersonalityType enum with 5 values - COMPLETIONIST."""
        assert PersonalityType.COMPLETIONIST is not None

    def test_has_speedrunner(self):
        """Spec: PersonalityType enum with 5 values - SPEEDRUNNER."""
        assert PersonalityType.SPEEDRUNNER is not None

    def test_has_roleplayer(self):
        """Spec: PersonalityType enum with 5 values - ROLEPLAYER."""
        assert PersonalityType.ROLEPLAYER is not None

    def test_exactly_five_types(self):
        """Spec: PersonalityType enum with 5 values."""
        assert len(PersonalityType) == 5


class TestPersonalityTraits:
    """Test PersonalityTraits dataclass structure."""

    def test_has_risk_tolerance(self):
        """Spec: PersonalityTraits has risk_tolerance field."""
        traits = PersonalityTraits(
            risk_tolerance=0.5,
            exploration_drive=0.5,
            social_engagement=0.5,
            combat_aggression=0.5,
            resource_conservation=0.5,
        )
        assert traits.risk_tolerance == 0.5

    def test_has_exploration_drive(self):
        """Spec: PersonalityTraits has exploration_drive field."""
        traits = PersonalityTraits(
            risk_tolerance=0.5,
            exploration_drive=0.8,
            social_engagement=0.5,
            combat_aggression=0.5,
            resource_conservation=0.5,
        )
        assert traits.exploration_drive == 0.8

    def test_has_social_engagement(self):
        """Spec: PersonalityTraits has social_engagement field."""
        traits = PersonalityTraits(
            risk_tolerance=0.5,
            exploration_drive=0.5,
            social_engagement=0.7,
            combat_aggression=0.5,
            resource_conservation=0.5,
        )
        assert traits.social_engagement == 0.7

    def test_has_combat_aggression(self):
        """Spec: PersonalityTraits has combat_aggression field."""
        traits = PersonalityTraits(
            risk_tolerance=0.5,
            exploration_drive=0.5,
            social_engagement=0.5,
            combat_aggression=0.9,
            resource_conservation=0.5,
        )
        assert traits.combat_aggression == 0.9

    def test_has_resource_conservation(self):
        """Spec: PersonalityTraits has resource_conservation field."""
        traits = PersonalityTraits(
            risk_tolerance=0.5,
            exploration_drive=0.5,
            social_engagement=0.5,
            combat_aggression=0.5,
            resource_conservation=0.3,
        )
        assert traits.resource_conservation == 0.3


class TestPersonalityPresets:
    """Test preset values match the specification from ISSUES.md."""

    def test_all_presets_exist(self):
        """Spec: All PersonalityTypes have corresponding presets."""
        for personality_type in PersonalityType:
            assert personality_type in PERSONALITY_PRESETS

    def test_cautious_explorer_preset(self):
        """Spec: CAUTIOUS_EXPLORER - Risk 0.2, Exploration 0.9, Social 0.7, Combat 0.3, Conservation 0.7."""
        traits = PERSONALITY_PRESETS[PersonalityType.CAUTIOUS_EXPLORER]
        assert traits.risk_tolerance == 0.2
        assert traits.exploration_drive == 0.9
        assert traits.social_engagement == 0.7
        assert traits.combat_aggression == 0.3
        assert traits.resource_conservation == 0.7

    def test_aggressive_fighter_preset(self):
        """Spec: AGGRESSIVE_FIGHTER - Risk 0.9, Exploration 0.4, Social 0.3, Combat 0.9, Conservation 0.2."""
        traits = PERSONALITY_PRESETS[PersonalityType.AGGRESSIVE_FIGHTER]
        assert traits.risk_tolerance == 0.9
        assert traits.exploration_drive == 0.4
        assert traits.social_engagement == 0.3
        assert traits.combat_aggression == 0.9
        assert traits.resource_conservation == 0.2

    def test_completionist_preset(self):
        """Spec: COMPLETIONIST - Risk 0.5, Exploration 1.0, Social 1.0, Combat 0.5, Conservation 0.4."""
        traits = PERSONALITY_PRESETS[PersonalityType.COMPLETIONIST]
        assert traits.risk_tolerance == 0.5
        assert traits.exploration_drive == 1.0
        assert traits.social_engagement == 1.0
        assert traits.combat_aggression == 0.5
        assert traits.resource_conservation == 0.4

    def test_speedrunner_preset(self):
        """Spec: SPEEDRUNNER - Risk 0.7, Exploration 0.1, Social 0.1, Combat 0.4, Conservation 0.3."""
        traits = PERSONALITY_PRESETS[PersonalityType.SPEEDRUNNER]
        assert traits.risk_tolerance == 0.7
        assert traits.exploration_drive == 0.1
        assert traits.social_engagement == 0.1
        assert traits.combat_aggression == 0.4
        assert traits.resource_conservation == 0.3

    def test_roleplayer_preset(self):
        """Spec: ROLEPLAYER - Risk 0.5, Exploration 0.7, Social 0.9, Combat 0.5, Conservation 0.5."""
        traits = PERSONALITY_PRESETS[PersonalityType.ROLEPLAYER]
        assert traits.risk_tolerance == 0.5
        assert traits.exploration_drive == 0.7
        assert traits.social_engagement == 0.9
        assert traits.combat_aggression == 0.5
        assert traits.resource_conservation == 0.5


class TestTraitValidation:
    """Test that all trait values are within valid range (0.0-1.0)."""

    @pytest.mark.parametrize("personality_type", list(PersonalityType))
    def test_all_traits_in_valid_range(self, personality_type):
        """Spec: Traits validated to 0.0-1.0 range."""
        traits = PERSONALITY_PRESETS[personality_type]
        assert 0.0 <= traits.risk_tolerance <= 1.0
        assert 0.0 <= traits.exploration_drive <= 1.0
        assert 0.0 <= traits.social_engagement <= 1.0
        assert 0.0 <= traits.combat_aggression <= 1.0
        assert 0.0 <= traits.resource_conservation <= 1.0


class TestGetPersonalityTraits:
    """Test the get_personality_traits helper function."""

    def test_returns_correct_traits(self):
        """Spec: get_personality_traits returns correct values."""
        traits = get_personality_traits(PersonalityType.CAUTIOUS_EXPLORER)
        expected = PERSONALITY_PRESETS[PersonalityType.CAUTIOUS_EXPLORER]
        assert traits == expected

    @pytest.mark.parametrize("personality_type", list(PersonalityType))
    def test_returns_traits_for_all_types(self, personality_type):
        """Spec: get_personality_traits works for all types."""
        traits = get_personality_traits(personality_type)
        assert isinstance(traits, PersonalityTraits)


class TestSerialization:
    """Test serialization for checkpoint compatibility."""

    def test_traits_to_dict(self):
        """Spec: Serialization works for checkpoint compatibility (to_dict)."""
        traits = PersonalityTraits(
            risk_tolerance=0.2,
            exploration_drive=0.9,
            social_engagement=0.7,
            combat_aggression=0.3,
            resource_conservation=0.7,
        )
        data = traits.to_dict()
        assert data == {
            "risk_tolerance": 0.2,
            "exploration_drive": 0.9,
            "social_engagement": 0.7,
            "combat_aggression": 0.3,
            "resource_conservation": 0.7,
        }

    def test_traits_from_dict(self):
        """Spec: Serialization works for checkpoint compatibility (from_dict)."""
        data = {
            "risk_tolerance": 0.5,
            "exploration_drive": 0.5,
            "social_engagement": 0.5,
            "combat_aggression": 0.5,
            "resource_conservation": 0.5,
        }
        traits = PersonalityTraits.from_dict(data)
        assert traits.risk_tolerance == 0.5
        assert traits.exploration_drive == 0.5
        assert traits.social_engagement == 0.5
        assert traits.combat_aggression == 0.5
        assert traits.resource_conservation == 0.5

    def test_serialization_round_trip(self):
        """Spec: Serialization round-trip works correctly."""
        original = PersonalityTraits(
            risk_tolerance=0.2,
            exploration_drive=0.9,
            social_engagement=0.7,
            combat_aggression=0.3,
            resource_conservation=0.7,
        )
        data = original.to_dict()
        restored = PersonalityTraits.from_dict(data)
        assert restored == original
