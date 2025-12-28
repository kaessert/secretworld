"""Integration tests for quest template content generation.

Tests ContentLayer.generate_quest_from_template() with AI mock and fallback,
quest chain generation, and determinism with same seed.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from cli_rpg.content_layer import ContentLayer
from cli_rpg.procedural_quests import (
    QuestTemplate,
    QuestTemplateType,
    QUEST_TEMPLATES,
    QUEST_CHAINS,
    select_quest_template,
    generate_quest_chain,
)
from cli_rpg.fallback_content import FallbackContentProvider, QUEST_TARGET_POOLS
from cli_rpg.models.quest import Quest, ObjectiveType, QuestDifficulty


class TestContentLayerGenerateQuestFromTemplate:
    """Tests for ContentLayer.generate_quest_from_template()."""

    def test_generates_quest_with_fallback(self):
        """Generate quest from template using fallback content (no AI)."""
        # Phase 1: Select a template from QUEST_TEMPLATES
        template = select_quest_template("dungeon", seed=42)

        # Phase 2: Use ContentLayer to generate quest
        content_layer = ContentLayer()
        quest = content_layer.generate_quest_from_template(
            template=template,
            category="dungeon",
            player_level=5,
            danger_level=2,
            npc_name="Test Quest Giver",
            coords=(0, 0, 0),
            ai_service=None,  # No AI, use fallback
            generation_context=None,
            seed=12345,
        )

        assert isinstance(quest, Quest)
        assert len(quest.name) >= 2  # Meets Quest.MIN_NAME_LENGTH
        assert len(quest.name) <= 30  # Meets Quest.MAX_NAME_LENGTH
        assert len(quest.description) >= 1
        assert quest.objective_type == template.objective_type
        assert quest.gold_reward > 0
        assert quest.xp_reward > 0
        assert quest.quest_giver == "Test Quest Giver"

    def test_fallback_content_is_deterministic(self):
        """Same seed should produce same quest content."""
        template = select_quest_template("cave", seed=100)
        content_layer = ContentLayer()

        quest1 = content_layer.generate_quest_from_template(
            template=template,
            category="cave",
            player_level=3,
            danger_level=1,
            npc_name="NPC",
            coords=(1, 2, 3),
            ai_service=None,
            generation_context=None,
            seed=99999,
        )

        quest2 = content_layer.generate_quest_from_template(
            template=template,
            category="cave",
            player_level=3,
            danger_level=1,
            npc_name="NPC",
            coords=(1, 2, 3),
            ai_service=None,
            generation_context=None,
            seed=99999,
        )

        assert quest1.name == quest2.name
        assert quest1.description == quest2.description
        assert quest1.target == quest2.target

    def test_different_seeds_can_produce_different_quests(self):
        """Different seeds should (eventually) produce different quests."""
        template = select_quest_template("town", seed=1)
        content_layer = ContentLayer()

        quests = set()
        for seed in range(50):
            quest = content_layer.generate_quest_from_template(
                template=template,
                category="town",
                player_level=1,
                danger_level=1,
                npc_name="NPC",
                coords=(0, 0, 0),
                ai_service=None,
                generation_context=None,
                seed=seed,
            )
            quests.add(quest.name)

        # Should see some variety in quest names
        assert len(quests) > 1

    def test_quest_has_scaled_values(self):
        """Quest should have properly scaled difficulty, rewards, etc."""
        template = QuestTemplate(
            template_type=QuestTemplateType.KILL_BOSS,
            objective_type=ObjectiveType.KILL,
            base_target_count=1,
            difficulty_scaling=2.0,
            base_gold_reward=100,
            base_xp_reward=50,
            category_tags=["dungeon"],
        )
        content_layer = ContentLayer()

        # Low level quest
        low_quest = content_layer.generate_quest_from_template(
            template=template,
            category="dungeon",
            player_level=1,
            danger_level=1,
            npc_name="NPC",
            coords=(0, 0, 0),
            ai_service=None,
            generation_context=None,
            seed=42,
        )

        # High level quest
        high_quest = content_layer.generate_quest_from_template(
            template=template,
            category="dungeon",
            player_level=10,
            danger_level=3,
            npc_name="NPC",
            coords=(0, 0, 0),
            ai_service=None,
            generation_context=None,
            seed=42,
        )

        # Higher level should have higher rewards
        assert high_quest.gold_reward > low_quest.gold_reward
        assert high_quest.xp_reward > low_quest.xp_reward

    def test_generates_quest_with_mock_ai(self):
        """Generate quest from template using mock AI service."""
        template = select_quest_template("ruins", seed=42)
        content_layer = ContentLayer()

        # Mock AI service
        mock_ai = MagicMock()
        mock_ai.generate_quest_from_template.return_value = {
            "name": "AI Quest Name",
            "description": "AI-generated quest description.",
            "target": "AI Target",
        }

        quest = content_layer.generate_quest_from_template(
            template=template,
            category="ruins",
            player_level=5,
            danger_level=2,
            npc_name="AI NPC",
            coords=(0, 0, 0),
            ai_service=mock_ai,
            generation_context=None,
            seed=42,
        )

        assert quest.name == "AI Quest Name"
        assert quest.description == "AI-generated quest description."
        assert quest.target == "AI Target"

    def test_falls_back_when_ai_fails(self):
        """Falls back to template content when AI raises exception."""
        template = select_quest_template("temple", seed=42)
        content_layer = ContentLayer()

        # Mock AI service that fails
        mock_ai = MagicMock()
        mock_ai.generate_quest_from_template.side_effect = Exception("AI error")

        quest = content_layer.generate_quest_from_template(
            template=template,
            category="temple",
            player_level=3,
            danger_level=1,
            npc_name="Fallback NPC",
            coords=(0, 0, 0),
            ai_service=mock_ai,
            generation_context=None,
            seed=42,
        )

        # Should still get a valid quest from fallback
        assert isinstance(quest, Quest)
        assert len(quest.name) >= 2

    def test_falls_back_when_ai_returns_incomplete(self):
        """Falls back when AI returns incomplete content."""
        template = select_quest_template("cave", seed=42)
        content_layer = ContentLayer()

        # Mock AI that returns incomplete data
        mock_ai = MagicMock()
        mock_ai.generate_quest_from_template.return_value = {
            "name": "Only Name",
            # Missing description and target
        }

        quest = content_layer.generate_quest_from_template(
            template=template,
            category="cave",
            player_level=3,
            danger_level=1,
            npc_name="NPC",
            coords=(0, 0, 0),
            ai_service=mock_ai,
            generation_context=None,
            seed=42,
        )

        # Should fall back and still generate valid quest
        assert isinstance(quest, Quest)
        assert quest.description is not None


class TestFallbackContentProviderQuestTarget:
    """Tests for FallbackContentProvider.get_quest_target()."""

    def test_get_quest_target_returns_string(self):
        """get_quest_target returns a non-empty string."""
        provider = FallbackContentProvider(seed=42)
        target = provider.get_quest_target("kill_boss", "dungeon")

        assert isinstance(target, str)
        assert len(target) > 0

    def test_get_quest_target_is_deterministic(self):
        """Same seed produces same target."""
        target1 = FallbackContentProvider(seed=123).get_quest_target("collect", "cave")
        target2 = FallbackContentProvider(seed=123).get_quest_target("collect", "cave")

        assert target1 == target2

    def test_get_quest_target_uses_category(self):
        """Different categories can produce different targets."""
        targets = set()
        for category in ["dungeon", "cave", "ruins", "temple"]:
            provider = FallbackContentProvider(seed=42)
            target = provider.get_quest_target("explore", category)
            targets.add(target)

        # Different categories should have different possible targets
        assert len(targets) > 1

    def test_get_quest_target_falls_back_to_default(self):
        """Unknown category falls back to default targets."""
        provider = FallbackContentProvider(seed=42)
        target = provider.get_quest_target("kill_boss", "unknown_category")

        # Should get a target from the "default" pool
        default_targets = QUEST_TARGET_POOLS["kill_boss"]["default"]
        assert target in default_targets

    def test_all_template_types_have_targets(self):
        """All QuestTemplateType values have target pools."""
        template_types = [
            "kill_boss", "kill_mobs", "collect", "explore", "talk", "escort", "fetch"
        ]

        for template_type in template_types:
            assert template_type in QUEST_TARGET_POOLS


class TestQuestChainGeneration:
    """Tests for quest chain generation via generate_quest_chain()."""

    def test_chain_quests_have_correct_structure(self):
        """Generated chain quests have proper chain_id and positions."""
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests = generate_quest_chain(chain_id, player_level=5, seed=42)

        assert len(quests) >= 2

        for i, quest in enumerate(quests):
            assert quest.chain_id == chain_id
            assert quest.chain_position == i + 1

    def test_chain_quests_link_correctly(self):
        """Chain quests have proper prerequisite/unlock links."""
        chain_id = next(iter(QUEST_CHAINS.keys()))
        quests = generate_quest_chain(chain_id, player_level=5, seed=42)

        # First quest has no prerequisites
        assert len(quests[0].prerequisite_quests) == 0

        # Each quest after first requires the previous
        for i in range(1, len(quests)):
            assert quests[i - 1].name in quests[i].prerequisite_quests

        # Each quest except last unlocks the next
        for i in range(len(quests) - 1):
            assert quests[i + 1].name in quests[i].unlocks_quests

        # Last quest has no unlocks
        assert len(quests[-1].unlocks_quests) == 0

    def test_chain_with_content_callback(self):
        """Chain generation uses content callback when provided."""
        chain_id = next(iter(QUEST_CHAINS.keys()))

        callback_calls = []

        def mock_callback(template_type, category, seed):
            callback_calls.append((template_type, category, seed))
            return {
                "name": f"Custom {template_type.value}",
                "description": "Custom description.",
                "target": "Custom Target",
            }

        quests = generate_quest_chain(
            chain_id,
            player_level=5,
            seed=42,
            content_callback=mock_callback,
        )

        # Callback should have been called for each quest in chain
        assert len(callback_calls) == len(quests)

        # Quests should have custom names
        for quest in quests:
            assert quest.name.startswith("Custom ")


class TestQuestTemplateContentRequestModel:
    """Tests for the QuestTemplateContentRequest dataclass."""

    def test_create_request(self):
        """Test creating a QuestTemplateContentRequest."""
        from cli_rpg.models.content_request import QuestTemplateContentRequest

        request = QuestTemplateContentRequest(
            template_type="kill_boss",
            category="dungeon",
            player_level=5,
            npc_name="Quest Giver",
            coordinates=(1, 2, 3),
        )

        assert request.template_type == "kill_boss"
        assert request.category == "dungeon"
        assert request.player_level == 5
        assert request.npc_name == "Quest Giver"
        assert request.coordinates == (1, 2, 3)


class TestEndToEndQuestFlow:
    """End-to-end tests for the full quest generation flow."""

    def test_full_flow_dungeon_quest(self):
        """Full flow: select template -> generate quest -> validate."""
        # Step 1: Select a template
        template = select_quest_template("dungeon", seed=42)

        # Step 2: Create ContentLayer and generate quest
        content_layer = ContentLayer()
        quest = content_layer.generate_quest_from_template(
            template=template,
            category="dungeon",
            player_level=5,
            danger_level=2,
            npc_name="Dungeon Guide",
            coords=(0, 0, -1),  # Below ground
            ai_service=None,
            generation_context=None,
            seed=12345,
        )

        # Step 3: Validate quest structure
        assert isinstance(quest, Quest)
        assert quest.quest_giver == "Dungeon Guide"
        assert quest.objective_type in [ObjectiveType.KILL, ObjectiveType.COLLECT, ObjectiveType.EXPLORE]
        assert quest.gold_reward > 0
        assert quest.xp_reward > 0
        assert quest.difficulty in list(QuestDifficulty)
        assert quest.recommended_level >= 1

    def test_all_categories_generate_valid_quests(self):
        """All categories in QUEST_TEMPLATES can generate valid quests."""
        content_layer = ContentLayer()

        for category in QUEST_TEMPLATES.keys():
            template = select_quest_template(category, seed=42)
            quest = content_layer.generate_quest_from_template(
                template=template,
                category=category,
                player_level=3,
                danger_level=1,
                npc_name="Test NPC",
                coords=(0, 0, 0),
                ai_service=None,
                generation_context=None,
                seed=42,
            )

            assert isinstance(quest, Quest), f"Failed for category: {category}"
            assert quest.name, f"No name for category: {category}"
            assert quest.description, f"No description for category: {category}"

    def test_all_chains_generate_valid_quests(self):
        """All chains in QUEST_CHAINS generate valid quest lists."""
        for chain_id in QUEST_CHAINS.keys():
            quests = generate_quest_chain(chain_id, player_level=5, seed=42)

            assert len(quests) >= 2, f"Chain {chain_id} too short"
            for quest in quests:
                assert isinstance(quest, Quest), f"Invalid quest in chain: {chain_id}"
                assert quest.chain_id == chain_id
