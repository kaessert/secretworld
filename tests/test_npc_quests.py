"""Tests for NPC quest-giver functionality.

Tests the ability for players to acquire quests by talking to NPCs.
Spec: Quest Acquisition from NPCs.
"""
from cli_rpg.models.npc import NPC
from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType
from cli_rpg.models.character import Character
from cli_rpg.models.location import Location
from cli_rpg.game_state import GameState, parse_command


class TestNPCQuestGiver:
    """Tests for NPC quest-giver capability - parallel to merchant pattern."""

    def test_npc_quest_giver_default_false(self):
        """NPC defaults to not being a quest giver."""
        npc = NPC(name="Guard", description="A town guard", dialogue="Move along.")
        assert npc.is_quest_giver is False
        assert npc.offered_quests == []

    def test_create_quest_giver_npc(self):
        """NPC can be created as a quest giver with offered quests."""
        quest = Quest(
            name="Kill Goblins",
            description="Defeat the goblins in the forest.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            target_count=5
        )
        npc = NPC(
            name="Captain",
            description="The town guard captain",
            dialogue="We need your help!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        assert npc.is_quest_giver is True
        assert len(npc.offered_quests) == 1
        assert npc.offered_quests[0].name == "Kill Goblins"

    def test_npc_quest_giver_serialization(self):
        """NPC with offered quests can be serialized to dict."""
        quest = Quest(
            name="Collect Herbs",
            description="Gather healing herbs.",
            objective_type=ObjectiveType.COLLECT,
            target="healing herb",
            target_count=3
        )
        npc = NPC(
            name="Healer",
            description="The village healer",
            dialogue="Please help me gather herbs.",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        data = npc.to_dict()

        assert data["is_quest_giver"] is True
        assert "offered_quests" in data
        assert len(data["offered_quests"]) == 1
        assert data["offered_quests"][0]["name"] == "Collect Herbs"

    def test_npc_quest_giver_deserialization(self):
        """NPC with offered quests can be deserialized from dict."""
        quest = Quest(
            name="Explore Dungeon",
            description="Map the dungeon entrance.",
            objective_type=ObjectiveType.EXPLORE,
            target="dungeon",
        )
        npc = NPC(
            name="Scholar",
            description="A curious scholar",
            dialogue="The dungeon holds many secrets.",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        data = npc.to_dict()
        restored = NPC.from_dict(data)

        assert restored.is_quest_giver is True
        assert len(restored.offered_quests) == 1
        assert restored.offered_quests[0].name == "Explore Dungeon"
        assert restored.offered_quests[0].objective_type == ObjectiveType.EXPLORE

    def test_npc_not_quest_giver_backward_compatibility(self):
        """Old NPC data without quest_giver fields can be deserialized."""
        # Simulate old format data
        old_data = {
            "name": "Merchant",
            "description": "A shopkeeper",
            "dialogue": "Hello!",
            "is_merchant": False,
            "shop": None
        }
        npc = NPC.from_dict(old_data)
        assert npc.is_quest_giver is False
        assert npc.offered_quests == []


class TestCharacterHasQuest:
    """Tests for Character.has_quest() method."""

    def test_has_quest_returns_false_when_empty(self):
        """Character with no quests returns False for has_quest."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        assert character.has_quest("Any Quest") is False

    def test_has_quest_returns_true_for_matching_quest(self):
        """Character returns True if they have the quest."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            status=QuestStatus.ACTIVE
        )
        character.quests.append(quest)
        assert character.has_quest("Kill Goblins") is True

    def test_has_quest_case_insensitive(self):
        """has_quest check is case-insensitive."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        character.quests.append(quest)
        assert character.has_quest("kill goblins") is True
        assert character.has_quest("KILL GOBLINS") is True

    def test_has_quest_returns_false_for_different_quest(self):
        """Character returns False for a quest they don't have."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        character.quests.append(quest)
        assert character.has_quest("Collect Herbs") is False


class TestGameStateCurrentNPC:
    """Tests for GameState.current_npc field."""

    def test_game_state_current_npc_default_none(self):
        """GameState.current_npc defaults to None."""
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        location = Location(name="Town", description="A town.", coordinates=(0, 0))
        game_state = GameState(character, {"Town": location}, "Town")
        assert game_state.current_npc is None


class TestTalkCommandShowsQuests:
    """Tests for talk command showing available quests."""

    def test_talk_to_quest_giver_shows_available_quests(self):
        """Talking to a quest giver NPC shows their available quests."""
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        _, output = handle_exploration_command(game_state, "talk", ["Captain"])

        assert "We need heroes!" in output  # Dialogue shown
        assert "Available Quests:" in output
        assert "Kill Goblins" in output
        assert "accept" in output.lower()

    def test_talk_to_quest_giver_hides_already_acquired_quests(self):
        """Quests already acquired by the player are not shown as available."""
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Player already has the quest
        player_quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            status=QuestStatus.ACTIVE
        )
        character.quests.append(player_quest)

        game_state = GameState(character, {"Town": location}, "Town")

        _, output = handle_exploration_command(game_state, "talk", ["Captain"])

        assert "We need heroes!" in output  # Dialogue still shown
        assert "Available Quests:" not in output  # No quests to show

    def test_talk_sets_current_npc(self):
        """Talking to an NPC sets game_state.current_npc."""
        from cli_rpg.main import handle_exploration_command

        npc = NPC(
            name="Guard",
            description="A guard",
            dialogue="Halt!",
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        handle_exploration_command(game_state, "talk", ["Guard"])

        assert game_state.current_npc is not None
        assert game_state.current_npc.name == "Guard"


class TestAcceptCommand:
    """Tests for the accept command."""

    def test_accept_command_parsed(self):
        """Accept command is recognized by parse_command."""
        command, args = parse_command("accept Kill Goblins")
        assert command == "accept"
        # parse_command lowercases all input
        assert args == ["kill", "goblins"]

    def test_accept_requires_npc_context(self):
        """Accept command fails without talking to an NPC first."""
        from cli_rpg.main import handle_exploration_command

        location = Location(name="Town", description="A town.", coordinates=(0, 0))
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        _, output = handle_exploration_command(game_state, "accept", ["Quest"])

        assert "talk to an NPC first" in output.lower() or "npc first" in output.lower()

    def test_accept_auto_accepts_single_quest(self):
        """Bare 'accept' auto-accepts when NPC offers exactly one available quest.

        Spec: When player types 'accept' without arguments while talking to an NPC
        with exactly one available quest, auto-accept that quest.
        """
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            target_count=5
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Bare accept should auto-accept the single quest
        _, output = handle_exploration_command(game_state, "accept", [])

        assert len(character.quests) == 1
        assert character.quests[0].name == "Kill Goblins"
        assert character.quests[0].status == QuestStatus.ACTIVE
        assert "Kill Goblins" in output

    def test_accept_lists_quests_when_multiple(self):
        """Bare 'accept' shows available quests when NPC has 2+ quests.

        Spec: When NPC has 2+ available quests, show "Accept what? Available: Quest1, Quest2".
        """
        from cli_rpg.main import handle_exploration_command

        quest1 = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        quest2 = Quest(
            name="Collect Herbs",
            description="Gather herbs.",
            objective_type=ObjectiveType.COLLECT,
            target="herb"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest1, quest2]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Bare accept should list available quests
        _, output = handle_exploration_command(game_state, "accept", [])

        assert len(character.quests) == 0  # No quest accepted
        assert "Accept what?" in output
        assert "Kill Goblins" in output
        assert "Collect Herbs" in output

    def test_accept_no_quests_shows_none(self):
        """Bare 'accept' shows no quests message when NPC isn't a quest giver.

        Spec: When NPC has 0 available quests, show "X doesn't offer any quests."
        """
        from cli_rpg.main import handle_exploration_command

        npc = NPC(name="Guard", description="A guard", dialogue="Halt!")
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Guard"])

        # Bare accept should show no quests message
        _, output = handle_exploration_command(game_state, "accept", [])

        assert len(character.quests) == 0
        assert "doesn't offer any quests" in output.lower()

    def test_accept_auto_accepts_only_available_quest(self):
        """Bare 'accept' auto-accepts when NPC has multiple quests but only one available.

        Spec: Available quests = quests the player doesn't already have.
        """
        from cli_rpg.main import handle_exploration_command

        quest1 = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        quest2 = Quest(
            name="Collect Herbs",
            description="Gather herbs.",
            objective_type=ObjectiveType.COLLECT,
            target="herb"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest1, quest2]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Player already has the first quest
        existing_quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            status=QuestStatus.ACTIVE
        )
        character.quests.append(existing_quest)

        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Bare accept should auto-accept the only available quest
        _, output = handle_exploration_command(game_state, "accept", [])

        assert len(character.quests) == 2  # Now has both quests
        assert any(q.name == "Collect Herbs" for q in character.quests)
        assert "Collect Herbs" in output

    def test_accept_adds_quest_to_character(self):
        """Accept command adds quest to character with ACTIVE status."""
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            target_count=5
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Accept the quest
        _, output = handle_exploration_command(game_state, "accept", ["Kill", "Goblins"])

        assert len(character.quests) == 1
        assert character.quests[0].name == "Kill Goblins"
        assert character.quests[0].status == QuestStatus.ACTIVE
        assert "accept" in output.lower() or "Kill Goblins" in output

    def test_accept_rejects_already_acquired_quest(self):
        """Accept command fails if character already has the quest."""
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Player already has this quest
        existing_quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            status=QuestStatus.ACTIVE
        )
        character.quests.append(existing_quest)

        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Try to accept the quest again
        _, output = handle_exploration_command(game_state, "accept", ["Kill", "Goblins"])

        assert len(character.quests) == 1  # Still only one quest
        assert "already" in output.lower()

    def test_accept_rejects_quest_not_offered(self):
        """Accept command fails if NPC doesn't offer that quest."""
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Try to accept a quest the NPC doesn't offer
        _, output = handle_exploration_command(game_state, "accept", ["Collect", "Herbs"])

        assert len(character.quests) == 0
        assert "doesn't offer" in output.lower() or "not found" in output.lower()

    def test_accept_case_insensitive_matching(self):
        """Accept command matches quest names case-insensitively."""
        from cli_rpg.main import handle_exploration_command

        quest = Quest(
            name="Kill Goblins",
            description="Defeat goblins.",
            objective_type=ObjectiveType.KILL,
            target="goblin"
        )
        npc = NPC(
            name="Captain",
            description="Guard captain",
            dialogue="We need heroes!",
            is_quest_giver=True,
            offered_quests=[quest]
        )
        location = Location(name="Town", description="A town.", coordinates=(0, 0), npcs=[npc])
        character = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        game_state = GameState(character, {"Town": location}, "Town")

        # Talk to NPC first
        handle_exploration_command(game_state, "talk", ["Captain"])

        # Accept with different case
        _, output = handle_exploration_command(game_state, "accept", ["kill", "goblins"])

        assert len(character.quests) == 1
        assert character.quests[0].name == "Kill Goblins"  # Preserves original case
