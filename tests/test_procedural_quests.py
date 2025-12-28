"""Tests for procedural quest generation system.

Tests the QuestTemplateType enum, QuestTemplate dataclass, template selection,
difficulty scaling, and QUEST_TEMPLATES coverage.
"""

import pytest
from cli_rpg.procedural_quests import (
    QuestTemplateType,
    QuestTemplate,
    QUEST_TEMPLATES,
    QUEST_CHAINS,
    select_quest_template,
    scale_quest_difficulty,
    generate_quest_chain,
)
from cli_rpg.models.quest import ObjectiveType, QuestDifficulty


class TestQuestTemplateType:
    """Tests for QuestTemplateType enum."""

    def test_all_template_types_exist(self):
        """Verify all expected template types are defined."""
        expected_types = [
            "KILL_BOSS",
            "KILL_MOBS",
            "COLLECT_ITEMS",
            "EXPLORE_AREA",
            "TALK_NPC",
            "ESCORT",
            "FETCH",
        ]
        for type_name in expected_types:
            assert hasattr(QuestTemplateType, type_name)

    def test_template_type_values(self):
        """Verify template type values match expected strings."""
        assert QuestTemplateType.KILL_BOSS.value == "kill_boss"
        assert QuestTemplateType.KILL_MOBS.value == "kill_mobs"
        assert QuestTemplateType.COLLECT_ITEMS.value == "collect"
        assert QuestTemplateType.EXPLORE_AREA.value == "explore"
        assert QuestTemplateType.TALK_NPC.value == "talk"
        assert QuestTemplateType.ESCORT.value == "escort"
        assert QuestTemplateType.FETCH.value == "fetch"

    def test_template_type_count(self):
        """Verify we have exactly 7 template types."""
        assert len(QuestTemplateType) == 7


class TestQuestTemplate:
    """Tests for QuestTemplate dataclass."""

    def test_create_basic_template(self):
        """Test creating a basic quest template."""
        template = QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=1.5,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["dungeon", "ruins"],
        )

        assert template.template_type == QuestTemplateType.KILL_BOSS
        assert template.objective_type == ObjectiveType.KILL
        assert template.base_target_count == 1
        assert template.difficulty_scaling == 1.5
        assert template.base_gold_reward == 100
        assert template.base_xp_reward == 50
        assert template.category_tags == ["dungeon", "ruins"]
        assert template.chain_position == 0  # Default

    def test_template_with_chain_position(self):
        """Test creating a template with chain position."""
        template = QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=1.0,
            base_gold_reward=50,
            base_xp_reward=25,
            category_tags=["town"],
            chain_position=2,
        )

        assert template.chain_position == 2

    def test_all_objective_types_mappable(self):
        """Verify each template type maps to a valid ObjectiveType."""
        type_to_objective = {
            QuestTemplateType.KILL_BOSS: ObjectiveType.KILL,
            QuestTemplateType.KILL_MOBS: ObjectiveType.KILL,
            QuestTemplateType.COLLECT_ITEMS: ObjectiveType.COLLECT,
            QuestTemplateType.EXPLORE_AREA: ObjectiveType.EXPLORE,
            QuestTemplateType.TALK_NPC: ObjectiveType.TALK,
            QuestTemplateType.ESCORT: ObjectiveType.EXPLORE,  # Escort uses explore mechanics
            QuestTemplateType.FETCH: ObjectiveType.COLLECT,  # Fetch uses collect mechanics
        }

        for template_type, expected_objective in type_to_objective.items():
            template = QuestTemplate(
                template_type=template_type,
                objective_type=expected_objective,
                base_target_count=1,
                difficulty_scaling=1.0,
                base_gold_reward=50,
                base_xp_reward=25,
                category_tags=["default"],
            )
            assert template.objective_type == expected_objective


class TestQuestTemplates:
    """Tests for QUEST_TEMPLATES dictionary coverage."""

    def test_required_categories_exist(self):
        """Verify all required location categories have templates."""
        required_categories = ["dungeon", "cave", "ruins", "temple", "town", "village"]
        for category in required_categories:
            assert category in QUEST_TEMPLATES, f"Missing category: {category}"
            assert len(QUEST_TEMPLATES[category]) > 0, f"Empty templates for: {category}"

    def test_each_category_has_multiple_templates(self):
        """Each category should have at least 2 templates for variety."""
        for category, templates in QUEST_TEMPLATES.items():
            assert len(templates) >= 2, f"Category {category} needs more templates"

    def test_dungeon_templates_include_expected_types(self):
        """Dungeon should have KILL_BOSS, EXPLORE_AREA, COLLECT_ITEMS."""
        dungeon_types = {t.template_type for t in QUEST_TEMPLATES["dungeon"]}
        assert QuestTemplateType.KILL_BOSS in dungeon_types
        assert QuestTemplateType.EXPLORE_AREA in dungeon_types
        assert QuestTemplateType.COLLECT_ITEMS in dungeon_types

    def test_cave_templates_include_expected_types(self):
        """Cave should have KILL_MOBS, COLLECT_ITEMS, TALK_NPC."""
        cave_types = {t.template_type for t in QUEST_TEMPLATES["cave"]}
        assert QuestTemplateType.KILL_MOBS in cave_types
        assert QuestTemplateType.COLLECT_ITEMS in cave_types
        assert QuestTemplateType.TALK_NPC in cave_types

    def test_town_templates_include_expected_types(self):
        """Town should have FETCH, TALK_NPC, ESCORT."""
        town_types = {t.template_type for t in QUEST_TEMPLATES["town"]}
        assert QuestTemplateType.FETCH in town_types
        assert QuestTemplateType.TALK_NPC in town_types
        assert QuestTemplateType.ESCORT in town_types

    def test_all_templates_have_valid_objective_types(self):
        """All templates should have valid ObjectiveType values."""
        for category, templates in QUEST_TEMPLATES.items():
            for template in templates:
                assert isinstance(template.objective_type, ObjectiveType)


class TestSelectQuestTemplate:
    """Tests for select_quest_template() function."""

    def test_select_returns_valid_template(self):
        """Select should return a QuestTemplate from the category."""
        template = select_quest_template("dungeon", seed=42)
        assert isinstance(template, QuestTemplate)
        assert "dungeon" in template.category_tags

    def test_select_is_deterministic(self):
        """Same seed should produce same template."""
        template1 = select_quest_template("dungeon", seed=12345)
        template2 = select_quest_template("dungeon", seed=12345)
        assert template1.template_type == template2.template_type

    def test_different_seeds_can_produce_different_templates(self):
        """Different seeds should (eventually) produce different templates."""
        templates = set()
        for seed in range(100):
            template = select_quest_template("dungeon", seed=seed)
            templates.add(template.template_type)

        # With 3+ templates and 100 seeds, we should see variety
        assert len(templates) > 1

    def test_unknown_category_falls_back(self):
        """Unknown category should fall back to default templates."""
        template = select_quest_template("unknown_category", seed=42)
        assert isinstance(template, QuestTemplate)

    def test_each_category_selectable(self):
        """Each category should be selectable without error."""
        for category in QUEST_TEMPLATES.keys():
            template = select_quest_template(category, seed=42)
            assert isinstance(template, QuestTemplate)


class TestScaleQuestDifficulty:
    """Tests for scale_quest_difficulty() function."""

    def test_level_1_trivial_difficulty(self):
        """Level 1 with danger 1 and low scaling should produce trivial difficulty.

        Difficulty score = 1 * 1 * 1.0 = 1, which is < 3 so TRIVIAL.
        """
        template = QuestTemplate(
            template_type=QuestTemplateType.KILL_MOBS,
            objective_type=ObjectiveType.KILL,
            base_target_count=5,
            difficulty_scaling=1.0,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["dungeon"],
        )

        result = scale_quest_difficulty(template, player_level=1, danger_level=1)

        assert result["difficulty"] == QuestDifficulty.TRIVIAL
        assert result["target_count"] == 5  # base + (1 // 3) = 5 + 0 = 5
        # With trivial difficulty multiplier (0.5), gold = 100 * 1.1 * 0.5 = 55
        assert result["gold_reward"] >= 50
        assert result["xp_reward"] >= 25

    def test_higher_level_increases_target_count(self):
        """Higher player level should increase target count."""
        template = QuestTemplate(
            template_type=QuestTemplateType.KILL_MOBS,
            objective_type=ObjectiveType.KILL,
            base_target_count=5,
            difficulty_scaling=1.0,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["dungeon"],
        )

        result_low = scale_quest_difficulty(template, player_level=1, danger_level=1)
        result_high = scale_quest_difficulty(template, player_level=10, danger_level=1)

        # Level 10: 5 + (10 // 3) = 5 + 3 = 8
        assert result_high["target_count"] > result_low["target_count"]

    def test_higher_level_increases_rewards(self):
        """Higher player level should increase gold and xp rewards."""
        template = QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.0,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["ruins"],
        )

        result_low = scale_quest_difficulty(template, player_level=1, danger_level=1)
        result_high = scale_quest_difficulty(template, player_level=10, danger_level=1)

        assert result_high["gold_reward"] > result_low["gold_reward"]
        assert result_high["xp_reward"] > result_low["xp_reward"]

    def test_high_danger_increases_difficulty(self):
        """Higher danger level should increase difficulty rating."""
        template = QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.0,  # High scaling
            base_gold_reward=200,
            base_xp_reward=100,
            category_tags=["dungeon"],
        )

        result_low_danger = scale_quest_difficulty(template, player_level=5, danger_level=1)
        result_high_danger = scale_quest_difficulty(template, player_level=5, danger_level=3)

        # Higher danger should result in harder difficulty or same
        danger_order = [
            QuestDifficulty.TRIVIAL,
            QuestDifficulty.EASY,
            QuestDifficulty.NORMAL,
            QuestDifficulty.HARD,
            QuestDifficulty.DEADLY,
        ]
        low_idx = danger_order.index(result_low_danger["difficulty"])
        high_idx = danger_order.index(result_high_danger["difficulty"])
        assert high_idx >= low_idx

    def test_difficulty_scaling_affects_result(self):
        """Template's difficulty_scaling should affect final difficulty."""
        easy_template = QuestTemplate(
            template_type=QuestTemplateType.TALK_NPC,
            objective_type=ObjectiveType.TALK,
            base_target_count=1,
            difficulty_scaling=0.5,  # Easy
            base_gold_reward=50,
            base_xp_reward=25,
            category_tags=["town"],
        )

        hard_template = QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.5,  # Hard
            base_gold_reward=300,
            base_xp_reward=150,
            category_tags=["dungeon"],
        )

        easy_result = scale_quest_difficulty(easy_template, player_level=5, danger_level=2)
        hard_result = scale_quest_difficulty(hard_template, player_level=5, danger_level=2)

        # Hard template should have higher rewards (from higher scaling multiplier)
        assert hard_result["gold_reward"] > easy_result["gold_reward"]

    def test_returns_recommended_level(self):
        """Result should include recommended_level."""
        template = QuestTemplate(
            template_type=QuestTemplateType.EXPLORE_AREA,
            objective_type=ObjectiveType.EXPLORE,
            base_target_count=1,
            difficulty_scaling=1.0,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["ruins"],
        )

        result = scale_quest_difficulty(template, player_level=5, danger_level=2)

        assert "recommended_level" in result
        assert result["recommended_level"] >= 1


class TestQuestChains:
    """Tests for QUEST_CHAINS dictionary and chain generation."""

    def test_quest_chains_exist(self):
        """QUEST_CHAINS should have at least one chain defined."""
        assert len(QUEST_CHAINS) > 0

    def test_chains_have_multiple_steps(self):
        """Each chain should have at least 2 templates (forming a chain)."""
        for chain_id, chain_templates in QUEST_CHAINS.items():
            assert len(chain_templates) >= 2, f"Chain {chain_id} needs 2+ steps"

    def test_chain_positions_are_sequential(self):
        """Chain positions should be sequential starting from 1."""
        for chain_id, chain_templates in QUEST_CHAINS.items():
            positions = [t.chain_position for t in chain_templates]
            expected = list(range(1, len(chain_templates) + 1))
            assert sorted(positions) == expected, f"Chain {chain_id} has bad positions"


class TestGenerateQuestChain:
    """Tests for generate_quest_chain() function."""

    def test_generate_chain_returns_quest_list(self):
        """Generate chain should return a list of Quest objects."""
        from cli_rpg.models.quest import Quest

        # Get first chain_id from QUEST_CHAINS
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests = generate_quest_chain(chain_id, player_level=5, seed=42)

        assert isinstance(quests, list)
        assert len(quests) > 0
        for quest in quests:
            assert isinstance(quest, Quest)

    def test_generated_chain_has_prerequisites(self):
        """Generated quests should have proper prerequisite links."""
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests = generate_quest_chain(chain_id, player_level=5, seed=42)

        if len(quests) > 1:
            # First quest should have no prerequisites
            assert len(quests[0].prerequisite_quests) == 0

            # Subsequent quests should require previous quest
            for i in range(1, len(quests)):
                assert quests[i - 1].name in quests[i].prerequisite_quests

    def test_generated_chain_has_unlocks(self):
        """Generated quests should have proper unlocks_quests links."""
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests = generate_quest_chain(chain_id, player_level=5, seed=42)

        if len(quests) > 1:
            # Each quest except last should unlock the next
            for i in range(len(quests) - 1):
                assert quests[i + 1].name in quests[i].unlocks_quests

            # Last quest should have no unlocks (empty list)
            assert len(quests[-1].unlocks_quests) == 0

    def test_generated_chain_has_chain_id(self):
        """All quests in chain should share the same chain_id."""
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests = generate_quest_chain(chain_id, player_level=5, seed=42)

        for quest in quests:
            assert quest.chain_id == chain_id

    def test_chain_is_deterministic(self):
        """Same seed should produce same chain."""
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests1 = generate_quest_chain(chain_id, player_level=5, seed=12345)
        quests2 = generate_quest_chain(chain_id, player_level=5, seed=12345)

        assert len(quests1) == len(quests2)
        for q1, q2 in zip(quests1, quests2):
            assert q1.name == q2.name
            assert q1.description == q2.description

    def test_unknown_chain_returns_empty(self):
        """Unknown chain_id should return empty list."""
        quests = generate_quest_chain("nonexistent_chain", player_level=5, seed=42)
        assert quests == []
