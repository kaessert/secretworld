"""Tests for Charisma (CHA) stat and social skills system.

Tests the CHA stat on Character model, price modifiers, and social skill commands
(persuade, intimidate, bribe) per spec in thoughts/current_plan.md.
"""
import pytest
from unittest.mock import patch, MagicMock

from cli_rpg.models.character import Character, CharacterClass, CLASS_BONUSES
from cli_rpg.models.npc import NPC


class TestCharacterCharisma:
    """Tests for Character charisma stat - tests spec: CHA stat."""

    def test_character_has_charisma_stat(self):
        """Character has charisma stat initialized and validated (1-20)."""
        # Tests spec: CHA stat (1-20) added to Character
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=12,
        )
        assert character.charisma == 12

    def test_character_charisma_validation_min(self):
        """Charisma must be at least 1."""
        with pytest.raises(ValueError, match="charisma must be at least 1"):
            Character(
                name="TestHero",
                strength=10,
                dexterity=10,
                intelligence=10,
                charisma=0,
            )

    def test_character_charisma_validation_max(self):
        """Charisma must be at most 20."""
        with pytest.raises(ValueError, match="charisma must be at most 20"):
            Character(
                name="TestHero",
                strength=10,
                dexterity=10,
                intelligence=10,
                charisma=21,
            )

    def test_character_class_cha_bonuses_cleric(self):
        """Cleric class gets +2 CHA bonus."""
        # Tests spec: Cleric +2 CHA
        character = Character(
            name="TestCleric",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.CLERIC,
        )
        # Base 10 + 2 bonus = 12
        assert character.charisma == 12

    def test_character_class_cha_bonuses_rogue(self):
        """Rogue class gets +1 CHA bonus."""
        # Tests spec: Rogue +1 CHA
        character = Character(
            name="TestRogue",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.ROGUE,
        )
        # Base 10 + 1 bonus = 11
        assert character.charisma == 11

    def test_character_class_cha_bonuses_warrior(self):
        """Warrior class gets 0 CHA bonus."""
        # Tests spec: Others: 0 CHA
        character = Character(
            name="TestWarrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
            character_class=CharacterClass.WARRIOR,
        )
        # No bonus
        assert character.charisma == 10

    def test_character_level_up_increases_cha(self):
        """Level up increases CHA by 1."""
        # Tests spec: CHA +1 on level up
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        initial_cha = character.charisma
        character.level_up()
        assert character.charisma == initial_cha + 1

    def test_character_serialization_includes_cha(self):
        """Character to_dict() includes charisma."""
        # Tests spec: to_dict includes CHA
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=15,
        )
        data = character.to_dict()
        assert "charisma" in data
        assert data["charisma"] == 15

    def test_character_deserialization_restores_cha(self):
        """Character from_dict() restores charisma."""
        # Tests spec: from_dict restores CHA
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=15,
        )
        data = character.to_dict()
        restored = Character.from_dict(data)
        assert restored.charisma == 15

    def test_character_deserialization_backward_compat(self):
        """Character from_dict() defaults charisma to 10 for old saves."""
        # Tests spec: default 10 for backward compat
        data = {
            "name": "OldSave",
            "strength": 12,
            "dexterity": 12,
            "intelligence": 12,
            "level": 1,
        }
        character = Character.from_dict(data)
        assert character.charisma == 10

    def test_character_status_displays_cha(self):
        """Character __str__() displays CHA."""
        # Tests spec: Status output shows CHA
        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=14,
        )
        status = str(character)
        assert "Charisma" in status
        assert "14" in status


class TestCharacterCreationCharisma:
    """Tests for charisma in character creation."""

    def test_generate_random_stats_includes_cha(self):
        """Random stats include charisma in 8-15 range."""
        # Tests spec: Random stats include CHA
        from cli_rpg.character_creation import generate_random_stats

        stats = generate_random_stats()
        assert "charisma" in stats
        assert 8 <= stats["charisma"] <= 15


class TestShopPriceModifiers:
    """Tests for CHA-based shop price modifiers."""

    def test_get_cha_price_modifier_baseline(self):
        """CHA 10 gives 1.0 (no modifier)."""
        # Tests spec: ±1% per CHA point from baseline 10
        from cli_rpg.social_skills import get_cha_price_modifier

        modifier = get_cha_price_modifier(10)
        assert modifier == 1.0

    def test_get_cha_price_modifier_high_cha(self):
        """High CHA reduces buy price (lower modifier)."""
        # Tests spec: High CHA = lower buy price
        from cli_rpg.social_skills import get_cha_price_modifier

        # CHA 15 = -5% = 0.95
        modifier = get_cha_price_modifier(15)
        assert modifier == 0.95

    def test_get_cha_price_modifier_low_cha(self):
        """Low CHA increases buy price (higher modifier)."""
        # Tests spec: formula ±1% per CHA from 10
        from cli_rpg.social_skills import get_cha_price_modifier

        # CHA 5 = +5% = 1.05
        modifier = get_cha_price_modifier(5)
        assert modifier == 1.05

    def test_shop_buy_price_modified_by_cha(self):
        """Shop buy price is reduced by high CHA."""
        # Tests spec: Shop buy prices adjusted by CHA
        from cli_rpg.social_skills import get_cha_price_modifier

        base_price = 100
        # CHA 15 gives 0.95 modifier
        modifier = get_cha_price_modifier(15)
        final_price = int(base_price * modifier)
        assert final_price == 95

    def test_shop_sell_price_modified_by_cha(self):
        """Shop sell price is increased by high CHA (inverse modifier)."""
        # Tests spec: High CHA = higher sell price
        from cli_rpg.social_skills import get_cha_sell_modifier

        # High CHA should increase what you get from selling
        modifier = get_cha_sell_modifier(15)
        assert modifier > 1.0

        # CHA 15 = +5% = 1.05
        assert modifier == 1.05


class TestPersuadeCommand:
    """Tests for persuade social skill command."""

    def test_persuade_success_rate_formula(self):
        """Persuade success uses 30% base + (CHA × 3%), max 90%."""
        # Tests spec: 30% base + (CHA × 3%), max 90%
        from cli_rpg.social_skills import calculate_persuade_chance

        # CHA 10: 30% + 30% = 60%
        assert calculate_persuade_chance(10) == 60

        # CHA 20: 30% + 60% = 90% (capped)
        assert calculate_persuade_chance(20) == 90

        # CHA 5: 30% + 15% = 45%
        assert calculate_persuade_chance(5) == 45

    def test_persuade_requires_npc_conversation(self):
        """Persuade fails if not talking to an NPC."""
        # Tests spec: Must be talking to NPC
        from cli_rpg.social_skills import attempt_persuade

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=15,
        )
        success, message = attempt_persuade(character, None)
        assert success is False
        assert "talking to" in message.lower() or "no one" in message.lower()

    def test_persuade_success_grants_discount(self):
        """Successful persuade grants 20% shop discount."""
        # Tests spec: 20% shop discount on success
        from cli_rpg.social_skills import attempt_persuade

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=15,
        )
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello")

        # Force success with mocked random
        with patch("cli_rpg.social_skills.random.randint", return_value=1):
            success, message = attempt_persuade(character, npc)
            assert success is True
            assert npc.persuaded is True
            assert "discount" in message.lower()

    def test_persuade_failure_message(self):
        """Failed persuade shows graceful failure message."""
        # Tests spec: Graceful failure message
        from cli_rpg.social_skills import attempt_persuade

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=5,  # Low CHA for likely failure
        )
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello")

        # Force failure with high roll
        with patch("cli_rpg.social_skills.random.randint", return_value=100):
            success, message = attempt_persuade(character, npc)
            assert success is False
            assert "not convinced" in message.lower() or "fail" in message.lower()

    def test_persuade_cooldown_per_npc(self):
        """Can't spam persuade on same NPC."""
        # Tests spec: Can't spam persuade
        from cli_rpg.social_skills import attempt_persuade

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=15,
        )
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello")
        npc.persuaded = True  # Already persuaded

        success, message = attempt_persuade(character, npc)
        assert success is False
        assert "already" in message.lower()


class TestIntimidateCommand:
    """Tests for intimidate social skill command."""

    def test_intimidate_success_rate_formula(self):
        """Intimidate uses 20% base + (CHA × 2%) + (kills × 5%), max 85%."""
        # Tests spec: 20% base + (CHA × 2%) + (kills × 5%), max 85%
        from cli_rpg.social_skills import calculate_intimidate_chance

        # CHA 10, 0 kills: 20% + 20% + 0% = 40%
        assert calculate_intimidate_chance(10, 0) == 40

        # CHA 15, 5 kills: 20% + 30% + 25% = 75%
        assert calculate_intimidate_chance(15, 5) == 75

        # CHA 20, 10 kills: 20% + 40% + 50% = 110% -> capped at 85%
        assert calculate_intimidate_chance(20, 10) == 85

    def test_intimidate_success_on_weak_willed(self):
        """Intimidate works on NPCs with low willpower."""
        # Tests spec: Works on low willpower NPCs
        from cli_rpg.social_skills import attempt_intimidate

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=15,
        )
        npc = NPC(name="Timid", description="A nervous person", dialogue="H-hello")
        npc.willpower = 2  # Very weak-willed

        # Force success
        with patch("cli_rpg.social_skills.random.randint", return_value=1):
            success, message = attempt_intimidate(character, npc, kill_count=5)
            assert success is True
            assert "cower" in message.lower() or "intimidate" in message.lower()

    def test_intimidate_backfires_on_strong_willed(self):
        """Intimidate fails + penalty on high willpower NPCs."""
        # Tests spec: Fails + penalty on high willpower
        from cli_rpg.social_skills import attempt_intimidate

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        npc = NPC(name="Guard", description="A stern guard", dialogue="Watch it")
        npc.willpower = 9  # Strong-willed

        # Force failure
        with patch("cli_rpg.social_skills.random.randint", return_value=100):
            success, message = attempt_intimidate(character, npc, kill_count=0)
            assert success is False
            # Strong-willed NPCs should respond more harshly
            assert "anger" in message.lower() or "hostil" in message.lower() or "not impressed" in message.lower()

    def test_intimidate_bonus_from_kills(self):
        """Kill count boosts intimidate success chance."""
        # Tests spec: Kill count boosts success
        from cli_rpg.social_skills import calculate_intimidate_chance

        # 0 kills vs 5 kills at CHA 10 (stay below cap)
        chance_0_kills = calculate_intimidate_chance(10, 0)  # 20 + 20 + 0 = 40%
        chance_5_kills = calculate_intimidate_chance(10, 5)  # 20 + 20 + 25 = 65%
        assert chance_5_kills > chance_0_kills
        assert chance_5_kills - chance_0_kills == 25  # 5 kills × 5%


class TestBribeCommand:
    """Tests for bribe social skill command."""

    def test_bribe_success_formula(self):
        """Bribe succeeds if amount >= 50 - (CHA × 2), min 10 gold."""
        # Tests spec: Success if amount >= 50 - (CHA × 2), min 10
        from cli_rpg.social_skills import calculate_bribe_threshold

        # CHA 10: 50 - 20 = 30 gold needed
        assert calculate_bribe_threshold(10) == 30

        # CHA 20: 50 - 40 = 10 gold (minimum)
        assert calculate_bribe_threshold(20) == 10

        # CHA 5: 50 - 10 = 40 gold needed
        assert calculate_bribe_threshold(5) == 40

    def test_bribe_requires_amount(self):
        """Bribe command requires gold amount."""
        # Tests spec: Must specify gold amount
        from cli_rpg.social_skills import attempt_bribe

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        npc = NPC(name="Guard", description="A guard", dialogue="Hello")

        success, message = attempt_bribe(character, npc, None)
        assert success is False
        assert "amount" in message.lower() or "how much" in message.lower()

    def test_bribe_insufficient_gold_fails(self):
        """Bribe fails if not enough gold."""
        # Tests spec: Error if not enough gold
        from cli_rpg.social_skills import attempt_bribe

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        character.gold = 10  # Only 10 gold
        npc = NPC(name="Guard", description="A guard", dialogue="Hello")

        success, message = attempt_bribe(character, npc, 50)
        assert success is False
        assert "enough gold" in message.lower() or "afford" in message.lower()

    def test_bribe_success_deducts_gold(self):
        """Successful bribe deducts gold from character."""
        # Tests spec: Gold removed on success
        from cli_rpg.social_skills import attempt_bribe

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        character.gold = 100
        npc = NPC(name="Guard", description="A guard", dialogue="Hello")

        success, message = attempt_bribe(character, npc, 50)
        assert success is True
        assert character.gold == 50  # 100 - 50

    def test_bribe_unbribeable_npc_refuses(self):
        """NPCs with bribeable=False refuse bribes."""
        # Tests spec: Some NPCs can't be bribed
        from cli_rpg.social_skills import attempt_bribe

        character = Character(
            name="TestHero",
            strength=10,
            dexterity=10,
            intelligence=10,
            charisma=10,
        )
        character.gold = 100
        npc = NPC(name="Paladin", description="A holy warrior", dialogue="Justice!")
        npc.bribeable = False

        success, message = attempt_bribe(character, npc, 50)
        assert success is False
        assert "refuse" in message.lower() or "cannot be bribed" in message.lower()
        assert character.gold == 100  # Gold not deducted


class TestNPCSocialAttributes:
    """Tests for NPC social attributes (willpower, bribeable)."""

    def test_npc_has_willpower_default(self):
        """NPC has willpower attribute with default 5."""
        # Tests spec: willpower: int (1-10), default 5
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello")
        assert hasattr(npc, "willpower")
        assert npc.willpower == 5

    def test_npc_willpower_can_be_set(self):
        """NPC willpower can be set during creation."""
        npc = NPC(
            name="Guard",
            description="A tough guard",
            dialogue="Move along",
            willpower=8,
        )
        assert npc.willpower == 8

    def test_npc_has_bribeable_default(self):
        """NPC has bribeable attribute with default True."""
        # Tests spec: bribeable: bool, default True
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello")
        assert hasattr(npc, "bribeable")
        assert npc.bribeable is True

    def test_npc_bribeable_can_be_set(self):
        """NPC bribeable can be set during creation."""
        npc = NPC(
            name="Paladin",
            description="A holy warrior",
            dialogue="Justice!",
            bribeable=False,
        )
        assert npc.bribeable is False

    def test_npc_has_persuaded_default(self):
        """NPC has persuaded attribute with default False."""
        # Tests spec: persuaded: bool, default False
        npc = NPC(name="Merchant", description="A shopkeeper", dialogue="Hello")
        assert hasattr(npc, "persuaded")
        assert npc.persuaded is False

    def test_npc_serialization_includes_social_attributes(self):
        """NPC to_dict() includes willpower, bribeable, persuaded."""
        # Tests spec: to_dict/from_dict preserves social attrs
        npc = NPC(
            name="Guard",
            description="A guard",
            dialogue="Hello",
            willpower=7,
            bribeable=False,
        )
        npc.persuaded = True

        data = npc.to_dict()
        assert data["willpower"] == 7
        assert data["bribeable"] is False
        assert data["persuaded"] is True

    def test_npc_deserialization_restores_social_attributes(self):
        """NPC from_dict() restores willpower, bribeable, persuaded."""
        npc = NPC(
            name="Guard",
            description="A guard",
            dialogue="Hello",
            willpower=7,
            bribeable=False,
        )
        npc.persuaded = True

        data = npc.to_dict()
        restored = NPC.from_dict(data)

        assert restored.willpower == 7
        assert restored.bribeable is False
        assert restored.persuaded is True

    def test_npc_deserialization_backward_compat(self):
        """NPC from_dict() uses defaults for old saves without social attrs."""
        data = {
            "name": "OldNPC",
            "description": "An old NPC",
            "dialogue": "Hello",
        }
        npc = NPC.from_dict(data)
        assert npc.willpower == 5
        assert npc.bribeable is True
        assert npc.persuaded is False
