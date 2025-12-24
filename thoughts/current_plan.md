# Implementation Plan: Combat Commands Integration into Main Game Loop

## 1. SPECIFICATION

### Combat State Detection Requirements
- Game loop must check `game_state.is_in_combat()` on every iteration
- Combat state transitions: exploration → combat (via encounter) → exploration (via victory/flee/death)
- Commands must be routed to appropriate handlers based on combat state

### Combat Command Routing Specification
**When `is_in_combat() == True`:**
- `attack` → call `game_state.current_combat.player_attack()`
- `defend` → call `game_state.current_combat.player_defend()`
- `flee` → call `game_state.current_combat.player_flee()`
- `status` → call `game_state.current_combat.get_status()`
- `look`, `go`, `save`, `quit` → display error: "Can't do that during combat!"

**When `is_in_combat() == False`:**
- `look` → call `game_state.look()`
- `go <direction>` → call `game_state.move(direction)`
- `status` → display character status via `str(game_state.current_character)`
- `save` → save game state
- `quit` → exit game
- `attack`, `defend`, `flee` → display error: "Not in combat."

### Combat Flow Specification
1. **Player Turn**: Execute player command (attack/defend/flee)
2. **Enemy Turn**: If combat still active and player didn't flee, enemy attacks
3. **Victory Check**: If enemy defeated, call `end_combat(victory=True)`
4. **Flee Check**: If flee successful, call `end_combat(victory=False)` with no XP
5. **Death Check**: If player health ≤ 0, end combat and handle game over
6. **Combat End**: Clear `game_state.current_combat` (set to None)

### Display Specification
- Show available commands based on combat state
- Display combat status after each action during combat
- Display clear messages for state transitions

---

## 2. TEST IMPLEMENTATION

### 2.1 Create Test File: `tests/test_main_combat_integration.py`

**Test: Combat command routing during combat**
- Spec: When in combat, attack/defend/flee commands should execute combat actions
- Setup: Create game state, trigger encounter, simulate combat commands
- Assert: Commands call correct CombatEncounter methods and return proper messages

**Test: Exploration command blocking during combat**
- Spec: When in combat, look/go/save commands should show error message
- Setup: Create game state, trigger encounter
- Assert: Commands return error messages and don't execute exploration actions

**Test: Combat command blocking during exploration**
- Spec: When not in combat, attack/defend/flee commands should show error
- Setup: Create game state with no combat
- Assert: Commands return error messages

**Test: Status command in exploration mode**
- Spec: Status command during exploration shows character stats
- Setup: Create game state, no combat
- Assert: Status output contains character name, level, health, stats

**Test: Status command in combat mode**
- Spec: Status command during combat shows combat status
- Setup: Create game state, trigger encounter
- Assert: Status output contains both player and enemy health

**Test: Player attack sequence**
- Spec: Attack command damages enemy, triggers enemy turn if combat continues
- Setup: Create game state with combat
- Assert: Enemy health decreases, enemy attacks back if alive

**Test: Player defend sequence**
- Spec: Defend command sets defensive stance, enemy attack does reduced damage
- Setup: Create game state with combat
- Assert: Defending flag set, next enemy attack does less damage

**Test: Successful flee from combat**
- Spec: Flee command exits combat without XP when successful
- Setup: Create game state with high dexterity character in combat
- Assert: Combat ends, current_combat is None, no XP gained

**Test: Failed flee from combat**
- Spec: Failed flee triggers enemy turn and combat continues
- Setup: Create game state with low dexterity character in combat
- Assert: Combat still active, player takes damage

**Test: Victory ends combat and awards XP**
- Spec: Defeating enemy ends combat, awards XP, may trigger level up
- Setup: Create game state with high-damage character vs weak enemy
- Assert: Enemy defeated, XP gained, combat cleared

**Test: Player death ends combat**
- Spec: When player health reaches 0, combat ends
- Setup: Create game state, reduce player health to critical
- Assert: Combat ends when health ≤ 0

**Test: Combat state persists through turns**
- Spec: Combat encounter object remains active through multiple turns
- Setup: Create game state with combat
- Assert: Same combat instance used across turns until resolution

### 2.2 Create Test File: `tests/test_main_game_loop_state_handling.py`

**Test: Game loop checks combat state each iteration**
- Spec: Main loop must call is_in_combat() to determine command routing
- Setup: Mock game loop iteration
- Assert: is_in_combat() called before command routing

**Test: Transition from exploration to combat**
- Spec: Random encounter triggers combat state
- Setup: Create game state, move to new location triggering encounter
- Assert: is_in_combat() returns True after encounter

**Test: Transition from combat to exploration**
- Spec: Ending combat (victory/flee) returns to exploration state
- Setup: Create game state in combat, resolve combat
- Assert: is_in_combat() returns False after resolution

**Test: Save during exploration allowed**
- Spec: Save command works when not in combat
- Setup: Create game state, execute save
- Assert: Save executes successfully

**Test: Save during combat blocked**
- Spec: Save command blocked when in combat
- Setup: Create game state in combat, attempt save
- Assert: Error message displayed, save not executed

---

## 3. IMPLEMENTATION

### 3.1 Modify `src/cli_rpg/main.py` - `start_game()` function

**Step 1: Add combat command handler function (before main loop)**
```python
def handle_combat_command(game_state: GameState, command: str, args: list[str]) -> str:
    """Handle commands during combat.
    
    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments
        
    Returns:
        Message string to display
    """
    if not game_state.is_in_combat():
        return "\n✗ Not in combat."
    
    combat = game_state.current_combat
    
    if command == "attack":
        victory, message = combat.player_attack()
        output = f"\n{message}"
        
        if victory:
            # Enemy defeated
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            game_state.current_combat = None
        else:
            # Enemy still alive, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"
            
            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                game_state.current_combat = None
        
        return output
    
    elif command == "defend":
        _, message = combat.player_defend()
        output = f"\n{message}"
        
        # Enemy attacks
        enemy_message = combat.enemy_turn()
        output += f"\n{enemy_message}"
        
        # Check if player died
        if not game_state.current_character.is_alive():
            death_message = combat.end_combat(victory=False)
            output += f"\n{death_message}"
            output += "\n\n=== GAME OVER ==="
            game_state.current_combat = None
        
        return output
    
    elif command == "flee":
        success, message = combat.player_flee()
        output = f"\n{message}"
        
        if success:
            # Fled successfully
            game_state.current_combat = None
            combat.is_active = False
        else:
            # Flee failed, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"
            
            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                game_state.current_combat = None
        
        return output
    
    elif command == "status":
        return "\n" + combat.get_status()
    
    else:
        return "\n✗ Can't do that during combat! Use: attack, defend, flee, or status"
```

**Step 2: Add exploration command handler function (before main loop)**
```python
def handle_exploration_command(game_state: GameState, command: str, args: list[str]) -> tuple[bool, str]:
    """Handle commands during exploration.
    
    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments
        
    Returns:
        Tuple of (continue_game, message)
    """
    if command == "look":
        return (True, "\n" + game_state.look())
    
    elif command == "go":
        if not args:
            return (True, "\nGo where? Specify a direction (north, south, east, west, up, down)")
        
        direction = args[0]
        success, message = game_state.move(direction)
        output = f"\n{message}"
        
        if success:
            # Show new location
            output += "\n\n" + game_state.look()
        
        return (True, output)
    
    elif command == "status":
        return (True, "\n" + str(game_state.current_character))
    
    elif command == "save":
        try:
            filepath = save_game_state(game_state)
            return (True, f"\n✓ Game saved successfully!\n  Save location: {filepath}")
        except IOError as e:
            return (True, f"\n✗ Failed to save game: {e}")
    
    elif command == "quit":
        print("\n" + "=" * 50)
        response = input("Save before quitting? (y/n): ").strip().lower()
        if response == 'y':
            try:
                filepath = save_game_state(game_state)
                print(f"\n✓ Game saved successfully!")
                print(f"  Save location: {filepath}")
            except IOError as e:
                print(f"\n✗ Failed to save game: {e}")
        
        print("\nReturning to main menu...")
        return (False, "")
    
    elif command in ["attack", "defend", "flee"]:
        return (True, "\n✗ Not in combat.")
    
    elif command == "unknown":
        return (True, "\n✗ Unknown command. Type 'look', 'go <direction>', 'status', 'save', or 'quit'")
    
    else:
        return (True, "\n✗ Unknown command. Type 'look', 'go <direction>', 'status', 'save', or 'quit'")
```

**Step 3: Replace main game loop in `start_game()`**

Replace the existing game loop (lines ~75-120) with:

```python
    # Main gameplay loop
    while True:
        # Check if player is alive (game over condition)
        if not game_state.current_character.is_alive():
            print("\n" + "=" * 50)
            print("GAME OVER - You have fallen in battle.")
            print("=" * 50)
            response = input("\nReturn to main menu? (y/n): ").strip().lower()
            if response == 'y':
                break
            else:
                # Allow continue even after death (for testing/fun)
                game_state.current_character.health = game_state.current_character.max_health
                print("\n✓ Health restored. Returning to town square...")
                game_state.current_location = "Town Square"
                game_state.current_combat = None
        
        print()
        command_input = input("> ").strip()
        
        if not command_input:
            continue
        
        # Parse command
        command, args = parse_command(command_input)
        
        # Route command based on combat state
        if game_state.is_in_combat():
            message = handle_combat_command(game_state, command, args)
            print(message)
            
            # Show combat status after each action if still in combat
            if game_state.is_in_combat():
                print("\n" + game_state.current_combat.get_status())
        else:
            continue_game, message = handle_exploration_command(game_state, command, args)
            print(message)
            
            if not continue_game:
                break
```

### 3.2 Update Command Display in `start_game()` intro

Replace lines ~60-70 with:

```python
    print("\nExploration Commands:")
    print("  look          - Look around at your surroundings")
    print("  go <direction> - Move in a direction (north, south, east, west)")
    print("  status        - View your character status")
    print("  save          - Save your game (not available during combat)")
    print("  quit          - Return to main menu")
    print("\nCombat Commands:")
    print("  attack        - Attack the enemy")
    print("  defend        - Take a defensive stance")
    print("  flee          - Attempt to flee from combat")
    print("  status        - View combat status")
    print("=" * 50)
```

---

## 4. VERIFICATION

### 4.1 Run Test Suite
```bash
pytest tests/test_main_combat_integration.py -v
pytest tests/test_main_game_loop_state_handling.py -v
pytest tests/test_game_state_combat.py -v
pytest tests/test_combat.py -v
```

### 4.2 Run Full Test Suite
```bash
pytest tests/ -v
```
Verify all 273+ tests pass.

### 4.3 Manual Integration Testing

**Test Case 1: Combat Flow**
1. Start game with new character
2. Move to Forest (type: `go north`)
3. Trigger encounter (may need multiple moves)
4. Use `attack` command
5. Verify enemy health decreases and enemy attacks back
6. Continue until victory
7. Verify XP awarded

**Test Case 2: Defend Mechanic**
1. Start game, trigger encounter
2. Use `defend` command
3. Verify enemy does reduced damage
4. Continue combat

**Test Case 3: Flee Mechanic**
1. Start game, trigger encounter
2. Use `flee` command
3. Verify combat exits (may need multiple tries)
4. Verify no XP awarded on successful flee

**Test Case 4: Command Blocking**
1. Start game, trigger encounter
2. Try `go north` during combat
3. Verify error message
4. Try `save` during combat
5. Verify error message

**Test Case 5: Status Command**
1. Start game, use `status` (exploration)
2. Verify character stats displayed
3. Trigger encounter, use `status` (combat)
4. Verify combat status displayed

**Test Case 6: Game Over**
1. Start game, trigger encounter with strong enemy
2. Let enemy reduce health to 0
3. Verify game over message
4. Verify offered return to menu

---

## 5. FILE CHANGES SUMMARY

### New Files
- `tests/test_main_combat_integration.py` (12 test functions)
- `tests/test_main_game_loop_state_handling.py` (6 test functions)

### Modified Files
- `src/cli_rpg/main.py`:
  - Add `handle_combat_command()` function (~80 lines)
  - Add `handle_exploration_command()` function (~55 lines)
  - Replace main game loop in `start_game()` (~40 lines)
  - Update command display text (~10 lines)
  - Total changes: ~185 lines

### Unchanged Files (used by integration)
- `src/cli_rpg/game_state.py` (already has `is_in_combat()`, `trigger_encounter()`)
- `src/cli_rpg/combat.py` (all methods already implemented)
- `src/cli_rpg/models/character.py` (already complete)
- `src/cli_rpg/models/enemy.py` (already complete)

---

## 6. BACKWARD COMPATIBILITY

### Preserved Functionality
- All exploration commands work identically when not in combat
- Save/load system unchanged
- Character creation unchanged
- World generation unchanged
- AI integration unchanged

### New Functionality
- Combat command routing
- Combat state management
- Game over handling
- Status command works in both modes

### Breaking Changes
- None (pure addition of combat handling to existing exploration system)
