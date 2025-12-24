# Fix: Unknown Command Error Message Missing Commands

## Task
Update the unknown command error message to include missing commands: `talk`, `shop`, `buy`, `sell`.

## Change
**File:** `src/cli_rpg/main.py` (lines 420 and 423)

**Current:**
```python
return (True, "\n✗ Unknown command. Type 'look', 'go', 'status', 'inventory', 'equip', 'unequip', 'use', 'save', or 'quit'")
```

**Updated:**
```python
return (True, "\n✗ Unknown command. Type 'look', 'go', 'talk', 'shop', 'buy', 'sell', 'status', 'inventory', 'equip', 'unequip', 'use', 'save', or 'quit'")
```

## Verification
- Run `pytest tests/test_main.py -v` to ensure no tests break
