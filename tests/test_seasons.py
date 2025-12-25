"""Tests for seasonal events and festivals system.

These tests verify the season/day tracking, festival spawning,
and festival gameplay effects.
"""

import pytest
from cli_rpg.models.game_time import GameTime
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState


class TestSeasonModel:
    """Tests for season tracking in GameTime model."""

    # Spec: New GameTime starts at Spring Day 1
    def test_season_defaults_to_spring_day_1(self):
        """New GameTime defaults to day 1 (Spring)."""
        time = GameTime()
        assert time.get_day() == 1
        assert time.get_season() == "spring"

    # Spec: Days 1-30 are Spring
    def test_get_season_spring_days_1_30(self):
        """Days 1-30 return 'spring'."""
        time = GameTime()
        # Day 1
        time.total_hours = 0
        assert time.get_season() == "spring"
        assert time.get_day() == 1

        # Day 30 (hours 696-719)
        time.total_hours = 29 * 24  # Start of day 30
        assert time.get_season() == "spring"
        assert time.get_day() == 30

    # Spec: Days 31-60 are Summer
    def test_get_season_summer_days_31_60(self):
        """Days 31-60 return 'summer'."""
        time = GameTime()
        # Day 31
        time.total_hours = 30 * 24
        assert time.get_season() == "summer"
        assert time.get_day() == 31

        # Day 60
        time.total_hours = 59 * 24
        assert time.get_season() == "summer"
        assert time.get_day() == 60

    # Spec: Days 61-90 are Autumn
    def test_get_season_autumn_days_61_90(self):
        """Days 61-90 return 'autumn'."""
        time = GameTime()
        # Day 61
        time.total_hours = 60 * 24
        assert time.get_season() == "autumn"
        assert time.get_day() == 61

        # Day 90
        time.total_hours = 89 * 24
        assert time.get_season() == "autumn"
        assert time.get_day() == 90

    # Spec: Days 91-120 are Winter
    def test_get_season_winter_days_91_120(self):
        """Days 91-120 return 'winter'."""
        time = GameTime()
        # Day 91
        time.total_hours = 90 * 24
        assert time.get_season() == "winter"
        assert time.get_day() == 91

        # Day 120
        time.total_hours = 119 * 24
        assert time.get_season() == "winter"
        assert time.get_day() == 120

    # Spec: Day 121 becomes Day 1 (year wraps)
    def test_day_wraps_after_120(self):
        """Day 121 wraps back to Day 1 (Spring)."""
        time = GameTime()
        time.total_hours = 120 * 24  # Day 121
        assert time.get_day() == 1
        assert time.get_season() == "spring"

    # Spec: Display format "Day X (Season)"
    def test_get_season_display(self):
        """get_season_display returns 'Day X (Season)' format."""
        time = GameTime()
        # Day 1 Spring
        assert time.get_season_display() == "Day 1 (Spring)"

        # Day 45 Summer
        time.total_hours = 44 * 24
        assert time.get_season_display() == "Day 45 (Summer)"

        # Day 75 Autumn
        time.total_hours = 74 * 24
        assert time.get_season_display() == "Day 75 (Autumn)"

        # Day 100 Winter
        time.total_hours = 99 * 24
        assert time.get_season_display() == "Day 100 (Winter)"

    # Spec: Season dread modifiers
    def test_season_dread_modifiers(self):
        """Seasons have correct dread modifiers: Winter +2, Autumn +1, Spring -1, Summer 0."""
        time = GameTime()

        # Spring: -1
        time.total_hours = 0
        assert time.get_season_dread_modifier() == -1

        # Summer: 0
        time.total_hours = 30 * 24
        assert time.get_season_dread_modifier() == 0

        # Autumn: +1
        time.total_hours = 60 * 24
        assert time.get_season_dread_modifier() == 1

        # Winter: +2
        time.total_hours = 90 * 24
        assert time.get_season_dread_modifier() == 2

    # Spec: total_hours persists in serialization
    def test_season_serialization(self):
        """to_dict/from_dict preserves total_hours."""
        time = GameTime()
        time.total_hours = 1500  # Some arbitrary value

        data = time.to_dict()
        assert "total_hours" in data
        assert data["total_hours"] == 1500

        restored = GameTime.from_dict(data)
        assert restored.total_hours == 1500
        assert restored.get_day() == time.get_day()
        assert restored.get_season() == time.get_season()

    # Spec: advance() accumulates total_hours
    def test_advance_accumulates_total_hours(self):
        """advance() increments total_hours correctly."""
        time = GameTime()
        assert time.total_hours == 0

        time.advance(10)
        assert time.total_hours == 10
        assert time.hour == 16  # 6 + 10

        time.advance(14)  # Wraps hour, adds to total
        assert time.total_hours == 24
        assert time.hour == 6  # (16 + 14) % 24 = 6


class TestFestivalSpawning:
    """Tests for festival event spawning."""

    # Spec: Spring Festival spawns on day 10
    def test_spring_festival_spawns_on_day_10(self):
        """Festival triggers at correct day (Spring Festival on day 10-12)."""
        from cli_rpg.seasons import check_for_festival

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # Set to day 10 (Spring)
        game_state.game_time.total_hours = 9 * 24  # Day 10

        message = check_for_festival(game_state)
        assert message is not None
        assert "Spring Festival" in message

    # Spec: Same festival doesn't spawn twice when already active
    def test_festival_not_duplicate_if_active(self):
        """Same festival doesn't spawn twice if already active."""
        from cli_rpg.seasons import check_for_festival
        from cli_rpg.models.world_event import WorldEvent

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # Set to day 10 (Spring Festival)
        game_state.game_time.total_hours = 9 * 24

        # First check spawns the festival
        message1 = check_for_festival(game_state)
        assert message1 is not None

        # Second check should not spawn duplicate
        message2 = check_for_festival(game_state)
        assert message2 is None

    # Spec: Festivals have 24-72 hour duration
    def test_festival_has_correct_duration(self):
        """Festival events have duration in 24-72 hour range."""
        from cli_rpg.seasons import check_for_festival

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # Spawn Spring Festival
        game_state.game_time.total_hours = 9 * 24  # Day 10
        check_for_festival(game_state)

        # Find the festival event
        festivals = [e for e in game_state.world_events if e.event_type == "festival"]
        assert len(festivals) == 1
        assert 24 <= festivals[0].duration_hours <= 72

    # Spec: Festival shows with [FESTIVAL] tag in events list
    def test_festival_appears_in_events_list(self):
        """Festival events show with [FESTIVAL] tag in events display."""
        from cli_rpg.seasons import check_for_festival
        from cli_rpg.world_events import get_active_events_display

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # Spawn festival
        game_state.game_time.total_hours = 9 * 24  # Day 10
        check_for_festival(game_state)

        display = get_active_events_display(game_state)
        assert "[FESTIVAL]" in display


class TestFestivalEffects:
    """Tests for festival gameplay effects."""

    # Spec: Spring Festival reduces shop prices by 20%
    def test_spring_festival_reduces_shop_prices(self):
        """Spring Festival applies 20% shop discount."""
        from cli_rpg.seasons import check_for_festival, get_festival_shop_discount

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # No festival - no discount
        discount = get_festival_shop_discount(game_state)
        assert discount == 0.0

        # Spawn Spring Festival
        game_state.game_time.total_hours = 9 * 24  # Day 10
        check_for_festival(game_state)

        discount = get_festival_shop_discount(game_state)
        assert discount == 0.20

    # Spec: Harvest Moon increases XP by 25%
    def test_harvest_moon_increases_xp(self):
        """Harvest Moon festival gives 25% XP bonus."""
        from cli_rpg.seasons import check_for_festival, get_festival_xp_multiplier

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # No festival - normal XP
        xp_mult = get_festival_xp_multiplier(game_state)
        assert xp_mult == 1.0

        # Spawn Harvest Moon (Autumn day 20-22)
        game_state.game_time.total_hours = 79 * 24  # Day 80 is Autumn but we need day 80 which is day 20 of Autumn
        # Day 80 = 79*24 total hours. Day 80 is (79*24 // 24 % 120) + 1 = 80. Season autumn (61-90).
        # Actually need day 80: 79*24 = 1896 hours, 1896/24 = 79, 79%120=79, +1 = 80. Autumn.
        # But spec says Harvest Moon on day 20-22, which in our system is day 80-82 (since days 61-90 are autumn, day 80 is the 20th day of autumn)
        # Wait, the plan says days 20-22 of Autumn, but our day system is 1-120 total.
        # Let me re-read: "Autumn, days 20-22" - this means overall days 80-82 since autumn is 61-90
        # Actually re-reading: "Spring Festival (Spring, days 10-12)" - this is overall days 10-12
        # So Harvest Moon (Autumn, days 20-22) would be... wait that's ambiguous.
        # Looking at Spring Festival: "days 10-12" in Spring means overall days 10-12
        # So Harvest Moon "days 20-22" probably means... within autumn? That would be days 80-82.
        # Let me interpret as: the day number is relative to the season start.
        # Spring days 10-12 = overall days 10-12
        # Harvest Moon Autumn days 20-22... hmm that's within autumn's 30 days, so 60+20=80 to 60+22=82

        # Actually simpler reading: the festival day ranges are absolute day numbers:
        # Spring Festival: days 10-12 (in Spring which is days 1-30) ✓
        # Midsummer Night: days 15-16 (in Summer which is 31-60, so days 45-46?) No that doesn't work.
        #
        # Let me re-read the plan more carefully:
        # "Spring Festival (Spring, days 10-12)" - day 10-12 of the year, which is in Spring ✓
        # "Midsummer Night (Summer, days 15-16)" - day 15-16 OF SUMMER = days 45-46 overall
        # "Harvest Moon (Autumn, days 20-22)" - day 20-22 OF AUTUMN = days 80-82 overall
        # "Winter Solstice (Winter, days 15-17)" - day 15-17 OF WINTER = days 105-107 overall
        #
        # That interpretation makes more sense! The day numbers are within that season.

        game_state.game_time.total_hours = 79 * 24  # Day 80 = 20th day of Autumn
        check_for_festival(game_state)

        xp_mult = get_festival_xp_multiplier(game_state)
        assert xp_mult == 1.25

    # Spec: Winter Solstice gives +25 HP on rest in town
    def test_winter_solstice_rest_bonus(self):
        """Winter Solstice gives +25 HP rest bonus in town."""
        from cli_rpg.seasons import check_for_festival, get_festival_rest_bonus

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # No festival - no bonus
        bonus = get_festival_rest_bonus(game_state)
        assert bonus == 0

        # Spawn Winter Solstice (Winter day 15-17 = overall days 105-107)
        game_state.game_time.total_hours = 104 * 24  # Day 105
        check_for_festival(game_state)

        bonus = get_festival_rest_bonus(game_state)
        assert bonus == 25

    # Spec: Midsummer Night increases whisper chance by 50%
    def test_midsummer_night_whisper_chance(self):
        """Midsummer Night increases whisper chance multiplier by 50%."""
        from cli_rpg.seasons import check_for_festival, get_festival_whisper_multiplier

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # No festival - normal chance
        whisper_mult = get_festival_whisper_multiplier(game_state)
        assert whisper_mult == 1.0

        # Spawn Midsummer Night (Summer day 15-16 = overall days 45-46)
        game_state.game_time.total_hours = 44 * 24  # Day 45
        check_for_festival(game_state)

        whisper_mult = get_festival_whisper_multiplier(game_state)
        assert whisper_mult == 1.5


class TestSeasonPersistence:
    """Tests for persistence of seasonal data."""

    # Spec: total_hours persists on save/load
    def test_total_hours_persists_on_save_load(self):
        """Season state (total_hours) survives save/load."""
        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0))
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # Set to specific day/season
        game_state.game_time.total_hours = 2000

        # Serialize and deserialize
        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        assert restored.game_time.total_hours == 2000
        assert restored.game_time.get_day() == game_state.game_time.get_day()
        assert restored.game_time.get_season() == game_state.game_time.get_season()

    # Spec: Active festival persists on save/load
    def test_active_festival_persists_on_save_load(self):
        """Festival events survive save/load."""
        from cli_rpg.seasons import check_for_festival

        char = Character(name="Test", strength=10, dexterity=10, intelligence=10)
        loc = Location(name="Town", description="A town", coordinates=(0, 0), category="town")
        world = {"Town": loc}
        game_state = GameState(char, world, starting_location="Town")

        # Spawn Spring Festival
        game_state.game_time.total_hours = 9 * 24  # Day 10
        check_for_festival(game_state)

        # Verify festival exists
        festivals = [e for e in game_state.world_events if e.event_type == "festival"]
        assert len(festivals) == 1
        assert "Spring Festival" in festivals[0].name

        # Serialize and deserialize
        data = game_state.to_dict()
        restored = GameState.from_dict(data)

        # Verify festival persisted
        restored_festivals = [e for e in restored.world_events if e.event_type == "festival"]
        assert len(restored_festivals) == 1
        assert "Spring Festival" in restored_festivals[0].name
