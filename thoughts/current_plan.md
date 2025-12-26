# Character Classes Implementation Plan

## Spec: Character Class System (MVP)

Add character classes at creation that provide:
- Unique starting stat bonuses
- Class identity stored on Character model
- Foundation for future class-specific abilities (mana/stamina, special commands)

### Classes (5 total)
| Class   | STR Bonus | DEX Bonus | INT Bonus | Theme |
|---------|-----------|-----------|-----------|-------|
| Warrior | +3        | +1        | 0         | Melee damage/tank |
| Mage    | 0         | +1        | +3        | Magic damage |
| Rogue   | +1        | +3        | 0         | Speed/crits |
| Ranger  | +1        | +2        | +1        | Balanced/wilderness |
| Cleric  | +1        | 0         | +2        | Support/healing |

---

## Tests First

### File: `tests/test_character_class.py`

1. **CharacterClass enum exists** with 5 values (WARRIOR, MAGE, ROGUE, RANGER, CLERIC)
2. **CLASS_BONUSES dict** maps each class to stat bonuses
3. **Character model** accepts optional `character_class` field (default: None for backward compat)
4. **Character.from_dict/to_dict** serialize class correctly
5. **get_class_selection()** returns valid class from input (1-5 or name)
6. **create_character() flow** includes class selection step
7. **Stats apply bonuses** - Warrior with STR 10 gets effective STR 13

---

## Implementation Steps

### Step 1: Add CharacterClass enum and bonuses
**File**: `src/cli_rpg/models/character.py`

```python
from enum import Enum

class CharacterClass(Enum):
    WARRIOR = "Warrior"
    MAGE = "Mage"
    ROGUE = "Rogue"
    RANGER = "Ranger"
    CLERIC = "Cleric"

CLASS_BONUSES = {
    CharacterClass.WARRIOR: {"strength": 3, "dexterity": 1, "intelligence": 0},
    CharacterClass.MAGE: {"strength": 0, "dexterity": 1, "intelligence": 3},
    CharacterClass.ROGUE: {"strength": 1, "dexterity": 3, "intelligence": 0},
    CharacterClass.RANGER: {"strength": 1, "dexterity": 2, "intelligence": 1},
    CharacterClass.CLERIC: {"strength": 1, "dexterity": 0, "intelligence": 2},
}
```

### Step 2: Add class field to Character dataclass
**File**: `src/cli_rpg/models/character.py`

- Add `character_class: Optional[CharacterClass] = None` field
- Update `__post_init__` to apply class bonuses to base stats
- Update `to_dict()` to serialize class as string
- Update `from_dict()` to deserialize class (with backward compat for None)
- Update `__str__()` to display class name

### Step 3: Add class selection to character creation
**File**: `src/cli_rpg/character_creation.py`

Add `get_class_selection()` function:
```python
def get_class_selection() -> Optional[CharacterClass]:
    """Prompt user for class selection.

    Returns:
        CharacterClass or None if cancelled
    """
```

Update `create_character()`:
- Add class selection step after name, before stat allocation
- Pass class to Character constructor

### Step 4: Update non-interactive character creation
**File**: `src/cli_rpg/character_creation.py`

Update `create_character_non_interactive()`:
- Read class input (1-5 or class name) after name
- Validate and pass to Character constructor

---

## Verification

Run tests:
```bash
pytest tests/test_character_class.py -v
pytest tests/test_character_creation.py -v
pytest tests/test_character.py -v
```

Manual verification:
```bash
cli-rpg  # Interactive: verify class selection appears
echo -e "TestHero\n1\n2\n10\n10\n10\nyes" | cli-rpg --non-interactive  # Non-interactive
```
