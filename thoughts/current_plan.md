# Companion Combat Abilities - Implementation Plan

## Spec
Add passive combat bonus based on companion bond level:
- STRANGER (0-24): No bonus
- ACQUAINTANCE (25-49): +3% attack
- TRUSTED (50-74): +5% attack
- DEVOTED (75-100): +10% attack

Bonuses stack if multiple companions (rare but possible). Display bonus in combat status.

## Files to Modify
1. `src/cli_rpg/models/companion.py` - Add `get_combat_bonus()` method
2. `src/cli_rpg/combat.py` - Apply companion bonus in `player_attack()` and `player_cast()`
3. `tests/test_companion_combat.py` - New test file

## Tests (TDD)

### tests/test_companion_combat.py

```python
"""Tests for companion combat abilities."""

class TestCompanionCombatBonus:
    """Test companion bond level combat bonuses."""

    def test_stranger_provides_no_bonus(self):
        """Companions at STRANGER level give 0% attack bonus."""
        companion = Companion(name="Test", description="Test", recruited_at="Test", bond_points=0)
        assert companion.get_combat_bonus() == 0.0

    def test_acquaintance_provides_3_percent_bonus(self):
        """Companions at ACQUAINTANCE level give 3% attack bonus."""
        companion = Companion(name="Test", description="Test", recruited_at="Test", bond_points=25)
        assert companion.get_combat_bonus() == 0.03

    def test_trusted_provides_5_percent_bonus(self):
        """Companions at TRUSTED level give 5% attack bonus."""
        companion = Companion(name="Test", description="Test", recruited_at="Test", bond_points=50)
        assert companion.get_combat_bonus() == 0.05

    def test_devoted_provides_10_percent_bonus(self):
        """Companions at DEVOTED level give 10% attack bonus."""
        companion = Companion(name="Test", description="Test", recruited_at="Test", bond_points=75)
        assert companion.get_combat_bonus() == 0.10


class TestCombatWithCompanions:
    """Test combat damage with companion bonuses applied."""

    def test_attack_damage_increased_by_companion_bonus(self):
        """Attack damage should be multiplied by (1 + companion_bonus)."""
        # Setup: character with 10 STR, no weapon, companion at DEVOTED (+10%)
        # Base damage = 10 STR - enemy defense, apply 1.10 multiplier

    def test_cast_damage_increased_by_companion_bonus(self):
        """Cast damage should be multiplied by (1 + companion_bonus)."""

    def test_multiple_companions_stack_bonuses(self):
        """Multiple companions should stack their bonuses additively."""
        # Two DEVOTED companions = +20% total

    def test_no_companions_means_no_bonus(self):
        """Combat without companions should work normally (1.0 multiplier)."""

    def test_combat_status_shows_companion_bonus(self):
        """Combat status should display active companion bonus if > 0."""
```

## Implementation Steps

1. **Add `get_combat_bonus()` to Companion model** (`src/cli_rpg/models/companion.py`):
   ```python
   # Add after BondLevel thresholds
   COMBAT_BONUSES = {
       BondLevel.STRANGER: 0.0,
       BondLevel.ACQUAINTANCE: 0.03,
       BondLevel.TRUSTED: 0.05,
       BondLevel.DEVOTED: 0.10,
   }

   # Add method to Companion class
   def get_combat_bonus(self) -> float:
       """Get combat attack bonus based on bond level.

       Returns:
           Attack damage multiplier bonus (0.0 to 0.10)
       """
       return COMBAT_BONUSES.get(self.get_bond_level(), 0.0)
   ```

2. **Modify CombatEncounter to accept companions** (`src/cli_rpg/combat.py`):
   - Add `companions: list[Companion] = None` parameter to `__init__`
   - Store as `self.companions = companions or []`
   - Add helper method `_get_companion_bonus() -> float` that sums all companion bonuses

3. **Apply bonus in `player_attack()`** (`src/cli_rpg/combat.py` ~line 494):
   ```python
   # After calculating base damage
   dmg = max(1, self.player.get_attack_power() - enemy.defense)
   # Apply companion bonus
   companion_bonus = self._get_companion_bonus()
   if companion_bonus > 0:
       dmg = int(dmg * (1 + companion_bonus))
   ```

4. **Apply bonus in `player_cast()`** (`src/cli_rpg/combat.py` ~line 584):
   ```python
   dmg = max(1, int(self.player.intelligence * 1.5))
   companion_bonus = self._get_companion_bonus()
   if companion_bonus > 0:
       dmg = int(dmg * (1 + companion_bonus))
   ```

5. **Update `get_status()` to show companion bonus** (~line 831):
   ```python
   # After status effects display
   companion_bonus = self._get_companion_bonus()
   if companion_bonus > 0:
       lines.append(f"Companion Bonus: +{int(companion_bonus * 100)}% attack")
   ```

6. **Pass companions to CombatEncounter in game_state.py** (~line 312):
   ```python
   self.current_combat = CombatEncounter(
       self.current_character, enemies=enemies, weather=self.weather,
       companions=self.companions  # Add this
   )
   ```

7. **Run tests**: `pytest tests/test_companion_combat.py -v`
