# Implementation Plan: Add Hidden Secrets to Default World

## Summary
Add `hidden_secrets` to default world locations in `world.py` so the `search` command actually finds content.

## Secret Format (from secrets.py)
```python
{
    "type": "hidden_door|hidden_treasure|trap|lore_hint",  # SecretType enum values
    "description": "What the player sees when discovered",
    "threshold": 10-20,  # PER check difficulty (passive detection) or PER+5 (active search)
    "discovered": False  # Set to True when found
}
```

## Implementation

### 1. Add secrets to locations in `src/cli_rpg/world.py`

Add `hidden_secrets` parameter to the following locations with thematic secrets:

**Town Square area (easy secrets, threshold 8-12):**
- **Town Well**: Hidden treasure (loose stone with coins), threshold 10
- **Guard Post**: Lore hint (scratched tally marks), threshold 12

**Forest area (medium secrets, threshold 12-15):**
- **Forest Edge**: Trap (snare trap), threshold 12
- **Deep Woods**: Hidden door (overgrown path), threshold 14
- **Ancient Grove**: Lore hint (ancient runes), threshold 15

**Cave (medium secret, threshold 13):**
- **Cave**: Hidden treasure (gemstone in crack), threshold 13

**Millbrook Village (easy-medium, threshold 10-13):**
- **Village Square**: Lore hint (worn inscription on well), threshold 10
- **Blacksmith**: Hidden treasure (coins in ash), threshold 12

**Abandoned Mines (hard secrets, threshold 14-18):**
- **Upper Tunnels**: Trap (unstable ceiling), threshold 14
- **Flooded Level**: Hidden treasure (submerged cache), threshold 16
- **Boss Chamber**: Lore hint (ancient warning), threshold 18

**Ironhold City (varied, threshold 11-16):**
- **Slums**: Hidden door (secret passage), threshold 14
- **Castle Ward**: Lore hint (coded message), threshold 16
- **Temple Quarter**: Hidden treasure (offering box), threshold 11

### 2. Add tests in `tests/test_perception.py`

Add new test class `TestDefaultWorldSecrets`:
- `test_default_world_has_secrets`: Verify at least 5 locations have secrets
- `test_secrets_have_valid_format`: Verify all secrets have required fields
- `test_secrets_have_varied_thresholds`: Verify range of thresholds (10-18)
- `test_secrets_have_varied_types`: Verify multiple secret types used

## Files to Modify
1. `src/cli_rpg/world.py` - Add `hidden_secrets` to Location instantiations
2. `tests/test_perception.py` - Add tests for default world secrets
