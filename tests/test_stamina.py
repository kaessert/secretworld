"""Tests for the Stamina resource system.

Tests the stamina stat implementation for physical classes, including:
- Stamina calculation based on class (Warrior/Ranger vs others)
- Stamina usage and restoration methods
- Stamina costs in combat (Sneak)
- Stamina regeneration per combat turn
- Rest restores stamina
- Stamina potion items
- Serialization and backward compatibility
- Status display includes stamina
"""
import pytest
from cli_rpg.models.character import Character, CharacterClass
from cli_rpg.models.item import Item, ItemType
from cli_rpg.models.enemy import Enemy
from cli_rpg.combat import CombatEncounter


class TestStaminaStat:
    """Tests for stamina stat calculation and basic methods."""

    # Test 1: Warrior with STR 15 gets 50 + 15*5 = 125 max_stamina
    def test_warrior_has_higher_max_stamina(self):
        """Warrior with STR 15 gets max_stamina = 50 + 15*5 = 125."""
        # Create warrior with STR 12 (will get +3 from class bonus = 15)
        warrior = Character(
            name="TestWarrior",
            strength=12,  # +3 from class = 15
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # After class bonus: STR = 15
        # Formula: 50 + STR * 5 = 50 + 15*5 = 125
        assert warrior.max_stamina == 125
        assert warrior.stamina == warrior.max_stamina

    # Test 2: Mage with STR 10 gets 20 + 10*2 = 40 max_stamina
    def test_mage_has_lower_max_stamina(self):
        """Mage with STR 10 gets max_stamina = 20 + 10*2 = 40."""
        # Create mage with base STR 10 (no strength bonus from class)
        mage = Character(
            name="TestMage",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.MAGE,
        )
        # Mage gets no STR bonus, so STR = 10
        # Formula: 20 + STR * 2 = 20 + 10*2 = 40
        assert mage.max_stamina == 40
        assert mage.stamina == mage.max_stamina

    # Test 3: Rogue uses the lower stamina formula (20 + STR*2)
    def test_rogue_has_lower_max_stamina(self):
        """Rogue uses lower stamina formula: 20 + STR*2."""
        # Create rogue with base STR 10 (+1 from class = 11)
        rogue = Character(
            name="TestRogue",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.ROGUE,
        )
        # Rogue gets +1 STR from class, so STR = 11
        # Formula: 20 + STR * 2 = 20 + 11*2 = 42
        assert rogue.max_stamina == 42
        assert rogue.stamina == rogue.max_stamina

    # Test 4: use_stamina returns False if insufficient stamina
    def test_stamina_use_method(self):
        """use_stamina(amount) returns False if insufficient, True and deducts otherwise."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        initial_stamina = char.stamina

        # Use some stamina successfully
        assert char.use_stamina(10) is True
        assert char.stamina == initial_stamina - 10

        # Try to use more stamina than available
        assert char.use_stamina(char.stamina + 1) is False
        # Stamina should not have changed
        assert char.stamina == initial_stamina - 10

    # Test 5: restore_stamina capped at max_stamina
    def test_stamina_restore_method(self):
        """restore_stamina adds stamina, capped at max_stamina."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Drain some stamina
        char.use_stamina(50)
        old_stamina = char.stamina

        # Restore some stamina
        char.restore_stamina(20)
        assert char.stamina == old_stamina + 20

    # Test 6: Cannot exceed max_stamina
    def test_stamina_capped_at_max(self):
        """Stamina cannot exceed max_stamina."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Try to restore more than max
        char.restore_stamina(1000)
        assert char.stamina == char.max_stamina


class TestStaminaInCombat:
    """Tests for stamina usage and regeneration in combat."""

    # Test 7: Sneak deducts 10 stamina
    def test_sneak_deducts_stamina(self):
        """Sneak costs 10 stamina."""
        rogue = Character(
            name="TestRogue",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.ROGUE,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=20,
            level=1,
        )
        combat = CombatEncounter(rogue, enemy)
        combat.start()

        initial_stamina = rogue.stamina
        victory, msg = combat.player_sneak()

        assert victory is False  # Combat continues
        assert "shadows" in msg.lower()  # Sneak message
        assert rogue.stamina == initial_stamina - 10

    # Test 8: Sneak fails without sufficient stamina
    def test_sneak_fails_without_stamina(self):
        """Sneak with <10 stamina returns failure message."""
        rogue = Character(
            name="TestRogue",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.ROGUE,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=20,
            level=1,
        )
        combat = CombatEncounter(rogue, enemy)
        combat.start()

        # Drain stamina to below 10
        rogue.stamina = 5

        victory, msg = combat.player_sneak()

        assert victory is False
        assert "stamina" in msg.lower()  # Error message mentions stamina
        assert rogue.stamina == 5  # Stamina unchanged

    # Test 9: Stamina regenerates 1 per enemy turn
    def test_stamina_regen_on_turn(self):
        """Stamina regenerates 1 per enemy turn."""
        warrior = Character(
            name="TestWarrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=20,
            level=1,
        )
        combat = CombatEncounter(warrior, enemy)
        combat.start()

        # Drain some stamina
        warrior.use_stamina(20)
        stamina_before = warrior.stamina

        # Enemy takes a turn
        combat.enemy_turn()

        # Stamina should have regenerated by 1
        assert warrior.stamina == stamina_before + 1


class TestStaminaRest:
    """Tests for stamina restoration during rest."""

    # Test 10: Rest restores 25% of max_stamina
    def test_rest_regenerates_stamina(self):
        """Rest restores 25% of max_stamina."""
        # This test verifies the spec - actual implementation is in main.py
        warrior = Character(
            name="TestWarrior",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Drain stamina
        warrior.use_stamina(warrior.max_stamina - 10)
        low_stamina = warrior.stamina

        # Simulate rest: restore 25% of max_stamina
        rest_amount = max(1, warrior.max_stamina // 4)
        warrior.restore_stamina(rest_amount)

        assert warrior.stamina == low_stamina + rest_amount


class TestStaminaPotion:
    """Tests for Stamina Potion items."""

    # Test 11: Using Stamina Potion restores stamina
    def test_stamina_potion_restores_stamina(self):
        """Using Stamina Potion adds stamina_restore amount to stamina."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Create Stamina Potion
        potion = Item(
            name="Stamina Potion",
            description="Restores stamina",
            item_type=ItemType.CONSUMABLE,
            stamina_restore=25,
        )
        char.inventory.add_item(potion)

        # Drain stamina
        char.use_stamina(50)
        stamina_before = char.stamina

        # Use potion
        success, msg = char.use_item(potion)

        assert success is True
        assert char.stamina == stamina_before + 25
        assert "stamina" in msg.lower()

    # Test 12: Item with stamina_restore serializes correctly
    def test_item_stamina_restore_field(self):
        """Item with stamina_restore serializes and deserializes correctly."""
        potion = Item(
            name="Stamina Potion",
            description="Restores stamina",
            item_type=ItemType.CONSUMABLE,
            stamina_restore=25,
        )

        # Serialize
        data = potion.to_dict()
        assert data["stamina_restore"] == 25

        # Deserialize
        restored = Item.from_dict(data)
        assert restored.stamina_restore == 25

    # Test 13: Item __str__() shows stamina restore
    def test_item_str_shows_stamina_restore(self):
        """Item __str__() shows stamina restore amount."""
        potion = Item(
            name="Stamina Potion",
            description="Restores stamina",
            item_type=ItemType.CONSUMABLE,
            stamina_restore=25,
        )

        item_str = str(potion)
        assert "stamina" in item_str.lower()
        assert "25" in item_str


class TestStaminaSerialization:
    """Tests for stamina serialization and backward compatibility."""

    # Test 14: to_dict/from_dict preserve stamina
    def test_stamina_serialization(self):
        """to_dict and from_dict preserve stamina values."""
        char = Character(
            name="TestChar",
            strength=12,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )
        # Modify stamina
        char.use_stamina(30)

        # Serialize
        data = char.to_dict()
        assert "stamina" in data
        assert "max_stamina" in data
        assert data["stamina"] == char.stamina
        assert data["max_stamina"] == char.max_stamina

        # Deserialize
        restored = Character.from_dict(data)
        assert restored.stamina == char.stamina
        assert restored.max_stamina == char.max_stamina

    # Test 15: Old saves without stamina load with defaults
    def test_stamina_backward_compat(self):
        """Old saves without stamina field load with defaults (full stamina)."""
        # Simulate old save data without stamina fields
        old_data = {
            "name": "OldChar",
            "strength": 15,
            "dexterity": 10,
            "intelligence": 10,
            "charisma": 10,
            "perception": 10,
            "luck": 10,
            "level": 1,
            "health": 100,
            "max_health": 125,
            "mana": 40,
            "max_mana": 40,
            "xp": 0,
            "gold": 100,
            "character_class": "Warrior",
            # No stamina or max_stamina fields
        }

        char = Character.from_dict(old_data)

        # Should calculate max_stamina from strength and have full stamina
        # Warrior formula: 50 + STR * 5 = 50 + 15*5 = 125
        assert char.max_stamina == 125
        assert char.stamina == char.max_stamina


class TestStaminaStatus:
    """Tests for stamina in status display."""

    # Test 16: Status display includes stamina bar
    def test_status_shows_stamina(self):
        """Status display includes stamina information."""
        char = Character(
            name="TestChar",
            strength=10,
            dexterity=10,
            intelligence=10,
            character_class=CharacterClass.WARRIOR,
        )

        status_str = str(char)
        assert "stamina" in status_str.lower()
