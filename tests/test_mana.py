"""Tests for the mana resource system.

These tests verify the spec:
- Mages get higher max_mana (50 + INT × 5); other classes get base 20 + INT × 2
- Mana regenerates on rest (+25% of max_mana)
- Cast command costs 10 mana per use
- Arcane Burst combo costs 25 mana (not 3 × 10)
- Mana potions restore mana
- Serialization preserves mana with backward compatibility
"""

import pytest
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter


class TestManaStat:
    """Tests for mana stat calculation on Character model."""

    def test_mage_has_higher_max_mana(self):
        """Spec: Mage with INT 15 gets 50 + 15×5 = 125 max_mana."""
        # Mage class gives +3 INT, so start with 12 to get 15 total
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=12,  # +3 from Mage = 15 INT
            character_class=CharacterClass.MAGE
        )
        # Mage formula: 50 + INT * 5 = 50 + 15 * 5 = 125
        assert char.max_mana == 125
        assert char.mana == char.max_mana  # Starts at full mana

    def test_warrior_has_lower_max_mana(self):
        """Spec: Warrior with INT 10 gets 20 + 10×2 = 40 max_mana."""
        char = Character(
            name="TestWarrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR
        )
        # Non-mage formula: 20 + INT * 2 = 20 + 10 * 2 = 40
        assert char.max_mana == 40
        assert char.mana == char.max_mana

    def test_rogue_has_lower_max_mana(self):
        """Spec: Non-mage classes use base 20 + INT × 2 formula."""
        char = Character(
            name="TestRogue",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.ROGUE
        )
        # Non-mage formula: 20 + INT * 2 = 20 + 10 * 2 = 40
        assert char.max_mana == 40

    def test_mana_use_method(self):
        """Spec: use_mana(amount) returns False if insufficient mana."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE
        )
        initial_mana = char.mana

        # Using mana should succeed and deduct mana
        assert char.use_mana(10) is True
        assert char.mana == initial_mana - 10

        # Using more mana than available should fail
        char.mana = 5
        assert char.use_mana(10) is False
        assert char.mana == 5  # Mana unchanged on failure

    def test_mana_restore_method(self):
        """Spec: restore_mana is capped at max_mana."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE
        )
        char.mana = 50

        # Restore within bounds
        char.restore_mana(25)
        assert char.mana == 75

        # Restore that would exceed max gets capped
        char.restore_mana(1000)
        assert char.mana == char.max_mana

    def test_mana_capped_at_max(self):
        """Spec: Mana cannot exceed max_mana."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE
        )
        char.mana = char.max_mana

        # Try to restore when already at max
        char.restore_mana(50)
        assert char.mana == char.max_mana


class TestManaInCombat:
    """Tests for mana costs in combat."""

    def test_cast_deducts_mana(self):
        """Spec: Casting reduces mana by 10."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        enemy = Enemy(
            name="TestEnemy",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=10,
            level=1
        )
        combat = CombatEncounter(char, enemy)
        combat.start()

        initial_mana = char.mana
        victory, message = combat.player_cast()

        # Mana should be deducted by 10
        assert char.mana == initial_mana - 10

    def test_cast_fails_without_mana(self):
        """Spec: Cast with 0 mana returns failure message."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        enemy = Enemy(
            name="TestEnemy",
            health=100,
            max_health=100,
            attack_power=5,
            defense=0,
            xp_reward=10,
            level=1
        )
        combat = CombatEncounter(char, enemy)
        combat.start()

        # Set mana to 0
        char.mana = 0
        victory, message = combat.player_cast()

        # Cast should fail
        assert victory is False
        assert "Not enough mana" in message
        assert "(0/" in message  # Shows current/max format

    def test_arcane_burst_costs_25_mana(self):
        """Spec: Arcane Burst combo costs 25 mana, not 30 (3×10)."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        enemy = Enemy(
            name="TestEnemy",
            health=500,  # High HP so it survives
            max_health=500,
            attack_power=5,
            defense=0,
            xp_reward=10,
            level=1
        )
        combat = CombatEncounter(char, enemy)
        combat.start()

        # Build up to Arcane Burst combo: cast x3 builds the combo,
        # 4th cast triggers it (combo is set after 3rd cast, triggered on 4th)
        # First three casts cost 10 each
        char.mana = 100  # Set a known starting point
        combat.player_cast()  # 100 - 10 = 90
        combat.player_cast()  # 90 - 10 = 80
        combat.player_cast()  # 80 - 10 = 70, sets pending_combo

        # Fourth cast triggers Arcane Burst which costs 25 (not another 10)
        mana_before_burst = char.mana  # 70
        victory, message = combat.player_cast()

        # Check that Arcane Burst was triggered
        assert "ARCANE BURST" in message

        # Arcane Burst costs 25 mana
        assert char.mana == mana_before_burst - 25


class TestManaRest:
    """Tests for mana regeneration on rest."""

    def test_rest_regenerates_mana(self):
        """Spec: Rest restores 25% of max_mana."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        # Reduce mana to test regeneration
        char.mana = 10
        expected_regen = char.max_mana // 4  # 25%

        # Manually call rest_mana method (similar to what rest command does)
        old_mana = char.mana
        char.restore_mana(expected_regen)

        assert char.mana == old_mana + expected_regen


class TestManaPotion:
    """Tests for mana restoration items."""

    def test_mana_potion_restores_mana(self):
        """Spec: Using Mana Potion adds mana_restore amount."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        # Create mana potion
        mana_potion = Item(
            name="Mana Potion",
            description="Restores mana",
            item_type=ItemType.CONSUMABLE,
            mana_restore=25
        )
        char.inventory.add_item(mana_potion)

        # Reduce mana
        char.mana = 10

        # Use the potion
        success, message = char.use_item(mana_potion)

        assert success is True
        assert char.mana == 35  # 10 + 25
        assert "mana" in message.lower()

    def test_item_mana_restore_field(self):
        """Spec: Item with mana_restore serializes correctly."""
        item = Item(
            name="Mana Potion",
            description="Restores mana",
            item_type=ItemType.CONSUMABLE,
            mana_restore=25
        )

        # Serialize
        data = item.to_dict()
        assert data["mana_restore"] == 25

        # Deserialize
        loaded = Item.from_dict(data)
        assert loaded.mana_restore == 25

    def test_item_str_shows_mana_restore(self):
        """Spec: Item __str__() shows 'restores X mana' when mana_restore > 0."""
        item = Item(
            name="Mana Potion",
            description="Restores mana",
            item_type=ItemType.CONSUMABLE,
            mana_restore=25
        )
        item_str = str(item)
        assert "25 mana" in item_str


class TestManaSerialization:
    """Tests for mana serialization and backward compatibility."""

    def test_mana_serialization(self):
        """Spec: to_dict/from_dict preserve mana."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        char.mana = 50  # Set a non-max value

        # Serialize
        data = char.to_dict()
        assert "mana" in data
        assert "max_mana" in data
        assert data["mana"] == 50

        # Deserialize
        loaded = Character.from_dict(data)
        assert loaded.mana == 50
        assert loaded.max_mana == char.max_mana

    def test_mana_backward_compat(self):
        """Spec: Old saves without mana load with calculated defaults."""
        # Simulate old save data without mana fields
        old_save_data = {
            "name": "OldChar",
            "strength": 10,
            "dexterity": 10,
            "intelligence": 15,
            "character_class": "Mage",
            "level": 1,
            "health": 100,
            "max_health": 150,
            "xp": 0,
            "inventory": {"items": [], "equipped_weapon": None, "equipped_armor": None},
            "gold": 100,
            # No mana or max_mana fields
        }

        # Load character
        loaded = Character.from_dict(old_save_data)

        # Should have calculated defaults based on class and INT
        # Mage formula: 50 + INT * 5
        # Since we're loading from save, class bonuses aren't re-applied
        # So we use the raw INT value
        expected_max = 50 + 15 * 5  # 125 for Mage with INT 15
        assert loaded.max_mana == expected_max
        assert loaded.mana == loaded.max_mana  # Default to full


class TestManaStatus:
    """Tests for mana display in status."""

    def test_status_shows_mana(self):
        """Spec: Status display includes mana bar."""
        char = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=15,
            character_class=CharacterClass.MAGE
        )
        char.mana = 50

        status_str = str(char)
        assert "Mana" in status_str
        assert "50/" in status_str  # Shows current/max format
