"""Tests for NPC arc effects on shop prices.

Tests verify the shop pricing system integrates with NPC arc stages per the spec:
- ENEMY: Trade refused entirely
- HOSTILE: +20% buy price, -20% sell price
- WARY: +10% buy price, -10% sell price
- STRANGER: No modifier (default)
- ACQUAINTANCE: -5% buy price, +5% sell price
- TRUSTED: -10% buy price, +10% sell price
- DEVOTED: -15% buy price, +15% sell price
"""
import pytest

from cli_rpg.models.npc_arc import NPCArc, NPCArcStage
from cli_rpg.npc_arc_shop import (
    ARC_PRICE_MODIFIERS,
    get_arc_price_modifiers,
    get_arc_price_message,
)


# === Unit tests for get_arc_price_modifiers ===


class TestArcPriceModifiers:
    """Tests for get_arc_price_modifiers function."""

    # Spec: ENEMY stage refuses trade entirely
    def test_arc_price_modifiers_enemy_refuses_trade(self):
        """ENEMY arc stage should refuse trade entirely."""
        arc = NPCArc(arc_points=-60)  # ENEMY is -50 to -100
        assert arc.get_stage() == NPCArcStage.ENEMY

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is True
        assert buy_mod is None
        assert sell_mod is None

    # Spec: HOSTILE +20% buy, -20% sell
    def test_arc_price_modifiers_hostile_premium(self):
        """HOSTILE arc stage should apply +20% buy, -20% sell."""
        arc = NPCArc(arc_points=-30)  # HOSTILE is -25 to -49
        assert arc.get_stage() == NPCArcStage.HOSTILE

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is False
        assert buy_mod == 1.20
        assert sell_mod == 0.80

    # Spec: WARY +10% buy, -10% sell
    def test_arc_price_modifiers_wary_penalty(self):
        """WARY arc stage should apply +10% buy, -10% sell."""
        arc = NPCArc(arc_points=-10)  # WARY is -1 to -24
        assert arc.get_stage() == NPCArcStage.WARY

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is False
        assert buy_mod == 1.10
        assert sell_mod == 0.90

    # Spec: STRANGER has no modifier
    def test_arc_price_modifiers_stranger_neutral(self):
        """STRANGER arc stage should have no price modifier."""
        arc = NPCArc(arc_points=10)  # STRANGER is 0-24
        assert arc.get_stage() == NPCArcStage.STRANGER

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is False
        assert buy_mod == 1.0
        assert sell_mod == 1.0

    # Spec: ACQUAINTANCE -5% buy, +5% sell
    def test_arc_price_modifiers_acquaintance_small_discount(self):
        """ACQUAINTANCE arc stage should apply -5% buy, +5% sell."""
        arc = NPCArc(arc_points=30)  # ACQUAINTANCE is 25-49
        assert arc.get_stage() == NPCArcStage.ACQUAINTANCE

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is False
        assert buy_mod == 0.95
        assert sell_mod == 1.05

    # Spec: TRUSTED -10% buy, +10% sell
    def test_arc_price_modifiers_trusted_discount(self):
        """TRUSTED arc stage should apply -10% buy, +10% sell."""
        arc = NPCArc(arc_points=60)  # TRUSTED is 50-74
        assert arc.get_stage() == NPCArcStage.TRUSTED

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is False
        assert buy_mod == 0.90
        assert sell_mod == 1.10

    # Spec: DEVOTED -15% buy, +15% sell (best prices)
    def test_arc_price_modifiers_devoted_best_discount(self):
        """DEVOTED arc stage should apply -15% buy, +15% sell."""
        arc = NPCArc(arc_points=80)  # DEVOTED is 75-100
        assert arc.get_stage() == NPCArcStage.DEVOTED

        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(arc)

        assert trade_refused is False
        assert buy_mod == 0.85
        assert sell_mod == 1.15

    # Spec: None arc should behave as neutral
    def test_arc_price_modifiers_none_arc_neutral(self):
        """None arc should behave as neutral (no modifier)."""
        buy_mod, sell_mod, trade_refused = get_arc_price_modifiers(None)

        assert trade_refused is False
        assert buy_mod == 1.0
        assert sell_mod == 1.0


class TestArcPriceMessages:
    """Tests for get_arc_price_message function."""

    def test_message_for_enemy(self):
        """ENEMY stage should have a refusal message."""
        msg = get_arc_price_message(NPCArcStage.ENEMY)
        assert msg != ""
        assert "refuse" in msg.lower()

    def test_message_for_hostile(self):
        """HOSTILE stage should have a penalty message."""
        msg = get_arc_price_message(NPCArcStage.HOSTILE)
        assert "20%" in msg
        assert "hostility" in msg.lower()

    def test_message_for_stranger(self):
        """STRANGER stage should have empty message."""
        msg = get_arc_price_message(NPCArcStage.STRANGER)
        assert msg == ""

    def test_message_for_trusted(self):
        """TRUSTED stage should have a discount message."""
        msg = get_arc_price_message(NPCArcStage.TRUSTED)
        assert "10%" in msg
        assert "trust" in msg.lower()

    def test_message_for_devoted(self):
        """DEVOTED stage should have best discount message."""
        msg = get_arc_price_message(NPCArcStage.DEVOTED)
        assert "15%" in msg


class TestArcPriceModifiersDict:
    """Tests for ARC_PRICE_MODIFIERS constant coverage."""

    def test_all_stages_have_modifiers(self):
        """All NPCArcStage values should have defined modifiers."""
        for stage in NPCArcStage:
            assert stage in ARC_PRICE_MODIFIERS, f"Missing modifier for {stage}"
