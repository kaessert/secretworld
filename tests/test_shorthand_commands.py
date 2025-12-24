"""Tests for shorthand command aliases.

These tests verify that single-letter aliases expand correctly to full commands
in parse_command() before validation.
"""

from cli_rpg.game_state import parse_command


class TestShorthandCommands:
    """Test single-letter command aliases expand correctly."""

    # Spec: g → go
    def test_g_expands_to_go(self):
        cmd, args = parse_command("g north")
        assert cmd == "go"
        assert args == ["north"]

    # Spec: l → look
    def test_l_expands_to_look(self):
        cmd, args = parse_command("l")
        assert cmd == "look"
        assert args == []

    # Spec: a → attack
    def test_a_expands_to_attack(self):
        cmd, args = parse_command("a")
        assert cmd == "attack"
        assert args == []

    # Spec: c → cast
    def test_c_expands_to_cast(self):
        cmd, args = parse_command("c")
        assert cmd == "cast"
        assert args == []

    # Spec: d → defend
    def test_d_expands_to_defend(self):
        cmd, args = parse_command("d")
        assert cmd == "defend"
        assert args == []

    # Spec: f → flee
    def test_f_expands_to_flee(self):
        cmd, args = parse_command("f")
        assert cmd == "flee"
        assert args == []

    # Spec: s → status
    def test_s_expands_to_status(self):
        cmd, args = parse_command("s")
        assert cmd == "status"
        assert args == []

    # Spec: i → inventory
    def test_i_expands_to_inventory(self):
        cmd, args = parse_command("i")
        assert cmd == "inventory"
        assert args == []

    # Spec: m → map
    def test_m_expands_to_map(self):
        cmd, args = parse_command("m")
        assert cmd == "map"
        assert args == []

    # Spec: h → help
    def test_h_expands_to_help(self):
        cmd, args = parse_command("h")
        assert cmd == "help"
        assert args == []

    # Spec: t → talk
    def test_t_expands_to_talk(self):
        cmd, args = parse_command("t merchant")
        assert cmd == "talk"
        assert args == ["merchant"]

    # Spec: u → use
    def test_u_expands_to_use(self):
        cmd, args = parse_command("u potion")
        assert cmd == "use"
        assert args == ["potion"]

    # Spec: e → equip
    def test_e_expands_to_equip(self):
        cmd, args = parse_command("e sword")
        assert cmd == "equip"
        assert args == ["sword"]

    # Spec: Aliases should be case-insensitive
    def test_shorthand_case_insensitive(self):
        cmd, args = parse_command("G NORTH")
        assert cmd == "go"
        assert args == ["north"]
