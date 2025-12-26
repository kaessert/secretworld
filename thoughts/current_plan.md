# Weapon Proficiencies System - Implementation Plan

## Feature Spec

Implement a weapon proficiency system where using a weapon type (sword, axe, dagger, mace, bow, staff) increases skill with it, providing damage bonuses and eventually unlocking special moves.

### Weapon Types
- **Sword**: Balanced, medium damage
- **Axe**: High damage, slower
- **Dagger**: Fast, lower damage, crit bonus
- **Mace**: Armor penetration (ignores some defense)
- **Bow**: Ranged (first strike bonus)
- **Staff**: Magic-focused (spell damage bonus)

### Proficiency Levels (0-100 XP per type)
| Level | XP Required | Damage Bonus | Special |
|-------|-------------|--------------|---------|
| Novice | 0 | +0% | - |
| Apprentice | 25 | +5% | - |
| Journeyman | 50 | +10% | Unlock special move |
| Expert | 75 | +15% | - |
| Master | 100 | +20% | Enhanced special move |

### Special Moves (unlocked at Journeyman, enhanced at Master)
- **Sword - Riposte**: Counter-attack after successful defend (costs 10 stamina)
- **Axe - Cleave**: Deal 50% damage to second enemy (costs 15 stamina)
- **Dagger - Expose**: Next attack has +25% crit chance (costs 10 stamina)
- **Mace - Crush**: Ignore 50% of enemy defense (costs 15 stamina)
- **Bow - Aimed Shot**: Deal 1.5x damage, can't be dodged (costs 15 stamina)
- **Staff - Channel**: Next spell costs 50% less mana (costs 10 stamina)

---

## Implementation Steps

### 1. Create WeaponType enum and proficiency model
**File**: `src/cli_rpg/models/weapon_proficiency.py` (new file)

```python
class WeaponType(Enum):
    SWORD = "sword"
    AXE = "axe"
    DAGGER = "dagger"
    MACE = "mace"
    BOW = "bow"
    STAFF = "staff"
    UNKNOWN = "unknown"  # For weapons that don't fit categories

class ProficiencyLevel(Enum):
    NOVICE = "Novice"
    APPRENTICE = "Apprentice"
    JOURNEYMAN = "Journeyman"
    EXPERT = "Expert"
    MASTER = "Master"

@dataclass
class WeaponProficiency:
    weapon_type: WeaponType
    xp: int = 0  # 0-100

    def get_level() -> ProficiencyLevel
    def get_damage_bonus() -> float  # Returns multiplier (1.0, 1.05, 1.10, 1.15, 1.20)
    def can_use_special() -> bool  # True if Journeyman+
    def is_special_enhanced() -> bool  # True if Master
    def gain_xp(amount: int) -> Optional[str]  # Returns level-up message
    def to_dict() / from_dict()  # Serialization
```

### 2. Add weapon_type field to Item model
**File**: `src/cli_rpg/models/item.py`

- Add `weapon_type: Optional[WeaponType] = None` field
- Update `to_dict()` and `from_dict()` for serialization
- Update `__str__()` to show weapon type for weapons

### 3. Add proficiencies dict to Character model
**File**: `src/cli_rpg/models/character.py`

- Add `weapon_proficiencies: Dict[WeaponType, WeaponProficiency]` field
- Add `get_weapon_proficiency(weapon_type)` method
- Add `gain_weapon_xp(weapon_type, amount)` method (called after attacks)
- Update `to_dict()` and `from_dict()` for serialization (backward compatible)

### 4. Integrate proficiency damage bonus in combat
**File**: `src/cli_rpg/combat.py`

- In `player_attack()`: Get equipped weapon type, apply proficiency damage bonus
- After successful attack: Call `player.gain_weapon_xp(weapon_type, 1)`
- XP gain: 1 XP per attack with that weapon type

### 5. Add weapon type inference for loot generation
**File**: `src/cli_rpg/combat.py`

- Update `generate_loot()` to assign weapon_type based on item name
- Mapping: "Sword" -> SWORD, "Dagger" -> DAGGER, "Axe" -> AXE, etc.

### 6. Add `proficiency` command to view proficiencies
**File**: `src/cli_rpg/main.py`

- Add `proficiency` / `prof` command to show weapon proficiency levels
- Display: weapon type, current level, XP progress bar, damage bonus

### 7. Add special move commands (Phase 2 - Future)
**Note**: Special moves deferred to keep initial implementation focused. The proficiency system tracks progress; special moves can be added later.

---

## Test Plan

### Unit Tests (`tests/test_weapon_proficiency.py`)

1. **WeaponProficiency model tests**:
   - Test XP gain and level transitions (0→25→50→75→100)
   - Test damage bonus returns correct values for each level
   - Test `can_use_special()` at each level
   - Test serialization/deserialization

2. **Character proficiency tracking tests**:
   - Test `get_weapon_proficiency()` returns default Novice for new types
   - Test `gain_weapon_xp()` correctly updates proficiency
   - Test proficiencies persist through save/load

3. **Item weapon_type tests**:
   - Test weapon_type field serialization
   - Test backward compatibility (old items without weapon_type)

### Integration Tests (`tests/test_combat_proficiency.py`)

4. **Combat proficiency integration tests**:
   - Test attacking with equipped weapon grants 1 XP to correct type
   - Test proficiency damage bonus applied to attacks
   - Test no XP gain when attacking with bare hands (no weapon equipped)

5. **Loot generation tests**:
   - Test generated weapons have correct weapon_type assigned
   - Test existing weapon types (Sword, Dagger, Axe, Mace) map correctly

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/cli_rpg/models/weapon_proficiency.py` | CREATE | New model file |
| `src/cli_rpg/models/item.py` | MODIFY | Add weapon_type field |
| `src/cli_rpg/models/character.py` | MODIFY | Add proficiencies tracking |
| `src/cli_rpg/combat.py` | MODIFY | Apply bonus, grant XP |
| `src/cli_rpg/main.py` | MODIFY | Add proficiency command |
| `tests/test_weapon_proficiency.py` | CREATE | Unit tests |
| `tests/test_combat_proficiency.py` | CREATE | Integration tests |
