# Playtesting CLI-RPG

## Quick Start

```bash
# Create a commands file
echo -e "look\nmap\ngo north\nquit" > /tmp/playtest.txt

# Run the game with piped input
./venv/bin/cli-rpg --seed 42 --non-interactive --skip-character-creation < /tmp/playtest.txt
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--seed N` | Use a specific seed for deterministic world generation |
| `--non-interactive` | Disable readline features (required for piped input) |
| `--skip-character-creation` | Start immediately with default character |
| `--json` | Output in JSON Lines format (for parsing) |
| `--no-wfc` | Disable WFC terrain generation |

## Map Exploration Commands

| Command | Description |
|---------|-------------|
| `look` | View current location |
| `map` | Display world map (or interior map if inside a landmark) |
| `go <direction>` | Move in a cardinal direction (north, south, east, west) |
| `enter <location>` | Enter a sublocation/landmark |
| `exit` | Exit from interior back to overworld (only works at exit points) |

## Example Playtest Script

Save this to `/tmp/exploration.txt`:

```
look
map
go north
look
map
go south
go east
look
map
enter Market District
look
map
go north
look
map
go south
exit
look
map
quit
```

Then run:
```bash
./venv/bin/cli-rpg --seed 42 --non-interactive --skip-character-creation < /tmp/exploration.txt
```

## What to Check During Playtesting

### World Map Issues
- [ ] Exits shown in `look` match actual navigable directions
- [ ] Exits shown in `map` legend match `look` output
- [ ] █ (blocked) markers correctly show impassable terrain
- [ ] ~ (water) markers correctly prevent movement
- [ ] Location letters in legend match grid positions

### Interior Map Issues
- [ ] Interior maps show correct parent location header
- [ ] [EXIT] markers appear on exit points
- [ ] Exit command works from exit points
- [ ] Exit command fails correctly from non-exit points
- [ ] Interior exits match navigable directions

### Consistency Checks
- [ ] Going north then south returns to same location
- [ ] Map coordinates update correctly when moving
- [ ] Current position marker (@) is accurate
- [ ] Legend entries correspond to actual locations

## Different Seeds to Test

```bash
# Test with different seeds to check WFC terrain variations
for seed in 42 100 200 500 999; do
  echo "=== SEED $seed ==="
  ./venv/bin/cli-rpg --seed $seed --non-interactive --skip-character-creation < /tmp/exploration.txt
done
```

## Testing Interior Locations

Known locations with interiors (seed 42):
- **Town Square**: Market District, Guard Post, Town Well
- **Forest**: Forest Edge, Deep Woods, Ancient Grove
- **Ironhold City**: Ironhold Market, Castle Ward, Slums, Temple Quarter
- **Millbrook Village**: Village Square, Inn, Blacksmith
- **Abandoned Mines**: Mine Entrance, Collapsed Tunnel, Ore Vein (has boss marker ⚔)

## Common Issues to Report

1. **Exit mismatch**: Map shows different exits than `look` command
2. **Blocked terrain mismatch**: Can move to location shown as blocked
3. **[EXIT] confusion**: Exit marker on wrong location
4. **Missing legend entries**: Location visible but not in legend
5. **Coordinate drift**: Position incorrect after navigation
