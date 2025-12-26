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

    # Spec: stats → status (word alias, not single-letter)
    def test_stats_expands_to_status(self):
        cmd, args = parse_command("stats")
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


class TestDirectionShorthands:
    """Test direction shorthand expansion for go command.

    Spec: Expand direction shorthands when using the `go` command:
    - n → north, s → south, e → east, w → west
    - Works with command shorthand: g n → go north
    - Works with full command: go s → go south
    - Case-insensitive: G N → go north
    """

    # Spec: g n → go north
    def test_g_n_expands_to_go_north(self):
        cmd, args = parse_command("g n")
        assert cmd == "go"
        assert args == ["north"]

    # Spec: g s → go south
    def test_g_s_expands_to_go_south(self):
        cmd, args = parse_command("g s")
        assert cmd == "go"
        assert args == ["south"]

    # Spec: g e → go east
    def test_g_e_expands_to_go_east(self):
        cmd, args = parse_command("g e")
        assert cmd == "go"
        assert args == ["east"]

    # Spec: g w → go west
    def test_g_w_expands_to_go_west(self):
        cmd, args = parse_command("g w")
        assert cmd == "go"
        assert args == ["west"]

    # Spec: go n → go north (full command with shorthand direction)
    def test_go_n_expands_to_go_north(self):
        cmd, args = parse_command("go n")
        assert cmd == "go"
        assert args == ["north"]

    # Spec: G N → go north (case-insensitive)
    def test_direction_shorthand_case_insensitive(self):
        cmd, args = parse_command("G N")
        assert cmd == "go"
        assert args == ["north"]

    # Spec: Full direction names still work
    def test_full_direction_still_works(self):
        cmd, args = parse_command("g north")
        assert cmd == "go"
        assert args == ["north"]


class TestMageSpellShorthands:
    """Test Mage spell shorthand aliases.

    Spec: Mage spell shorthand aliases:
    - fb → fireball
    - ib → ice_bolt
    - hl → heal
    """

    # Spec: fb → fireball
    def test_fb_expands_to_fireball(self):
        cmd, args = parse_command("fb goblin")
        assert cmd == "fireball"
        assert args == ["goblin"]

    # Spec: fb without target works
    def test_fb_without_target(self):
        cmd, args = parse_command("fb")
        assert cmd == "fireball"
        assert args == []

    # Spec: ib → ice_bolt
    def test_ib_expands_to_ice_bolt(self):
        cmd, args = parse_command("ib orc")
        assert cmd == "ice_bolt"
        assert args == ["orc"]

    # Spec: ib without target works
    def test_ib_without_target(self):
        cmd, args = parse_command("ib")
        assert cmd == "ice_bolt"
        assert args == []

    # Spec: hl → heal
    def test_hl_expands_to_heal(self):
        cmd, args = parse_command("hl")
        assert cmd == "heal"
        assert args == []

    # Spec: Full spell names still work
    def test_fireball_full_command(self):
        cmd, args = parse_command("fireball goblin")
        assert cmd == "fireball"
        assert args == ["goblin"]

    def test_ice_bolt_full_command(self):
        cmd, args = parse_command("ice_bolt orc")
        assert cmd == "ice_bolt"
        assert args == ["orc"]

    def test_heal_full_command(self):
        cmd, args = parse_command("heal")
        assert cmd == "heal"
        assert args == []