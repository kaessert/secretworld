"""Tests for location-specific encounter tables.

Tests for CATEGORY_ENEMIES, CATEGORY_ENCOUNTER_RATES, and CATEGORY_MERCHANT_ITEMS
as specified in Issue 21.
"""
import pytest

from cli_rpg.encounter_tables import (
    CATEGORY_ENEMIES,
    CATEGORY_ENCOUNTER_RATES,
    CATEGORY_MERCHANT_ITEMS,
    get_enemies_for_category,
    get_encounter_rate,
    get_merchant_items,
    DEFAULT_ENCOUNTER_RATE,
)


class TestCategoryEnemyTables:
    """Tests for category-specific enemy tables.

    Spec: Different enemy pools for dungeon, cave, ruins, forest, temple
    """

    def test_dungeon_enemies_exist(self):
        """CATEGORY_ENEMIES["dungeon"] has undead/construct enemies.

        Spec: Dungeon: undead, constructs, cultists
        """
        dungeon_enemies = CATEGORY_ENEMIES["dungeon"]
        assert len(dungeon_enemies) >= 4

        # Should contain undead-type enemies
        enemy_str = " ".join(dungeon_enemies).lower()
        assert any(term in enemy_str for term in ["skeleton", "zombie", "undead", "bone"])

    def test_cave_enemies_exist(self):
        """CATEGORY_ENEMIES["cave"] has beast/spider enemies.

        Spec: Cave: beasts, spiders, giant bats
        """
        cave_enemies = CATEGORY_ENEMIES["cave"]
        assert len(cave_enemies) >= 4

        # Should contain beast/spider-type enemies
        enemy_str = " ".join(cave_enemies).lower()
        assert any(term in enemy_str for term in ["spider", "bat", "bear", "beast", "goblin"])

    def test_ruins_enemies_exist(self):
        """CATEGORY_ENEMIES["ruins"] has ghost/golem enemies.

        Spec: Ruins: ghosts, treasure hunters, golems
        """
        ruins_enemies = CATEGORY_ENEMIES["ruins"]
        assert len(ruins_enemies) >= 4

        # Should contain ghost/golem-type enemies
        enemy_str = " ".join(ruins_enemies).lower()
        assert any(term in enemy_str for term in ["ghost", "golem", "phantom", "guardian"])

    def test_forest_enemies_exist(self):
        """CATEGORY_ENEMIES["forest"] has wolf/bandit/fey enemies.

        Spec: Forest: wolves, bandits, fey creatures
        """
        forest_enemies = CATEGORY_ENEMIES["forest"]
        assert len(forest_enemies) >= 4

        # Should contain wolf/bandit/fey-type enemies
        enemy_str = " ".join(forest_enemies).lower()
        assert any(term in enemy_str for term in ["wolf", "bandit", "boar", "dryad", "spirit"])

    def test_temple_enemies_exist(self):
        """CATEGORY_ENEMIES["temple"] has dark priest/animated statue enemies.

        Spec: Temple: dark priests, animated statues
        """
        temple_enemies = CATEGORY_ENEMIES["temple"]
        assert len(temple_enemies) >= 4

        # Should contain dark priest/statue-type enemies
        enemy_str = " ".join(temple_enemies).lower()
        assert any(term in enemy_str for term in ["priest", "statue", "guardian", "cultist"])

    def test_each_category_has_minimum_enemies(self):
        """Each category has at least 4 enemy types.

        Spec: All categories should have sufficient variety
        """
        required_categories = ["dungeon", "cave", "ruins", "forest", "temple"]
        for category in required_categories:
            assert category in CATEGORY_ENEMIES, f"Missing category: {category}"
            assert len(CATEGORY_ENEMIES[category]) >= 4, f"{category} has < 4 enemies"

    def test_get_enemies_for_category_valid(self):
        """`get_enemies_for_category("dungeon")` returns enemy list.

        Spec: Should return the list from CATEGORY_ENEMIES
        """
        enemies = get_enemies_for_category("dungeon")
        assert enemies == CATEGORY_ENEMIES["dungeon"]
        assert len(enemies) >= 4

    def test_get_enemies_for_category_fallback(self):
        """Unknown category returns default enemies.

        Spec: Should return a fallback list for unknown categories
        """
        enemies = get_enemies_for_category("unknown_category")
        assert isinstance(enemies, list)
        assert len(enemies) >= 1


class TestCategoryEncounterRates:
    """Tests for category-specific encounter rates.

    Spec: Variable encounter chances per category
    """

    def test_encounter_rates_exist(self):
        """CATEGORY_ENCOUNTER_RATES dict exists.

        Spec: Dict mapping categories to encounter probabilities
        """
        assert isinstance(CATEGORY_ENCOUNTER_RATES, dict)
        assert len(CATEGORY_ENCOUNTER_RATES) >= 5

    def test_dungeon_encounter_rate_higher(self):
        """Dungeon has higher rate than overworld.

        Spec: Dungeons are more dangerous
        """
        dungeon_rate = CATEGORY_ENCOUNTER_RATES.get("dungeon", 0)
        # Should be higher than default 0.15
        assert dungeon_rate > DEFAULT_ENCOUNTER_RATE

    def test_safe_categories_lower_rate(self):
        """Town/village have lower encounter rates.

        Spec: Safe areas have reduced encounter chance
        """
        town_rate = CATEGORY_ENCOUNTER_RATES.get("town", 1.0)
        village_rate = CATEGORY_ENCOUNTER_RATES.get("village", 1.0)
        # Should be lower than default 0.15
        assert town_rate < DEFAULT_ENCOUNTER_RATE
        assert village_rate < DEFAULT_ENCOUNTER_RATE

    def test_get_encounter_rate_valid(self):
        """`get_encounter_rate("dungeon")` returns correct rate.

        Spec: Should return the rate from CATEGORY_ENCOUNTER_RATES
        """
        rate = get_encounter_rate("dungeon")
        assert rate == CATEGORY_ENCOUNTER_RATES["dungeon"]

    def test_get_encounter_rate_default(self):
        """Unknown category returns default rate (0.15).

        Spec: Should return DEFAULT_ENCOUNTER_RATE for unknown categories
        """
        rate = get_encounter_rate("unknown_category")
        assert rate == DEFAULT_ENCOUNTER_RATE


class TestCategoryMerchantInventories:
    """Tests for category-specific merchant inventories.

    Spec: Merchants sell location-appropriate items
    """

    def test_merchant_items_exist(self):
        """CATEGORY_MERCHANT_ITEMS dict exists.

        Spec: Dict mapping categories to item templates
        """
        assert isinstance(CATEGORY_MERCHANT_ITEMS, dict)
        assert len(CATEGORY_MERCHANT_ITEMS) >= 3

    def test_dungeon_merchant_sells_healing(self):
        """Dungeon merchants favor healing items.

        Spec: Dungeon merchants should sell healing/survival items
        """
        items = CATEGORY_MERCHANT_ITEMS.get("dungeon", [])
        item_str = " ".join(items).lower()
        assert any(term in item_str for term in ["heal", "potion", "antidote"])

    def test_cave_merchant_sells_light(self):
        """Cave merchants sell torches/light items.

        Spec: Cave merchants should sell lighting/exploration items
        """
        items = CATEGORY_MERCHANT_ITEMS.get("cave", [])
        item_str = " ".join(items).lower()
        assert any(term in item_str for term in ["torch", "light", "rope"])

    def test_get_merchant_items_valid(self):
        """`get_merchant_items("dungeon")` returns item templates.

        Spec: Should return the list from CATEGORY_MERCHANT_ITEMS
        """
        items = get_merchant_items("dungeon")
        assert items == CATEGORY_MERCHANT_ITEMS["dungeon"]

    def test_get_merchant_items_fallback(self):
        """Unknown category returns default items.

        Spec: Should return a fallback list for unknown categories
        """
        items = get_merchant_items("unknown_category")
        assert isinstance(items, list)
        assert len(items) >= 1
