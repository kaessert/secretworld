# Implementation Plan: Secret Discovery Rewards

## Summary
Implement tangible rewards when players discover secrets via the `search` command. Currently, finding secrets only marks them as "discovered" but provides no gameplay benefit.

## Scope: MEDIUM
- 5-6 files to modify
- ~15 tests needed
- Estimated 30-40 new/modified lines of code

## Spec

### Secret Types and Their Effects

| Type | Effect When Discovered |
|------|----------------------|
| `hidden_treasure` | Add gold + random loot item to player inventory |
| `hidden_door` | Reveal new exit direction at current location |
| `trap` | Player takes damage OR disarms trap for XP (based on DEX check) |
| `lore_hint` | Display flavor text + small XP reward for discovery |

### Reward Amounts
- `hidden_treasure`: 10-50 gold + 1 random item (Health Potion, Dagger, etc.)
- `hidden_door`: No direct reward, but access to new area
- `trap`: 5-15 damage if triggered, 10 XP if disarmed (DEX >= 12)
- `lore_hint`: 5 XP for discovery

## Implementation Steps

### 1. Update `secrets.py` with reward logic

Add `apply_secret_rewards()` function:
```python
def apply_secret_rewards(
    char: Character,
    location: Location,
    secret: dict
) -> Tuple[bool, str]:
    """Apply rewards/effects for a discovered secret.

    Args:
        char: Player character
        location: Current location
        secret: The secret dict with type, description, etc.

    Returns:
        (success, message) describing what happened
    """
```

Handle each SecretType:
- `hidden_treasure`: Add gold via `char.add_gold()`, create random item via `char.inventory.add_item()`
- `hidden_door`: Add temporary exit via new field `location.temporary_exits`
- `trap`: DEX check, apply damage via `char.take_damage()` or grant XP via `char.gain_xp()`
- `lore_hint`: Grant XP via `char.gain_xp()`

### 2. Update `perform_active_search()` to call reward logic

After marking secrets as discovered, call `apply_secret_rewards()` for each:
```python
for secret in found:
    secret["discovered"] = True
    success, reward_msg = apply_secret_rewards(char, location, secret)
    if reward_msg:
        messages.append(reward_msg)
```

### 3. Update `main.py` search handler

The search command at line 1083-1086 needs to show reward messages:
```python
elif command == "search":
    from cli_rpg.secrets import perform_active_search

    found, message = perform_active_search(game_state.current_character, location)
    print(message)  # Message now includes rewards
```

### 4. Add `temporary_exits` field to Location (optional for hidden_door)

For hidden doors to reveal new exits:
```python
@dataclass
class Location:
    # ... existing fields ...
    temporary_exits: List[str] = field(default_factory=list)
```

Update `get_available_directions()` to include temporary exits.

### 5. Update world.py to include reward data in secrets

Secrets in default world need `reward_gold`, `reward_item`, etc.:
```python
hidden_secrets=[
    {
        "type": "hidden_treasure",
        "description": "A hidden alcove with a small chest",
        "threshold": 12,
        "reward_gold": 25,
        "reward_item": "Health Potion"
    }
]
```

## Tests

### In `tests/test_secret_rewards.py` (NEW FILE)

1. `test_hidden_treasure_grants_gold` - Gold added to character
2. `test_hidden_treasure_grants_item` - Item added to inventory
3. `test_trap_triggers_damage_on_low_dex` - Damage applied when DEX < 12
4. `test_trap_disarmed_on_high_dex` - XP granted when DEX >= 12
5. `test_lore_hint_grants_xp` - Small XP reward
6. `test_hidden_door_reveals_exit` - New exit becomes available
7. `test_reward_only_applied_once` - Re-searching doesn't re-grant rewards
8. `test_search_message_includes_rewards` - Message shows what was gained

### Update `tests/test_perception.py`

Update existing tests to expect reward messages in search output.

## File Changes

| File | Changes |
|------|---------|
| `src/cli_rpg/secrets.py` | Add `apply_secret_rewards()`, update `perform_active_search()` |
| `src/cli_rpg/models/location.py` | Add `temporary_exits` field (optional) |
| `src/cli_rpg/world.py` | Add reward data to default secrets |
| `tests/test_secret_rewards.py` | NEW - 8+ tests for reward system |
| `tests/test_perception.py` | Update search tests for new message format |
