# Plan: Increase Base Spawn Rates

**Task**: Complete the "Increase Named Location Density and Enterability" issue by raising base spawn probability.

## Change

In `src/cli_rpg/location_noise.py` (line 151), increase `BASE_SPAWN_PROBABILITY`:

```python
# Before
BASE_SPAWN_PROBABILITY = 0.15

# After
BASE_SPAWN_PROBABILITY = 0.20  # ~33% more named locations
```

**Note**: The ISSUES.md mentions `LOCATION_DENSITY_THRESHOLD` and `CITY_DENSITY_THRESHOLD` constants, but these don't exist in the code. The actual spawn rate is controlled by `BASE_SPAWN_PROBABILITY`.

## Verification

```bash
pytest tests/test_location_noise.py -v
```

Existing tests verify relative behavior (density/terrain effects), not absolute rates.

## Update ISSUES.md

Mark "Increase Base Spawn Rates" as complete and close the issue.
