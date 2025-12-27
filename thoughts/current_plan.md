# Rest Command Output UX Improvement

## Spec
When resting with full HP but not full stamina or dread, show "HP: X/X (already full)" instead of silently omitting HP info.

## Changes

### 1. Update test (`tests/test_rest_command.py`)
Add test: `test_rest_at_full_health_but_not_stamina_shows_hp_status`
- Set character to full health but reduced stamina
- Rest and verify message includes "HP" and "already full" or similar

### 2. Modify rest handler (`src/cli_rpg/main.py` ~line 2247-2252)
Change from:
```python
if not at_full_health:
    # heal and append message
```

To:
```python
if at_full_health:
    messages.append(f"HP: {char.health}/{char.max_health} (already full)")
else:
    # existing heal logic
```

Apply same pattern for stamina (show "Stamina: X/X (already full)" when full).
