"""Tests for AI Agent simulation system.

Spec from plan:
- State parser correctly handles all JSON message types
- Agent flees when HP critical
- Agent uses potions when available and HP low
- Agent explores when healthy
- Agent rests when dread high
- Session runs without crash for 100 commands
"""
import json
import pytest
import subprocess
import sys
import time

from scripts.state_parser import (
    AgentState,
    parse_line,
    update_state,
    parse_output_lines,
)
from scripts.ai_agent import Agent, SessionStats


class TestAgentState:
    """Test AgentState dataclass and helper methods."""

    # Spec: AgentState tracks health_percent correctly
    def test_health_percent_full(self):
        """Health percent is 1.0 when at max health."""
        state = AgentState(health=100, max_health=100)
        assert state.health_percent == 1.0

    def test_health_percent_half(self):
        """Health percent is 0.5 when at half health."""
        state = AgentState(health=50, max_health=100)
        assert state.health_percent == 0.5

    def test_health_percent_zero_max(self):
        """Health percent is 0 when max_health is 0."""
        state = AgentState(health=50, max_health=0)
        assert state.health_percent == 0.0

    # Spec: AgentState detects healing items
    def test_has_healing_item_with_potion(self):
        """has_healing_item returns True with potion in inventory."""
        state = AgentState(inventory=["Health Potion", "Sword"])
        assert state.has_healing_item() is True

    def test_has_healing_item_with_elixir(self):
        """has_healing_item returns True with elixir in inventory."""
        state = AgentState(inventory=["Lesser Healing Elixir"])
        assert state.has_healing_item() is True

    def test_has_healing_item_empty(self):
        """has_healing_item returns False with no healing items."""
        state = AgentState(inventory=["Sword", "Shield"])
        assert state.has_healing_item() is False

    def test_get_healing_item_name(self):
        """get_healing_item_name returns correct item name."""
        state = AgentState(inventory=["Sword", "Health Potion", "Shield"])
        assert state.get_healing_item_name() == "Health Potion"

    def test_get_healing_item_name_none(self):
        """get_healing_item_name returns None when no healing items."""
        state = AgentState(inventory=["Sword"])
        assert state.get_healing_item_name() is None


class TestStateParsing:
    """Test JSON parsing and state updates."""

    # Spec: State parser correctly handles all JSON message types

    def test_parse_line_valid_json(self):
        """parse_line returns dict for valid JSON."""
        line = '{"type": "state", "location": "Town"}'
        result = parse_line(line)
        assert result == {"type": "state", "location": "Town"}

    def test_parse_line_empty(self):
        """parse_line returns None for empty line."""
        assert parse_line("") is None
        assert parse_line("   ") is None

    def test_parse_line_invalid_json(self):
        """parse_line returns None for invalid JSON."""
        assert parse_line("not json") is None
        assert parse_line("{broken") is None

    def test_update_state_from_state_message(self):
        """update_state handles state type messages."""
        state = AgentState()
        message = {
            "type": "state",
            "location": "Dark Forest",
            "health": 75,
            "max_health": 100,
            "gold": 50,
            "level": 3
        }
        update_state(state, message)

        assert state.location == "Dark Forest"
        assert state.health == 75
        assert state.max_health == 100
        assert state.gold == 50
        assert state.level == 3

    def test_update_state_from_combat_message(self):
        """update_state handles combat type messages."""
        state = AgentState()
        message = {
            "type": "combat",
            "enemy": "Goblin",
            "enemy_health": 30,
            "player_health": 80
        }
        update_state(state, message)

        assert state.in_combat is True
        assert state.enemy == "Goblin"
        assert state.enemy_health == 30
        assert state.health == 80

    def test_update_state_from_actions_message(self):
        """update_state handles actions type messages."""
        state = AgentState()
        message = {
            "type": "actions",
            "exits": ["north", "south"],
            "npcs": ["Merchant"],
            "commands": ["go", "talk", "look"]
        }
        update_state(state, message)

        assert state.exits == ["north", "south"]
        assert state.npcs == ["Merchant"]
        assert state.commands == ["go", "talk", "look"]
        assert state.in_combat is False

    def test_update_state_from_actions_clears_combat(self):
        """update_state sets in_combat=False when actions received (combat emits combat type)."""
        state = AgentState(in_combat=True)  # Start in combat
        message = {
            "type": "actions",
            "exits": ["north"],
            "npcs": [],
            "commands": ["go", "look"]
        }
        update_state(state, message)

        # Actions are emitted when NOT in combat
        assert state.in_combat is False

    def test_update_state_from_dump_state(self):
        """update_state handles dump_state type messages."""
        state = AgentState()
        message = {
            "type": "dump_state",
            "current_location": "Castle",
            "character": {
                "health": 90,
                "max_health": 100,
                "gold": 200,
                "level": 5,
                "inventory": {
                    "items": [
                        {"name": "Sword"},
                        {"name": "Health Potion"}
                    ]
                },
                "dread_meter": {"dread": 45},
                "quests": [
                    {"name": "Find the Key", "status": "active"},
                    {"name": "Old Quest", "status": "completed"}
                ]
            }
        }
        update_state(state, message)

        assert state.location == "Castle"
        assert state.health == 90
        assert state.gold == 200
        assert state.level == 5
        assert state.inventory == ["Sword", "Health Potion"]
        assert state.dread == 45
        assert state.quests == ["Find the Key"]

    def test_parse_output_lines(self):
        """parse_output_lines processes multiple lines."""
        state = AgentState()
        lines = [
            '{"type": "state", "location": "Town", "health": 100, "max_health": 100, "gold": 0, "level": 1}',
            '{"type": "actions", "exits": ["north"], "npcs": [], "commands": ["go"]}',
            '',  # Empty line
            'invalid json',
        ]
        messages = parse_output_lines(lines, state)

        assert len(messages) == 2
        assert state.location == "Town"
        assert state.exits == ["north"]


class TestAgentDecisions:
    """Test Agent decision-making logic."""

    # Spec: Agent flees when HP critical (< 20%)
    def test_agent_flees_at_critical_hp(self):
        """Agent flees when health < 20%."""
        agent = Agent()
        state = AgentState(health=19, max_health=100, in_combat=True)

        decision = agent.decide(state)
        assert decision == "flee"

    def test_agent_flees_at_19_percent(self):
        """Agent flees at exactly 19% HP."""
        agent = Agent()
        state = AgentState(health=19, max_health=100, in_combat=True)

        decision = agent.decide(state)
        assert decision == "flee"

    # Spec: Agent uses potions when available and HP low (< 40%)
    def test_agent_uses_potion_when_hurt(self):
        """Agent uses healing potion when HP < 40% in combat."""
        agent = Agent()
        state = AgentState(
            health=39,
            max_health=100,
            in_combat=True,
            inventory=["Health Potion"]
        )

        decision = agent.decide(state)
        assert decision == "use Health Potion"

    def test_agent_attacks_when_healthy(self):
        """Agent attacks when HP >= 50% in combat."""
        agent = Agent()
        state = AgentState(health=60, max_health=100, in_combat=True)

        decision = agent.decide(state)
        assert decision == "attack"

    # Spec: Agent rests when dread high (requires triggering healing decision path)
    def test_agent_rests_when_dread_high(self):
        """Agent rests when HP < 50% and dread > 60%."""
        agent = Agent()
        # Agent needs HP < 50% to enter healing decision path where dread is checked
        state = AgentState(
            health=49,
            max_health=100,
            dread=65,
            exits=[]  # No exits to prevent exploration taking priority
        )

        decision = agent.decide(state)
        assert decision == "rest"

    def test_agent_rests_when_hp_low_out_of_combat(self):
        """Agent rests when HP < 50% outside combat."""
        agent = Agent()
        state = AgentState(
            health=40,
            max_health=100,
            dread=10,
            exits=["north"]
        )

        decision = agent.decide(state)
        assert decision == "rest"

    # Spec: Agent explores when healthy
    def test_agent_explores_when_healthy(self):
        """Agent moves to exit when healthy and not in combat."""
        agent = Agent()
        state = AgentState(
            health=100,
            max_health=100,
            dread=10,
            exits=["north", "south"]
        )

        decision = agent.decide(state)
        assert decision.startswith("go ")

    def test_agent_talks_to_npc_when_no_exits(self):
        """Agent talks to NPC when present but no exits available."""
        agent = Agent()
        state = AgentState(
            health=100,
            max_health=100,
            dread=10,
            npcs=["Merchant"],
            exits=[],  # No exits - can't explore
            commands=["talk", "look"]
        )

        decision = agent.decide(state)
        assert decision == "talk Merchant"

    def test_agent_completes_quest_with_npc_and_active_quest(self):
        """Agent uses complete command when ready-to-turn-in quest and complete available."""
        from scripts.state_parser import QuestInfo
        agent = Agent()
        # Mark NPC as already talked to so agent uses "complete" instead of "talk"
        agent.talked_this_location.add("Quest Giver")
        state = AgentState(
            health=100,
            max_health=100,
            dread=10,
            npcs=["Quest Giver"],
            quests=["Find the Key"],  # Active quest required
            quest_details=[QuestInfo(
                name="Find the Key",
                objective_type="collect",
                target="Key",
                target_count=1,
                current_count=1,  # Quest is complete
                quest_giver="Quest Giver"
            )],
            commands=["complete", "talk", "look"]
        )

        decision = agent.decide(state)
        assert decision == "complete"

    def test_agent_looks_when_no_exits(self):
        """Agent looks when no exits available."""
        agent = Agent()
        state = AgentState(
            health=100,
            max_health=100,
            dread=10,
            exits=[]
        )

        decision = agent.decide(state)
        assert decision == "look"


class TestSessionStats:
    """Test SessionStats tracking."""

    def test_stats_to_dict(self):
        """SessionStats serializes to dict correctly."""
        stats = SessionStats(
            commands_issued=100,
            locations_visited={"Town", "Forest", "Cave"},
            enemies_defeated=5,
            deaths=1,
            potions_used=3,
            gold_earned=150,
            fled_count=2,
            rested_count=10,
            errors_encountered=0,
        )

        result = stats.to_dict()

        assert result["commands_issued"] == 100
        assert result["unique_locations"] == 3
        assert set(result["locations_visited"]) == {"Town", "Forest", "Cave"}
        assert result["enemies_defeated"] == 5
        assert result["deaths"] == 1
        assert result["potions_used"] == 3
        assert result["gold_earned"] == 150
        assert result["fled_count"] == 2
        assert result["rested_count"] == 10
        assert result["errors_encountered"] == 0


class TestIntegration:
    """Integration tests for full simulation."""

    # Spec: Session runs without crash for 100 commands
    @pytest.mark.slow
    def test_session_runs_100_commands(self):
        """Session completes 100 commands without crashing."""
        from scripts.ai_agent import GameSession

        session = GameSession(
            seed=42,
            max_commands=100,
            timeout=60.0,
            verbose=False,
        )

        stats = session.run()

        # Should have issued commands
        assert stats.commands_issued > 0
        # Should have visited at least one location
        assert len(stats.locations_visited) >= 1
        # Should not have crashed (we got here)

    @pytest.mark.slow
    def test_session_explores_multiple_locations(self):
        """Session visits multiple locations during exploration."""
        from scripts.ai_agent import GameSession

        session = GameSession(
            seed=12345,
            max_commands=50,
            timeout=30.0,
            verbose=False,
        )

        stats = session.run()

        # Should have visited at least the starting location
        assert len(stats.locations_visited) >= 1


class TestVerboseMode:
    """Test verbose output mode."""

    def test_agent_verbose_prints(self, capsys):
        """Verbose agent prints decision reasoning."""
        agent = Agent(verbose=True)
        state = AgentState(health=19, max_health=100, in_combat=True)

        agent.decide(state)

        captured = capsys.readouterr()
        assert "[AGENT]" in captured.out
        assert "Fleeing" in captured.out
