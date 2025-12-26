# Telegraphed Enemy Attacks Implementation Plan

## Feature Spec
Add a telegraphed attack system where powerful enemies (bosses) announce their next attack the turn before executing it. This gives players a chance to `defend`, `block`, or `parry` strategically, adding depth to combat without changing core mechanics.

**Behavior:**
- Boss enemies have `special_attacks` - powerful moves that deal extra damage with bonus effects
- Before using a special attack, the boss "telegraphs" it with a warning message
- Players see the warning at the end of `enemy_turn()` and can react next turn
- If player defends/blocks/parries when the special hits, they mitigate more damage
- If player attacks or ignores the warning, they take full special attack damage
- Non-boss enemies continue to attack normally (no telegraph)

## Files to Modify

### 1. `src/cli_rpg/models/enemy.py`
- Add `SpecialAttack` dataclass with: `name`, `damage_multiplier`, `telegraph_message`, `hit_message`, `effect_type` (optional status effect), `effect_chance`
- Add `special_attacks: List[SpecialAttack]` field to Enemy dataclass
- Add `telegraphed_attack: Optional[str]` field to track pending special attack name
- Update `to_dict()` and `from_dict()` for persistence

### 2. `src/cli_rpg/combat.py`
- Modify `enemy_turn()` to:
  1. Check if boss has `telegraphed_attack` set from previous turn
  2. If yes: execute the special attack with bonus damage/effects, then clear it
  3. After normal attack: 30% chance for bosses to telegraph next special
  4. Append telegraph message to turn output if telegraphing
- Modify `spawn_boss()` to include special attacks for each boss type:
  - Stone Sentinel: "Crushing Blow" (2x damage, stun)
  - Elder Treant: "Nature's Wrath" (1.5x damage, guaranteed poison)
  - Drowned Overseer: "Tidal Surge" (1.5x damage, freeze)
  - Generic bosses: "Devastating Strike" (1.75x damage)

### 3. `tests/test_telegraphed_attacks.py` (new file)
Tests to write first:
- `test_boss_can_telegraph_special_attack`: Boss sets telegraphed_attack, message appears
- `test_telegraphed_attack_executes_next_turn`: Special attack fires after telegraph
- `test_telegraphed_attack_bonus_damage`: Special attack deals multiplied damage
- `test_defend_reduces_telegraphed_damage`: Defending still mitigates special
- `test_block_reduces_telegraphed_damage`: Blocking provides 75% mitigation
- `test_non_boss_no_telegraph`: Regular enemies never telegraph
- `test_telegraph_cleared_after_execution`: telegraphed_attack reset to None after use
- `test_special_attack_applies_effect`: Status effects apply on special hit
- `test_special_attack_serialization`: to_dict/from_dict preserves special attacks

## Implementation Steps

1. **Add SpecialAttack dataclass to enemy.py**
   ```python
   @dataclass
   class SpecialAttack:
       name: str
       damage_multiplier: float  # 1.5 = 50% more damage
       telegraph_message: str    # "The boss raises its weapon high..."
       hit_message: str          # "brings down a devastating blow"
       effect_type: Optional[str] = None  # "stun", "poison", "freeze"
       effect_damage: int = 0
       effect_duration: int = 0
       effect_chance: float = 1.0  # 1.0 = guaranteed
   ```

2. **Update Enemy dataclass**
   - Add `special_attacks: List[SpecialAttack] = field(default_factory=list)`
   - Add `telegraphed_attack: Optional[str] = None`
   - Update `to_dict()` and `from_dict()` for persistence

3. **Write tests in tests/test_telegraphed_attacks.py** (TDD)

4. **Modify enemy_turn() in combat.py**
   - At loop start for each boss: check for `telegraphed_attack`
   - If set: find matching SpecialAttack, execute with multiplied damage + effects
   - After normal attack for bosses: 30% chance to telegraph (sets `telegraphed_attack` and appends message)

5. **Update spawn_boss() with special attacks**
   ```python
   # Stone Sentinel
   special_attacks=[
       SpecialAttack(
           name="Crushing Blow",
           damage_multiplier=2.0,
           telegraph_message="The Stone Sentinel raises its massive fist high...",
           hit_message="brings down a CRUSHING BLOW",
           effect_type="stun",
           effect_duration=1,
           effect_chance=0.75,
       )
   ]
   ```

6. **Run tests**
   ```bash
   pytest tests/test_telegraphed_attacks.py -v
   pytest tests/test_combat.py -v
   pytest --cov=src/cli_rpg
   ```
