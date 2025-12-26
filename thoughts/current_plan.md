# Charisma Stat & Social Skills Implementation Plan

## Spec

Add a CHA (Charisma) stat that affects shop prices, NPC reactions, and enables social skill commands.

### Features
1. **CHA stat**: New primary stat (1-20) added to Character, included in character creation, class bonuses, level-ups, and serialization
2. **Price modifiers**: Shop buy/sell prices adjusted by CHA (±1% per CHA point from baseline 10)
3. **`persuade <npc>`**: Attempt to get discounts, secrets, or avoid conflicts (CHA-based success roll)
4. **`intimidate <npc>`**: Threaten NPCs for benefits; works on weak-willed, backfires on strong (CHA + reputation)
5. **`bribe <npc> <amount>`**: Spend gold for guaranteed success on social checks (amount + CHA determines outcome)

### Success Formulas
- **Persuade**: 30% base + (CHA × 3%), max 90%
- **Intimidate**: 20% base + (CHA × 2%) + (aggressive reputation × 5%), max 85%. Failure on "strong-willed" NPCs increases hostility.
- **Bribe**: Success if `amount >= 50 - (CHA × 2)` (min 10 gold required)

### NPC Attributes
- Add `willpower: int` (1-10) to NPC model - affects intimidate resistance
- Add `bribeable: bool` to NPC model - some NPCs refuse bribes

---

## Tests First (TDD)

### File: `tests/test_charisma.py`

1. **Character CHA stat tests**:
   - `test_character_has_charisma_stat` - CHA initialized and validated (1-20)
   - `test_character_class_cha_bonuses` - Cleric +2 CHA, Rogue +1 CHA
   - `test_character_level_up_increases_cha` - CHA +1 on level up
   - `test_character_serialization_includes_cha` - to_dict/from_dict preserves CHA

2. **Character creation tests**:
   - `test_character_creation_manual_cha_allocation` - CHA as 4th stat in manual mode
   - `test_character_creation_random_includes_cha` - Random stats include CHA
   - `test_character_status_displays_cha` - Status output shows CHA

3. **Shop price modifier tests**:
   - `test_shop_buy_price_modified_by_cha` - High CHA = lower buy price
   - `test_shop_sell_price_modified_by_cha` - High CHA = higher sell price
   - `test_shop_price_modifier_formula` - Verify ±1% per CHA from 10

4. **Persuade command tests**:
   - `test_persuade_command_exists` - Command recognized
   - `test_persuade_requires_npc_conversation` - Must be talking to NPC
   - `test_persuade_success_grants_discount` - 20% shop discount on success
   - `test_persuade_failure_message` - Graceful failure message
   - `test_persuade_cooldown_per_npc` - Can't spam persuade

5. **Intimidate command tests**:
   - `test_intimidate_command_exists` - Command recognized
   - `test_intimidate_success_on_weak_willed` - Works on low willpower NPCs
   - `test_intimidate_backfires_on_strong_willed` - Fails + penalty on high willpower
   - `test_intimidate_bonus_from_aggressive_reputation` - Kill count boosts success

6. **Bribe command tests**:
   - `test_bribe_command_exists` - Command recognized
   - `test_bribe_requires_amount` - Must specify gold amount
   - `test_bribe_insufficient_gold_fails` - Error if not enough gold
   - `test_bribe_success_deducts_gold` - Gold removed on success
   - `test_bribe_unbribeable_npc_refuses` - Some NPCs can't be bribed

7. **NPC model tests** (in `tests/test_npc.py` additions):
   - `test_npc_has_willpower` - Willpower attribute exists (default 5)
   - `test_npc_has_bribeable` - Bribeable attribute exists (default True)
   - `test_npc_serialization_includes_social_attributes` - to_dict/from_dict preserves willpower/bribeable

---

## Implementation Steps

### 1. Update Character Model (`src/cli_rpg/models/character.py`)

- Add `charisma: int` field after `intelligence`
- Update `__post_init__` validation to include charisma (1-20)
- Update `CLASS_BONUSES` dict:
  - Cleric: +2 CHA
  - Rogue: +1 CHA
  - Others: 0 CHA
- Update `level_up()` to increment charisma +1
- Update `to_dict()` to include charisma
- Update `from_dict()` to restore charisma (default 10 for backward compat)
- Update `__str__()` to display CHA

### 2. Update Character Creation (`src/cli_rpg/character_creation.py`)

- Update `get_manual_stats()` to prompt for charisma as 4th stat
- Update `generate_random_stats()` to include charisma (8-15 range)
- Update `create_character_non_interactive()` to handle 4th stat input

### 3. Update NPC Model (`src/cli_rpg/models/npc.py`)

- Add `willpower: int = 5` field (1-10 scale)
- Add `bribeable: bool = True` field
- Add `persuaded: bool = False` field (tracks if already persuaded this session)
- Update `to_dict()` and `from_dict()` with backward compat

### 4. Add Social Skills Module (`src/cli_rpg/social_skills.py`)

New file with:
- `get_cha_price_modifier(cha: int) -> float` - Returns multiplier (e.g., 0.95 for CHA 15)
- `attempt_persuade(character, npc) -> Tuple[bool, str]` - Roll persuade check
- `attempt_intimidate(character, npc, choices) -> Tuple[bool, str]` - Roll intimidate check
- `attempt_bribe(character, npc, amount) -> Tuple[bool, str]` - Process bribe

### 5. Update Shop Price Logic

**File: `src/cli_rpg/main.py`**
- In `buy` command handler (~line 827): Apply CHA modifier to buy_price
- In `sell` command handler (~line 874): Apply CHA modifier to sell_price
- Apply persuade discount if NPC is persuaded

### 6. Add Social Commands (`src/cli_rpg/main.py`)

Add handlers for:
- `persuade` command: Check in conversation, attempt persuade, set discount flag
- `intimidate` command: Check in conversation, attempt intimidate, handle success/backfire
- `bribe <amount>` command: Validate amount, deduct gold, apply effect

### 7. Update Help Command

Add social commands to help output in `get_command_reference()`.

### 8. Update Completer (`src/cli_rpg/completer.py`)

Add `persuade`, `intimidate`, `bribe` to command completions.

---

## File Changes Summary

| File | Changes |
|------|---------|
| `src/cli_rpg/models/character.py` | Add CHA stat, class bonuses, level-up, serialization |
| `src/cli_rpg/models/npc.py` | Add willpower, bribeable, persuaded fields |
| `src/cli_rpg/character_creation.py` | Add CHA to manual/random stat allocation |
| `src/cli_rpg/social_skills.py` | NEW - Social skill logic and formulas |
| `src/cli_rpg/main.py` | Add persuade/intimidate/bribe commands, CHA price modifiers |
| `src/cli_rpg/completer.py` | Add new commands to completion |
| `tests/test_charisma.py` | NEW - Comprehensive CHA and social skill tests |
| `tests/test_npc.py` | Add NPC social attribute tests |
