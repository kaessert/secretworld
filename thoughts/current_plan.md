# Implementation Plan: Intelligence Stat Functionality (Magic Attack)

## Problem Statement
Intelligence stat exists but has no gameplay effect. Players allocate Intelligence (1-20) during character creation, but unlike Strength (attack/HP) and Dexterity (flee chance), Intelligence provides no actual benefit.

## Approach
Add a `cast` combat command that deals magic damage scaled by Intelligence, following the established pattern of Strength → physical attack and Dexterity → flee chance.

---

## Step 1: Update Spec

**File:** `README.md` (line 32)

Change:
```markdown
   - **Intelligence**: (Future feature)
```
To:
```markdown
   - **Intelligence**: Increases magic attack damage
```

Add to Combat Commands section (after line 46):
```markdown
- `cast` - Cast a magic attack (damage based on intelligence)
```

---

## Step 2: Add Tests for Magic Attack

**File:** `tests/test_combat.py`

Add new test class after `TestPlayerDefend`:

```python
class TestPlayerCast:
    """Test player_cast() method."""

    def test_player_cast_damages_enemy_based_on_intelligence(self):
        """Spec: player_cast() should damage enemy based on player's intelligence."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=15, level=1)
        enemy = Enemy(
            name="Goblin",
            health=50,
            max_health=50,
            attack_power=5,
            defense=10,  # High defense
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        victory, message = combat.player_cast()

        # Magic damage ignores defense, scales with intelligence
        # Formula: intelligence * 1.5 (minimum 1)
        expected_damage = max(1, int(player.intelligence * 1.5))
        assert enemy.health == initial_health - expected_damage
        assert "cast" in message.lower() or "magic" in message.lower()

    def test_player_cast_handles_enemy_defeat(self):
        """Spec: player_cast() should return victory=True when enemy is defeated."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=20, level=1)
        enemy = Enemy(
            name="Goblin",
            health=5,
            max_health=30,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_cast()

        assert victory is True
        assert enemy.is_alive() is False

    def test_player_cast_continues_combat_when_enemy_survives(self):
        """Spec: player_cast() should return victory=False when enemy survives."""
        player = Character(name="Hero", strength=10, dexterity=10, intelligence=5, level=1)
        enemy = Enemy(
            name="Goblin",
            health=100,
            max_health=100,
            attack_power=5,
            defense=2,
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        victory, message = combat.player_cast()

        assert victory is False
        assert enemy.is_alive() is True

    def test_player_cast_ignores_enemy_defense(self):
        """Spec: Magic attack should bypass enemy defense."""
        player = Character(name="Hero", strength=5, dexterity=10, intelligence=10, level=1)
        enemy = Enemy(
            name="Armored Golem",
            health=50,
            max_health=50,
            attack_power=5,
            defense=100,  # Very high defense
            xp_reward=25
        )
        combat = CombatEncounter(player=player, enemy=enemy)
        combat.start()

        initial_health = enemy.health
        victory, message = combat.player_cast()

        # Cast should deal damage regardless of defense
        expected_damage = max(1, int(player.intelligence * 1.5))
        assert enemy.health == initial_health - expected_damage
        assert expected_damage > 1  # Meaningful damage despite high defense
```

---

## Step 3: Implement player_cast() Method

**File:** `src/cli_rpg/combat.py`

Add method after `player_defend()` (after line 69):

```python
    def player_cast(self) -> Tuple[bool, str]:
        """
        Player casts a magic attack.

        Magic damage is based on intelligence and ignores enemy defense.
        Formula: intelligence * 1.5 (minimum 1)

        Returns:
            Tuple of (victory, message)
            - victory: True if enemy defeated, False otherwise
            - message: Description of the spell cast
        """
        # Calculate magic damage: intelligence * 1.5, ignores defense
        damage = max(1, int(self.player.intelligence * 1.5))
        self.enemy.take_damage(damage)

        message = f"You cast a spell at {self.enemy.name} for {damage} magic damage!"

        if not self.enemy.is_alive():
            message += f"\n{self.enemy.name} has been defeated! Victory!"
            return True, message

        message += f"\n{self.enemy.name} has {self.enemy.health}/{self.enemy.max_health} HP remaining."
        return False, message
```

---

## Step 4: Add Cast Command Handler

**File:** `src/cli_rpg/main.py`

Add cast handling in `handle_combat_command()` after the flee block (after line 191):

```python
    elif command == "cast":
        victory, message = combat.player_cast()
        output = f"\n{message}"

        if victory:
            # Enemy defeated
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            game_state.current_combat = None
        else:
            # Enemy still alive, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                game_state.current_combat = None

        return output
```

Update the else clause error message (line 197):
```python
    else:
        return "\n✗ Can't do that during combat! Use: attack, defend, cast, flee, or status"
```

Update command help display in `start_game()` (after line 355):
```python
    print("  cast          - Cast a magic attack (intelligence-based)")
```

---

## Step 5: Add Cast to Known Commands

**File:** `src/cli_rpg/game_state.py`

Add "cast" to known_commands set in `parse_command()`:

```python
known_commands = {"look", "go", "save", "quit", "attack", "defend", "flee", "status", "cast"}
```

---

## Verification

```bash
# Run new magic attack tests
pytest tests/test_combat.py::TestPlayerCast -v

# Run full combat test suite to ensure no regressions
pytest tests/test_combat.py -v

# Run full test suite
pytest
```
