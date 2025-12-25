"""Tests for companion banter system.

The banter system displays companion comments during travel:
- 25% trigger chance per move when companions are present
- Context-aware: location, weather, time, dread influence banter
- Bond-level depth: TRUSTED/DEVOTED companions have richer banter
"""

import random
from unittest.mock import patch, MagicMock

import pytest

from cli_rpg.companion_banter import (
    BANTER_CHANCE,
    CATEGORY_BANTER,
    WEATHER_BANTER,
    NIGHT_BANTER,
    DREAD_BANTER,
    TRUSTED_BANTER,
    DEVOTED_BANTER,
    CompanionBanterService,
    format_banter,
)
from cli_rpg.models.companion import Companion, BondLevel


class TestBanterServiceCreation:
    """Tests for banter service initialization."""

    def test_banter_service_creation(self):
        """Test that banter service can be created."""
        # Spec: Banter service instantiation
        service = CompanionBanterService()
        assert service is not None


class TestBanterTriggering:
    """Tests for banter trigger conditions."""

    def test_banter_returns_none_when_no_companions(self):
        """Test that banter returns None when no companions present."""
        # Spec: No banter when no companions
        service = CompanionBanterService()
        result = service.get_banter(
            companions=[],
            location_category="town",
        )
        assert result is None

    def test_banter_respects_trigger_chance(self):
        """Test that banter triggers approximately 25% of the time."""
        # Spec: 25% chance per move when companions present
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="A mysterious ranger",
            recruited_at="Town Square",
            bond_points=50,
        )

        # Run many trials to verify approximately 25% trigger rate
        triggers = 0
        trials = 1000
        for _ in range(trials):
            result = service.get_banter(
                companions=[companion],
                location_category="town",
            )
            if result is not None:
                triggers += 1

        # Allow 20-30% range (statistical margin)
        rate = triggers / trials
        assert 0.15 <= rate <= 0.35, f"Expected ~25% trigger rate, got {rate:.1%}"

    def test_banter_selects_random_companion(self):
        """Test that banter picks a random companion when multiple present."""
        # Spec: Pick random companion if multiple
        service = CompanionBanterService()
        companion1 = Companion(name="Elara", description="Ranger", recruited_at="Town", bond_points=50)
        companion2 = Companion(name="Thorin", description="Dwarf", recruited_at="Cave", bond_points=50)

        # Force banter to trigger
        names_seen = set()
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):  # Force trigger
            for _ in range(100):
                result = service.get_banter(
                    companions=[companion1, companion2],
                    location_category="town",
                )
                if result:
                    names_seen.add(result[0])

        # Both companions should be selected at some point
        assert "Elara" in names_seen, "Elara should be selected sometimes"
        assert "Thorin" in names_seen, "Thorin should be selected sometimes"


class TestCategoryBasedBanter:
    """Tests for location category-based banter."""

    def test_banter_for_town_location(self):
        """Test that town locations produce town-specific banter."""
        # Spec: Location-based comments about location category
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,  # ACQUAINTANCE - base banter only
        )

        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):  # Force trigger
            # Run multiple times to get category banter
            for _ in range(50):
                result = service.get_banter(
                    companions=[companion],
                    location_category="town",
                )
                if result:
                    _, banter_text = result
                    # Check it's from town or default category
                    if banter_text in CATEGORY_BANTER["town"]:
                        return  # Success - found town banter

        # Should find at least one town banter in 50 tries
        pytest.fail("Expected town-specific banter")

    def test_banter_for_dungeon_location(self):
        """Test that dungeon locations produce dungeon-specific banter."""
        # Spec: Location-based comments about location category (dungeon)
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,
        )

        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(50):
                result = service.get_banter(
                    companions=[companion],
                    location_category="dungeon",
                )
                if result:
                    _, banter_text = result
                    if banter_text in CATEGORY_BANTER["dungeon"]:
                        return  # Success

        pytest.fail("Expected dungeon-specific banter")

    def test_banter_for_forest_location(self):
        """Test that forest locations produce forest-specific banter."""
        # Spec: Location-based comments about location category (forest)
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,
        )

        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(50):
                result = service.get_banter(
                    companions=[companion],
                    location_category="forest",
                )
                if result:
                    _, banter_text = result
                    if banter_text in CATEGORY_BANTER["forest"]:
                        return  # Success

        pytest.fail("Expected forest-specific banter")

    def test_banter_fallback_for_unknown_category(self):
        """Test that unknown categories use default banter."""
        # Spec: Fallback for unknown category
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,
        )

        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(50):
                result = service.get_banter(
                    companions=[companion],
                    location_category="unknown_category",
                )
                if result:
                    _, banter_text = result
                    if banter_text in CATEGORY_BANTER["default"]:
                        return  # Success

        pytest.fail("Expected default banter for unknown category")


class TestConditionalBanter:
    """Tests for weather, time, and dread-based banter."""

    def test_banter_references_weather_in_storm(self):
        """Test that storm weather triggers weather-specific banter."""
        # Spec: Weather-based - React to weather conditions (storm)
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,
        )

        found_weather_banter = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(100):
                result = service.get_banter(
                    companions=[companion],
                    location_category="wilderness",
                    weather="storm",
                )
                if result:
                    _, banter_text = result
                    if banter_text in WEATHER_BANTER.get("storm", []):
                        found_weather_banter = True
                        break

        assert found_weather_banter, "Expected storm-related banter"

    def test_banter_references_night_time(self):
        """Test that night time triggers night-specific banter."""
        # Spec: Time-based - Day/night observations
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,
        )

        found_night_banter = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(100):
                result = service.get_banter(
                    companions=[companion],
                    location_category="wilderness",
                    is_night=True,
                )
                if result:
                    _, banter_text = result
                    if banter_text in NIGHT_BANTER:
                        found_night_banter = True
                        break

        assert found_night_banter, "Expected night-related banter"

    def test_banter_nervous_at_high_dread(self):
        """Test that high dread (50%+) triggers nervous banter."""
        # Spec: Dread-based - Nervous comments at high dread (50%+)
        service = CompanionBanterService()
        companion = Companion(
            name="Elara",
            description="Ranger",
            recruited_at="Town",
            bond_points=25,
        )

        found_dread_banter = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(100):
                result = service.get_banter(
                    companions=[companion],
                    location_category="dungeon",
                    dread=60,  # High dread
                )
                if result:
                    _, banter_text = result
                    if banter_text in DREAD_BANTER:
                        found_dread_banter = True
                        break

        assert found_dread_banter, "Expected dread-related nervous banter"


class TestBondLevelInfluence:
    """Tests for bond level affecting banter content."""

    def test_banter_varies_by_bond_level(self):
        """Test that bond level influences available banter."""
        # Spec: Bond-level-based - More personal at TRUSTED/DEVOTED
        service = CompanionBanterService()

        # STRANGER companion - should not get trusted banter
        stranger = Companion(
            name="Stranger",
            description="Unknown",
            recruited_at="Town",
            bond_points=10,  # STRANGER level
        )
        assert stranger.get_bond_level() == BondLevel.STRANGER

        # TRUSTED companion - may get trusted banter
        trusted = Companion(
            name="Friend",
            description="Trusted ally",
            recruited_at="Town",
            bond_points=60,  # TRUSTED level
        )
        assert trusted.get_bond_level() == BondLevel.TRUSTED

        # Verify trusted companion can get trusted banter
        found_trusted_banter = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(200):
                result = service.get_banter(
                    companions=[trusted],
                    location_category="town",
                )
                if result:
                    _, banter_text = result
                    if banter_text in TRUSTED_BANTER:
                        found_trusted_banter = True
                        break

        assert found_trusted_banter, "TRUSTED companion should occasionally have trusted banter"

    def test_devoted_companion_more_personal_banter(self):
        """Test that DEVOTED companions can get devoted banter."""
        # Spec: Higher bond = more varied/deeper banter
        service = CompanionBanterService()
        devoted = Companion(
            name="Beloved",
            description="Closest friend",
            recruited_at="Town",
            bond_points=85,  # DEVOTED level
        )
        assert devoted.get_bond_level() == BondLevel.DEVOTED

        found_devoted_banter = False
        with patch("cli_rpg.companion_banter.random.random", return_value=0.1):
            for _ in range(200):
                result = service.get_banter(
                    companions=[devoted],
                    location_category="town",
                )
                if result:
                    _, banter_text = result
                    if banter_text in DEVOTED_BANTER:
                        found_devoted_banter = True
                        break

        assert found_devoted_banter, "DEVOTED companion should occasionally have devoted banter"


class TestBanterFormatting:
    """Tests for banter output formatting."""

    def test_format_banter_with_companion_name(self):
        """Test that banter is formatted with companion name."""
        # Spec: Styled with companion name in color, quote formatted
        result = format_banter("Elara", "I've heard stories about places like this...")
        assert "Elara" in result
        assert "I've heard stories about places like this..." in result

    def test_format_banter_has_correct_prefix(self):
        """Test that banter has [Companion] prefix."""
        # Spec: Format like [Companion] Name: "text"
        result = format_banter("Thorin", "Stay close!")
        assert "[Companion]" in result
        assert "Thorin" in result
        assert "Stay close!" in result
