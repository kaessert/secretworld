"""Tests for boss fight system.

Tests boss enemy spawning, enhanced loot, and boss combat flow.
"""

import pytest
import random
from cli_rpg.models.enemy import Enemy
from cli_rpg.models.character import Character
from cli_rpg.models.item import ItemType
from cli_rpg.combat import (
    spawn_boss,
    generate_boss_loot,
    CombatEncounter,
)


class TestEnemyBossFlag:
    """Tests for Enemy model is_boss field."""

    def test_enemy_is_boss_default_false(self):
        """Verify default is_boss=False."""
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=20,
            level=1,
        )
        assert enemy.is_boss is False

    def test_enemy_is_boss_can_be_true(self):
        """Verify is_boss can be set to True."""
        boss = Enemy(
            name="Demon Lord",
            health=200,
            max_health=200,
            attack_power=25,
            defense=15,
            xp_reward=500,
            level=5,
            is_boss=True,
        )
        assert boss.is_boss is True

    def test_enemy_is_boss_serialization(self):
        """Verify to_dict/from_dict preserves is_boss flag."""
        boss = Enemy(
            name="Lich Lord",
            health=150,
            max_health=150,
            attack_power=20,
            defense=10,
            xp_reward=400,
            level=5,
            is_boss=True,
        )
        # Serialize and deserialize
        data = boss.to_dict()
        restored = Enemy.from_dict(data)
        assert restored.is_boss is True
        assert restored.name == "Lich Lord"

    def test_enemy_is_boss_backward_compatibility(self):
        """Verify from_dict handles missing is_boss field (backward compat)."""
        data = {
            "name": "Old Enemy",
            "health": 50,
            "max_health": 50,
            "attack_power": 5,
            "defense": 2,
            "xp_reward": 20,
            "level": 1,
        }
        enemy = Enemy.from_dict(data)
        assert enemy.is_boss is False


class TestSpawnBoss:
    """Tests for spawn_boss function."""

    def test_spawn_boss_stats_scaled(self):
        """Verify boss has 2x stats and 4x XP compared to normal enemies."""
        boss = spawn_boss("Dark Dungeon", level=5)

        # Based on plan: base_health = (40 + level * 25) * 2
        # level 5: (40 + 5*25) * 2 = 165 * 2 = 330
        expected_health = (40 + 5 * 25) * 2
        assert boss.max_health == expected_health
        assert boss.health == expected_health

        # base_attack = (5 + level * 3) * 2
        # level 5: (5 + 5*3) * 2 = 20 * 2 = 40
        expected_attack = (5 + 5 * 3) * 2
        assert boss.attack_power == expected_attack

        # base_defense = (2 + level * 2) * 2
        # level 5: (2 + 5*2) * 2 = 12 * 2 = 24
        expected_defense = (2 + 5 * 2) * 2
        assert boss.defense == expected_defense

        # xp_reward = (30 + level * 20) * 4
        # level 5: (30 + 5*20) * 4 = 130 * 4 = 520
        expected_xp = (30 + 5 * 20) * 4
        assert boss.xp_reward == expected_xp

    def test_spawn_boss_is_boss_flag(self):
        """Verify spawned boss has is_boss=True."""
        boss = spawn_boss("Ancient Ruins", level=3)
        assert boss.is_boss is True

    def test_spawn_boss_location_category_dungeon(self):
        """Verify dungeon category uses dungeon boss templates."""
        random.seed(42)  # Fix seed for reproducibility
        boss = spawn_boss("Dark Hall", level=5, location_category="dungeon")
        dungeon_bosses = ["Lich Lord", "Dark Champion", "Demon Lord"]
        assert boss.name in dungeon_bosses

    def test_spawn_boss_location_category_ruins(self):
        """Verify ruins category uses ruins boss templates."""
        random.seed(42)
        boss = spawn_boss("Old Temple", level=5, location_category="ruins")
        ruins_bosses = ["Ancient Guardian", "Cursed Pharaoh", "Shadow King"]
        assert boss.name in ruins_bosses

    def test_spawn_boss_location_category_cave(self):
        """Verify cave category uses cave boss templates."""
        random.seed(42)
        boss = spawn_boss("Deep Cave", level=5, location_category="cave")
        cave_bosses = ["Cave Troll King", "Elder Wyrm", "Crystal Golem"]
        assert boss.name in cave_bosses

    def test_spawn_boss_default_category(self):
        """Verify default/unknown category uses default boss templates."""
        random.seed(42)
        boss = spawn_boss("Unknown Area", level=5, location_category="unknown")
        default_bosses = ["Archdemon", "Overlord", "Chaos Beast"]
        assert boss.name in default_bosses

    def test_spawn_boss_has_ascii_art(self):
        """Verify boss has ASCII art."""
        boss = spawn_boss("Dungeon", level=5, location_category="dungeon")
        assert boss.ascii_art is not None
        assert len(boss.ascii_art) > 0


class TestBossLoot:
    """Tests for generate_boss_loot function."""

    def test_generate_boss_loot_guaranteed(self):
        """Verify 100% drop rate from bosses."""
        boss = Enemy(
            name="Demon Lord",
            health=200,
            max_health=200,
            attack_power=25,
            defense=15,
            xp_reward=500,
            level=5,
            is_boss=True,
        )
        # Run multiple times to verify guaranteed drop
        for _ in range(10):
            loot = generate_boss_loot(boss, level=5)
            assert loot is not None

    def test_generate_boss_loot_enhanced_weapon_stats(self):
        """Verify boss weapon loot has enhanced damage bonus."""
        boss = Enemy(
            name="Lich Lord",
            health=150,
            max_health=150,
            attack_power=20,
            defense=10,
            xp_reward=400,
            level=5,
            is_boss=True,
        )
        random.seed(42)  # Fix seed to get weapon
        # Generate multiple loots to find a weapon
        weapons = []
        for _ in range(50):
            loot = generate_boss_loot(boss, level=5)
            if loot.item_type == ItemType.WEAPON:
                weapons.append(loot)
                break

        if weapons:
            weapon = weapons[0]
            # Enhanced stats: damage_bonus = level + random(5, 10)
            # For level 5: 5 + 5-10 = 10-15
            assert weapon.damage_bonus >= 10

    def test_generate_boss_loot_unique_prefixes(self):
        """Verify boss loot has legendary-tier prefixes."""
        boss = Enemy(
            name="Demon Lord",
            health=200,
            max_health=200,
            attack_power=25,
            defense=15,
            xp_reward=500,
            level=5,
            is_boss=True,
        )
        legendary_prefixes = ["Legendary", "Ancient", "Cursed", "Divine", "Epic"]

        # Generate multiple loots to check prefixes
        found_legendary = False
        for _ in range(50):
            loot = generate_boss_loot(boss, level=5)
            if loot.item_type in [ItemType.WEAPON, ItemType.ARMOR]:
                for prefix in legendary_prefixes:
                    if loot.name.startswith(prefix):
                        found_legendary = True
                        break
            if found_legendary:
                break

        assert found_legendary, "Boss loot should have legendary prefixes"


class TestBossCombatFlow:
    """Tests for boss combat integration."""

    def test_boss_combat_intro_message(self):
        """Verify 'BOSS appears' messaging for boss encounters."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        boss = Enemy(
            name="Demon Lord",
            health=200,
            max_health=200,
            attack_power=25,
            defense=15,
            xp_reward=500,
            level=5,
            is_boss=True,
        )
        combat = CombatEncounter(player, enemies=[boss])
        intro = combat.start()
        assert "BOSS" in intro
        assert "Demon Lord" in intro

    def test_boss_combat_non_boss_intro(self):
        """Verify normal enemies don't get BOSS messaging."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=2,
            xp_reward=20,
            level=1,
            is_boss=False,
        )
        combat = CombatEncounter(player, enemies=[enemy])
        intro = combat.start()
        assert "BOSS" not in intro
        assert "Goblin" in intro

    def test_boss_combat_end_uses_boss_loot(self):
        """Verify boss loot generation on victory."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        boss = Enemy(
            name="Demon Lord",
            health=1,  # Low health for quick defeat
            max_health=200,
            attack_power=25,
            defense=0,  # No defense for reliable attack
            xp_reward=500,
            level=5,
            is_boss=True,
        )
        combat = CombatEncounter(player, enemies=[boss])
        combat.start()

        # Defeat the boss
        boss.take_damage(1)
        assert not boss.is_alive()

        # End combat
        result = combat.end_combat(victory=True)

        # Boss loot is guaranteed, so check for item drop message
        assert "You found:" in result or "inventory is full" in result

    def test_boss_combat_quest_tracking(self):
        """Verify boss kills trigger KILL quests."""
        from cli_rpg.models.quest import Quest, QuestStatus, ObjectiveType

        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)

        # Add a kill quest for the boss
        quest = Quest(
            name="Slay the Demon Lord",
            description="Defeat the Demon Lord",
            objective_type=ObjectiveType.KILL,
            target="Demon Lord",
            target_count=1,
            gold_reward=100,
            xp_reward=200,
            status=QuestStatus.ACTIVE,
        )
        player.quests.append(quest)

        # Record the kill
        messages = player.record_kill("Demon Lord")

        # Quest should be complete
        assert quest.status == QuestStatus.READY_TO_TURN_IN
        assert len(messages) > 0


class TestBossEncounters:
    """Tests for boss encounter triggering."""

    def test_boss_encounter_single_enemy(self):
        """Verify boss fights are solo (no additional enemies)."""
        boss = spawn_boss("Dungeon", level=5, location_category="dungeon")
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        combat = CombatEncounter(player, enemies=[boss])

        # Boss encounters should have exactly 1 enemy
        assert len(combat.enemies) == 1
        assert combat.enemies[0].is_boss is True
