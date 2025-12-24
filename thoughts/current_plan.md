# Implementation Plan: Next Feature Selection

## Current State
The CLI RPG is feature-complete with all 444 tests passing. Implemented features:
- Character creation with stats (STR/DEX/INT)
- AI-generated worlds via OpenAI
- Turn-based combat system
- Autosave and manual save/load
- Dead-end prevention in world generation

## Feature Options for User Selection

The documented "Future Enhancements" in `docs/AI_FEATURES.md` include:
1. **Inventory/Items System** - Add items, equipment, and inventory management
2. **NPC Encounters** - Generate and interact with non-player characters
3. **Quest Generation** - AI-generated quests with objectives and rewards
4. **Multiple LLM Providers** - Add Anthropic Claude, local models, etc.

---

## Recommended Feature: Inventory/Items System

This is the recommended starting point because:
- Foundation for NPC trading and quest rewards
- Natural extension of combat (equipment affects stats)
- Clear, testable scope
- Follows existing patterns (dataclass models, serialization)

---

## Implementation Plan: Inventory/Items System

### Phase 1: Spec & Data Models

**Step 1.1: Create Item Model**
- File: `src/cli_rpg/models/item.py`
- Spec: Items have name (2-30 chars), description (1-200 chars), type (weapon/armor/consumable/misc), and stat modifiers
- Pattern: Follow `character.py` dataclass pattern with validation in `__post_init__`
- Include: `to_dict()` / `from_dict()` for serialization

**Step 1.2: Create Inventory Model**
- File: `src/cli_rpg/models/inventory.py`
- Spec: Inventory has max capacity (default 20), list of items, equipped weapon/armor slots
- Methods: `add_item()`, `remove_item()`, `equip()`, `unequip()`, `is_full()`
- Pattern: Follow existing model patterns

### Phase 2: Tests (TDD)

**Step 2.1: Item Model Tests**
- File: `tests/test_item.py`
- Tests:
  - Item creation with valid attributes
  - Name validation (2-30 chars)
  - Description validation (1-200 chars)
  - Type validation (weapon/armor/consumable/misc)
  - Serialization round-trip (`to_dict()` → `from_dict()`)
  - Stat modifier application

**Step 2.2: Inventory Model Tests**
- File: `tests/test_inventory.py`
- Tests:
  - Add item to inventory
  - Remove item from inventory
  - Inventory capacity limits
  - Equip weapon/armor
  - Unequip items
  - Equipped item stat bonuses
  - Serialization with equipped items

**Step 2.3: Character Integration Tests**
- File: `tests/test_character_inventory.py`
- Tests:
  - Character has inventory
  - Equipped weapon affects attack damage
  - Equipped armor affects damage reduction
  - Use consumable to heal
  - Inventory persists in save/load

### Phase 3: Implementation

**Step 3.1: Implement Item Model**
- Location: `src/cli_rpg/models/item.py`
- Create `@dataclass` with validation
- Implement serialization methods

**Step 3.2: Implement Inventory Model**
- Location: `src/cli_rpg/models/inventory.py`
- Create inventory management class
- Handle equipment slots

**Step 3.3: Integrate with Character**
- Modify: `src/cli_rpg/models/character.py`
- Add `inventory: Inventory` field
- Update `to_dict()` / `from_dict()` for inventory serialization
- Add methods: `equip_item()`, `use_item()`

**Step 3.4: Update Combat System**
- Modify: `src/cli_rpg/combat.py`
- Apply weapon damage bonus to attacks
- Apply armor defense bonus to damage reduction

**Step 3.5: Add Game Commands**
- Modify: `src/cli_rpg/game_state.py`
- Add commands: `inventory`, `equip <item>`, `unequip <slot>`, `use <item>`
- Modify: `src/cli_rpg/main.py`
- Add command routing for inventory commands

**Step 3.6: Add Item Drops**
- Modify: `src/cli_rpg/combat.py`
- Enemies drop items on defeat (configurable drop table)
- Add loot to inventory after combat victory

**Step 3.7: Update Persistence**
- Modify: `src/cli_rpg/persistence.py`
- Ensure inventory saves with game state
- Backward compatibility for saves without inventory

### Phase 4: Verification

**Step 4.1: Run All Tests**
```bash
pytest tests/test_item.py tests/test_inventory.py tests/test_character_inventory.py -v
pytest  # Full suite to ensure no regressions
```

**Step 4.2: Manual Verification**
- Start new game, find item drop
- Equip weapon, verify attack damage increases
- Equip armor, verify damage reduction
- Use consumable, verify effect
- Save and load, verify inventory persists

---

## File Changes Summary

| File | Action |
|------|--------|
| `src/cli_rpg/models/item.py` | CREATE |
| `src/cli_rpg/models/inventory.py` | CREATE |
| `src/cli_rpg/models/character.py` | MODIFY |
| `src/cli_rpg/combat.py` | MODIFY |
| `src/cli_rpg/game_state.py` | MODIFY |
| `src/cli_rpg/main.py` | MODIFY |
| `src/cli_rpg/persistence.py` | MODIFY |
| `tests/test_item.py` | CREATE |
| `tests/test_inventory.py` | CREATE |
| `tests/test_character_inventory.py` | CREATE |

---

## Alternative Features (If User Chooses Differently)

### NPC Encounters
- Create `npc.py` model with dialogue trees
- AI service generates NPCs contextually
- Add `talk` command to game loop

### Quest Generation
- Create `quest.py` model with objectives/rewards
- AI service generates quests from location context
- Add `quests`, `accept <quest>` commands

### Multiple LLM Providers
- Create `llm_provider.py` abstract interface
- Implement `OpenAIProvider`, `AnthropicProvider`
- Factory pattern in `ai_service.py`
