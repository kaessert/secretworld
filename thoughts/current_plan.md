# Implementation Plan: Elemental Strengths and Weaknesses

## Summary

Add elemental damage types and resistance/weakness modifiers to the combat system. Fire creatures take extra damage from ice, ice creatures take extra damage from fire, etc.

## Specification

### Element Types
- **FIRE**: Fire creatures, dragons, flame elementals
- **ICE**: Yetis, frost creatures, ice elementals
- **POISON**: Spiders, snakes, serpents, vipers
- **PHYSICAL**: Default for non-elemental creatures

### Damage Modifiers
| Attacker Element | Defender Element | Modifier |
|-----------------|------------------|----------|
| FIRE            | ICE              | 1.5x (strong) |
| ICE             | FIRE             | 1.5x (strong) |
| FIRE            | FIRE             | 0.5x (resist) |
| ICE             | ICE              | 0.5x (resist) |
| POISON          | POISON           | 0.5x (resist) |
| Any             | Any (same)       | 0.5x (resist) |
| Any             | Any (different, non-opposing) | 1.0x (neutral) |

### Application Points
1. **Fireball spell** (fire damage) → bonus vs ice enemies, reduced vs fire enemies
2. **Ice Bolt spell** (ice damage) → bonus vs fire enemies, reduced vs ice enemies
3. **Burn DOT damage** → reduced on fire-resistant enemies
4. **Freeze duration** → extended on fire-weak enemies, shortened on ice-resistant enemies
5. **Enemy elemental attacks** → bonus/reduced vs player elemental buffs (future)

## Implementation Steps

### Step 1: Create ElementType enum and add to Enemy model
**File**: `src/cli_rpg/models/enemy.py`

```python
from enum import Enum

class ElementType(Enum):
    PHYSICAL = "physical"  # Default
    FIRE = "fire"
    ICE = "ice"
    POISON = "poison"
```

- Add `element_type: ElementType = ElementType.PHYSICAL` field to Enemy dataclass
- Update `to_dict()` and `from_dict()` for serialization (backward compatible)

### Step 2: Create elemental damage calculation module
**File**: `src/cli_rpg/elements.py` (new file)

```python
from cli_rpg.models.enemy import ElementType

# Weakness relations: attacker → list of weak defender types
WEAKNESSES = {
    ElementType.FIRE: [ElementType.ICE],
    ElementType.ICE: [ElementType.FIRE],
}

# Resistance: same element resists itself
RESISTANCES = {
    ElementType.FIRE: [ElementType.FIRE],
    ElementType.ICE: [ElementType.ICE],
    ElementType.POISON: [ElementType.POISON],
}

WEAKNESS_MULTIPLIER = 1.5
RESISTANCE_MULTIPLIER = 0.5

def calculate_elemental_modifier(
    attacker_element: ElementType,
    defender_element: ElementType
) -> tuple[float, str]:
    """
    Calculate damage modifier and message based on elemental interaction.

    Returns:
        Tuple of (modifier, message) where message describes the interaction
    """
    if defender_element in WEAKNESSES.get(attacker_element, []):
        return WEAKNESS_MULTIPLIER, "It's super effective!"
    if defender_element in RESISTANCES.get(attacker_element, []):
        return RESISTANCE_MULTIPLIER, "It's not very effective..."
    return 1.0, ""
```

### Step 3: Assign element types in spawn_enemy
**File**: `src/cli_rpg/combat.py` (modify `spawn_enemy` function ~line 1979)

Add element type inference based on enemy name patterns (same patterns used for status effects):
```python
# After existing status effect assignment code (~line 2010)
element_type = ElementType.PHYSICAL  # default
if any(term in enemy_name_lower for term in ["fire", "dragon", "elemental", "flame", "inferno"]):
    element_type = ElementType.FIRE
elif any(term in enemy_name_lower for term in ["yeti", "ice", "frost", "frozen", "blizzard"]):
    element_type = ElementType.ICE
elif any(term in enemy_name_lower for term in ["spider", "snake", "serpent", "viper"]):
    element_type = ElementType.POISON
```

### Step 4: Apply elemental modifiers to Fireball
**File**: `src/cli_rpg/combat.py` (modify `player_fireball` ~line 1061)

```python
# After base damage calculation
from cli_rpg.elements import calculate_elemental_modifier, ElementType

# Calculate elemental modifier
elem_mod, elem_msg = calculate_elemental_modifier(ElementType.FIRE, enemy.element_type)
dmg = int(dmg * elem_mod)

# Add message if there was an elemental effect
if elem_msg:
    message += f" {elem_msg}"
```

### Step 5: Apply elemental modifiers to Ice Bolt
**File**: `src/cli_rpg/combat.py` (modify `player_ice_bolt` ~line 1137)

Same pattern as Fireball but with `ElementType.ICE`.

### Step 6: Write tests
**File**: `tests/test_elements.py` (new file)

```python
"""Tests for elemental damage system."""

import pytest
from cli_rpg.models.enemy import Enemy, ElementType
from cli_rpg.elements import calculate_elemental_modifier, WEAKNESS_MULTIPLIER, RESISTANCE_MULTIPLIER
from cli_rpg.combat import spawn_enemy

class TestElementType:
    """Tests for ElementType enum on Enemy model."""

    def test_enemy_default_element_is_physical(self):
        """Enemies default to PHYSICAL element."""
        enemy = Enemy(name="Wolf", health=50, max_health=50, attack_power=10, defense=2, xp_reward=30)
        assert enemy.element_type == ElementType.PHYSICAL

    def test_enemy_element_serialization(self):
        """Element type serializes and deserializes correctly."""
        enemy = Enemy(name="Fire Elemental", health=50, max_health=50, attack_power=10, defense=2, xp_reward=30, element_type=ElementType.FIRE)
        data = enemy.to_dict()
        assert data["element_type"] == "fire"
        restored = Enemy.from_dict(data)
        assert restored.element_type == ElementType.FIRE

    def test_enemy_element_backward_compatible(self):
        """Old saves without element_type load as PHYSICAL."""
        data = {"name": "Wolf", "health": 50, "max_health": 50, "attack_power": 10, "defense": 2, "xp_reward": 30}
        restored = Enemy.from_dict(data)
        assert restored.element_type == ElementType.PHYSICAL


class TestElementalModifiers:
    """Tests for elemental damage calculation."""

    def test_fire_strong_vs_ice(self):
        """Fire deals bonus damage to ice enemies."""
        mod, msg = calculate_elemental_modifier(ElementType.FIRE, ElementType.ICE)
        assert mod == WEAKNESS_MULTIPLIER
        assert msg != ""

    def test_ice_strong_vs_fire(self):
        """Ice deals bonus damage to fire enemies."""
        mod, msg = calculate_elemental_modifier(ElementType.ICE, ElementType.FIRE)
        assert mod == WEAKNESS_MULTIPLIER

    def test_fire_resists_fire(self):
        """Fire enemies resist fire damage."""
        mod, msg = calculate_elemental_modifier(ElementType.FIRE, ElementType.FIRE)
        assert mod == RESISTANCE_MULTIPLIER

    def test_ice_resists_ice(self):
        """Ice enemies resist ice damage."""
        mod, msg = calculate_elemental_modifier(ElementType.ICE, ElementType.ICE)
        assert mod == RESISTANCE_MULTIPLIER

    def test_poison_resists_poison(self):
        """Poison enemies resist poison damage."""
        mod, msg = calculate_elemental_modifier(ElementType.POISON, ElementType.POISON)
        assert mod == RESISTANCE_MULTIPLIER

    def test_physical_neutral_vs_all(self):
        """Physical damage is neutral against all types."""
        for element in ElementType:
            mod, msg = calculate_elemental_modifier(ElementType.PHYSICAL, element)
            assert mod == 1.0
            assert msg == ""


class TestSpawnEnemyElements:
    """Tests for element type assignment in spawn_enemy."""

    def test_fire_enemy_gets_fire_element(self):
        """Fire enemies are assigned FIRE element."""
        enemy = spawn_enemy("dungeon", 1, location_category="dungeon")
        # Force a fire enemy name for testing
        enemy.name = "Fire Elemental"
        # Re-test with actual spawn
        for _ in range(100):
            enemy = spawn_enemy("volcano", 1, location_category="dungeon")
            if "fire" in enemy.name.lower() or "flame" in enemy.name.lower():
                assert enemy.element_type == ElementType.FIRE
                return

    def test_ice_enemy_gets_ice_element(self):
        """Ice enemies are assigned ICE element."""
        for _ in range(100):
            enemy = spawn_enemy("tundra", 1, location_category="mountain")
            if "yeti" in enemy.name.lower() or "frost" in enemy.name.lower() or "ice" in enemy.name.lower():
                assert enemy.element_type == ElementType.ICE
                return
```

### Step 7: Integration tests for combat
**File**: `tests/test_elements.py` (add to same file)

```python
class TestCombatElementalDamage:
    """Integration tests for elemental damage in combat."""

    @pytest.fixture
    def mage(self):
        from cli_rpg.models.character import Character, CharacterClass
        char = Character(name="TestMage", strength=10, dexterity=10, intelligence=15)
        char.character_class = CharacterClass.MAGE
        char.mana = 100
        char.max_mana = 100
        return char

    @pytest.fixture
    def ice_enemy(self):
        return Enemy(name="Frost Giant", health=100, max_health=100, attack_power=10, defense=2, xp_reward=50, element_type=ElementType.ICE)

    @pytest.fixture
    def fire_enemy(self):
        return Enemy(name="Fire Elemental", health=100, max_health=100, attack_power=10, defense=2, xp_reward=50, element_type=ElementType.FIRE)

    def test_fireball_bonus_damage_vs_ice(self, mage, ice_enemy):
        """Fireball deals 1.5x damage to ice enemies."""
        from cli_rpg.combat import CombatEncounter
        combat = CombatEncounter(player=mage, enemy=ice_enemy)
        combat.start()
        initial_health = ice_enemy.health
        combat.player_fireball()
        damage = initial_health - ice_enemy.health
        # Base damage: INT * 2.5 = 15 * 2.5 = 37.5 -> 37
        # With 1.5x modifier: 37 * 1.5 = 55.5 -> 55
        assert damage >= 50  # Should be significantly higher than base

    def test_fireball_reduced_vs_fire(self, mage, fire_enemy):
        """Fireball deals 0.5x damage to fire enemies."""
        from cli_rpg.combat import CombatEncounter
        combat = CombatEncounter(player=mage, enemy=fire_enemy)
        combat.start()
        initial_health = fire_enemy.health
        combat.player_fireball()
        damage = initial_health - fire_enemy.health
        # Base damage: 37, with 0.5x: 18
        assert damage <= 25  # Should be lower than base

    def test_ice_bolt_bonus_damage_vs_fire(self, mage, fire_enemy):
        """Ice Bolt deals 1.5x damage to fire enemies."""
        from cli_rpg.combat import CombatEncounter
        combat = CombatEncounter(player=mage, enemy=fire_enemy)
        combat.start()
        initial_health = fire_enemy.health
        combat.player_ice_bolt()
        damage = initial_health - fire_enemy.health
        # Base: INT * 2.0 = 30, with 1.5x: 45
        assert damage >= 40
```

## File Summary

| File | Action | Description |
|------|--------|-------------|
| `src/cli_rpg/models/enemy.py` | Modify | Add ElementType enum and element_type field |
| `src/cli_rpg/elements.py` | Create | New module for elemental calculations |
| `src/cli_rpg/combat.py` | Modify | Apply modifiers in Fireball, Ice Bolt, spawn_enemy |
| `tests/test_elements.py` | Create | Comprehensive test suite |

## Test Verification

Run tests after implementation:
```bash
pytest tests/test_elements.py -v
pytest tests/test_status_effects.py -v  # Ensure no regressions
pytest tests/test_combat.py -v  # Ensure no regressions
```

## Notes

- ElementType is separate from status effect capabilities (an enemy can be FIRE element AND apply burn)
- Physical attacks remain neutral - only spells/abilities with explicit element types benefit
- Future: Add elemental weapons, player elemental buffs, more element types (lightning, earth)
