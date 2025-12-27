"""Main entry point for CLI RPG."""
import sys
from typing import Optional
from cli_rpg.character_creation import create_character, get_theme_selection, create_character_non_interactive
from cli_rpg.models.character import Character, FightingStance
from cli_rpg.models.item import Item, ItemType
from cli_rpg.persistence import save_character, load_character, list_saves, save_game_state, load_game_state, detect_save_type
from cli_rpg.game_state import GameState, parse_command, suggest_command, KNOWN_COMMANDS
from cli_rpg.world import create_world
from cli_rpg.config import load_ai_config, is_ai_strict_mode
from cli_rpg.ai_service import AIService
from cli_rpg.autosave import autosave
from cli_rpg.map_renderer import render_map, render_worldmap
from cli_rpg.input_handler import init_readline, get_input, set_completer_context
from cli_rpg.dreams import maybe_trigger_dream, display_dream
from cli_rpg.companion_reactions import process_companion_reactions
from cli_rpg.text_effects import set_effects_enabled
from cli_rpg.sound_effects import set_sound_enabled, sound_death, sound_quest_complete


def get_command_reference() -> str:
    """Return the full command reference string.

    Returns:
        Formatted string containing all available commands.
    """
    lines = [
        "Exploration Commands:",
        "  look (l)           - Look around at your surroundings",
        "  go (g) <direction> - Move in a direction (north, south, east, west)",
        "  enter <location>   - Enter a landmark (city, dungeon, etc.)",
        "  exit / leave       - Exit back to the overworld",
        "  status (s, stats)  - View your character status",
        "  inventory (i)      - View your inventory and equipped items",
        "  equip (e) <item>   - Equip a weapon or armor from inventory",
        "  unequip <slot>     - Unequip weapon or armor (slot: weapon/armor)",
        "  use (u) <item>     - Use a consumable item",
        "  drop (dr) <item>   - Drop an item from your inventory",
        "  pick (lp) <chest>  - Pick a lock on a chest (Rogue only, requires Lockpick)",
        "  open (o) <chest>   - Open an unlocked chest",
        "  search (sr)        - Search the area for hidden secrets (PER-based)",
        "  track (tr)         - Track enemies in adjacent areas (Ranger only)",
        "  sneak (sn)         - Move stealthily to avoid encounters (Rogue only, 10 stamina)",
        "  talk (t) <npc>     - Talk to an NPC (then chat freely, 'bye' to leave)",
        "  accept <quest>     - Accept a quest from the current NPC",
        "  complete <quest>   - Turn in a completed quest to the current NPC",
        "  abandon <quest>    - Abandon an active quest from your journal",
        "  shop               - View shop inventory (when at a shop)",
        "  buy <item>         - Buy an item from the shop",
        "  sell <item>        - Sell an item to the shop",
        "  map (m)            - Display a map of explored areas",
        "  worldmap (wm)      - Display the overworld map",
        "  travel <location>  - Fast travel to a discovered named location",
        "  lore               - Discover lore about your current location",
        "  rest (r)           - Rest to recover health (25% of max HP)",
        "  camp (ca)          - Set up camp to rest in wilderness (requires supplies)",
        "  forage (fg)        - Search for herbs and berries in wilderness",
        "  hunt (hu)          - Hunt for game in wilderness",
        "  gather (ga)        - Gather resources in wilderness/caves",
        "  craft (cr) <recipe> - Craft an item from gathered resources",
        "  recipes            - List available crafting recipes",
        "  quests (q)         - View your quest journal",
        "  quest <name>       - View details of a specific quest",
        "  bestiary (b)       - View defeated enemies",
        "  events             - View active world events",
        "  resolve <event>    - Resolve an active world event",
        "  companions         - View your party members and bond levels",
        "  recruit <npc>      - Recruit an NPC to join your party",
        "  dismiss <name>     - Dismiss a companion from your party",
        "  companion-quest <name> - Accept a companion's personal quest",
        "  proficiency (prof) - View your weapon proficiency levels",
        "  reputation (rep)   - View your faction standings",
        "",
        "Social Commands (when talking to an NPC):",
        "  persuade           - Charm NPC for shop discounts (CHA-based)",
        "  intimidate         - Threaten NPC for benefits (CHA + reputation)",
        "  bribe <amount>     - Pay gold for guaranteed social success",
        "  haggle             - Negotiate better prices (CHA-based, at shop)",
        "",
        "  help (h)           - Display this command reference",
        "  dump-state         - Export full game state as JSON",
        "  save               - Save your game (not available during combat)",
        "  quit               - Return to main menu",
        "",
        "Combat Commands:",
        "  attack (a) [target] - Attack an enemy (default: first living enemy)",
        "  defend (d)    - Take a defensive stance (50% damage reduction)",
        "  block (bl)    - Actively block attacks (5 stamina, 75% reduction)",
        "  parry (pa)    - Parry attacks for counter (8 stamina, DEX-based)",
        "  cast (c) [target]  - Cast a magic spell (default: first living enemy)",
        "  fireball (fb) [target] - Cast Fireball (Mage only, 20 mana, burn chance)",
        "  ice_bolt (ib) [target] - Cast Ice Bolt (Mage only, 15 mana, freeze chance)",
        "  heal (hl)     - Cast Heal on self (Mage only, 25 mana)",
        "  bless (bs)    - Bless party with +25% attack (Cleric only, 20 mana)",
        "  smite (sm) [target] - Holy damage, 2x vs undead (Cleric only, 15 mana)",
        "  sneak (sn)    - Enter stealth mode (Rogue only)",
        "  bash (ba) [target] - Stun an enemy (Warrior only, 15 stamina)",
        "  hide (hd)     - Hide to become untargetable for 1 turn (10 stamina)",
        "  stance (st) [type] - Change fighting stance (balanced/aggressive/defensive/berserker)",
        "  flee (f)      - Attempt to flee from combat",
        "  use (u) <item> - Use a consumable item",
        "  status (s, stats) - View combat status",
    ]
    return "\n".join(lines)


def prompt_save_character(character: Character) -> None:
    """Prompt user to save character and handle save operation.
    
    Args:
        character: Character to save
    """
    print("\n" + "=" * 50)
    response = input("Would you like to save this character? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            filepath = save_character(character)
            print("\n✓ Character saved successfully!")
            print(f"  Save location: {filepath}")
        except IOError as e:
            print(f"\n✗ Failed to save character: {e}")
    else:
        print("\nCharacter not saved.")


def select_and_load_character() -> tuple[Optional[Character], Optional[GameState]]:
    """Display save selection menu and load chosen character or game state.

    Returns:
        Tuple of (Character, GameState) where:
        - (character, None) for character-only saves (backward compatibility)
        - (None, game_state) for full game state saves
        - (None, None) if cancelled/failed
    """
    all_saves = list_saves()

    if not all_saves:
        print("\n⚠ No saved characters found.")
        print("  Create a new character first!")
        return (None, None)

    # Separate manual saves and autosaves
    manual_saves = [s for s in all_saves if not s.get('is_autosave')]
    autosaves = [s for s in all_saves if s.get('is_autosave')]

    # Limit display of manual saves
    MANUAL_LIMIT = 15
    displayed_manual = manual_saves[:MANUAL_LIMIT]
    hidden_manual = len(manual_saves) - len(displayed_manual)

    print("\n" + "=" * 50)
    print("LOAD CHARACTER")
    print("=" * 50)

    # Build selection list (for mapping user choice to save)
    selectable: list[dict] = []
    idx = 1

    # Display manual saves
    if displayed_manual:
        print("\nSaved Games:")
        for save in displayed_manual:
            display_time = save.get('display_time', save['timestamp'])
            print(f"  {idx}. {save['name']} ({display_time})")
            selectable.append(save)
            idx += 1
        if hidden_manual > 0:
            print(f"      ... and {hidden_manual} older saves")

    # Display autosave summary + option
    if autosaves:
        latest = autosaves[0]
        display_time = latest.get('display_time', latest['timestamp'])
        # Clean up autosave name for display
        display_name = latest['name']
        if display_name.startswith('autosave_'):
            display_name = display_name[9:]  # Remove 'autosave_' prefix
        print(f"\n  {idx}. [Autosave] {display_name} ({display_time})")
        if len(autosaves) > 1:
            older_count = len(autosaves) - 1
            plural = "s" if older_count > 1 else ""
            print(f"      ({older_count} older autosave{plural} available)")
        selectable.append(latest)
        idx += 1

    print(f"\n  {idx}. Cancel")
    print("=" * 50)

    try:
        choice = input("Select character to load: ").strip()
        choice_num = int(choice)

        if choice_num == idx:
            print("\nLoad cancelled.")
            return (None, None)

        if 1 <= choice_num <= len(selectable):
            selected_save = selectable[choice_num - 1]

            # Detect save type
            try:
                save_type = detect_save_type(selected_save['filepath'])
            except ValueError as e:
                print(f"\n✗ Corrupted save file: {e}")
                return (None, None)

            # Load based on save type
            if save_type == "game_state":
                # Load complete game state
                try:
                    game_state = load_game_state(selected_save['filepath'])
                    print("\n✓ Game state loaded successfully!")
                    print(f"  Location: {game_state.current_location}")
                    print(f"  Character: {game_state.current_character.name}")
                    print("\n" + str(game_state.current_character))
                    return (None, game_state)
                except Exception as e:
                    print(f"\n✗ Failed to load game state: {e}")
                    return (None, None)
            else:
                # Load character only (backward compatibility)
                try:
                    character = load_character(selected_save['filepath'])
                    print("\n✓ Character loaded successfully!")
                    print("\n" + str(character))
                    return (character, None)
                except Exception as e:
                    print(f"\n✗ Failed to load character: {e}")
                    return (None, None)
        else:
            print("\n✗ Invalid selection.")
            return (None, None)

    except ValueError:
        print("\n✗ Invalid input. Please enter a number.")
        return (None, None)
    except FileNotFoundError:
        print("\n✗ Save file not found.")
        return (None, None)
    except Exception as e:
        print(f"\n✗ Failed to load: {e}")
        return (None, None)


def handle_stance_command(game_state: GameState, args: list[str]) -> tuple[bool, str]:
    """Handle the stance command for changing fighting stances.

    The stance command works both in and out of combat.
    With no args: shows current stance and available options.
    With arg: changes stance to specified option (case-insensitive partial match).

    Args:
        game_state: Current game state
        args: Command arguments (stance name or empty)

    Returns:
        Tuple of (continue_game, message)
    """
    from cli_rpg import colors

    player = game_state.current_character

    # Map of stance names/aliases to FightingStance values
    stance_map = {
        "balanced": FightingStance.BALANCED,
        "bal": FightingStance.BALANCED,
        "aggressive": FightingStance.AGGRESSIVE,
        "agg": FightingStance.AGGRESSIVE,
        "defensive": FightingStance.DEFENSIVE,
        "def": FightingStance.DEFENSIVE,
        "berserker": FightingStance.BERSERKER,
        "ber": FightingStance.BERSERKER,
        "berserk": FightingStance.BERSERKER,
    }

    # Stance descriptions for display
    stance_info = {
        FightingStance.BALANCED: ("+5% crit chance", "A balanced approach to combat."),
        FightingStance.AGGRESSIVE: ("+20% damage, -10% defense", "Hit harder but take more damage."),
        FightingStance.DEFENSIVE: ("-10% damage, +20% defense", "Take less damage but deal less."),
        FightingStance.BERSERKER: ("Damage scales with missing HP (up to +50%)", "The lower your health, the harder you hit."),
    }

    if not args:
        # Show current stance and options
        current = player.stance
        modifier, desc = stance_info[current]
        lines = [
            f"Current Stance: {colors.heal(current.value)} ({modifier})",
            f"  {desc}",
            "",
            "Available Stances:",
        ]
        for stance, (mod, description) in stance_info.items():
            marker = "→ " if stance == current else "  "
            lines.append(f"  {marker}{stance.value} ({mod})")

        lines.append("")
        lines.append("Usage: stance <balanced|aggressive|defensive|berserker>")
        return (True, "\n" + "\n".join(lines))

    # Try to match the argument to a stance
    stance_name = args[0].lower()

    if stance_name in stance_map:
        new_stance = stance_map[stance_name]
        if new_stance == player.stance:
            return (True, f"\nYou're already in {colors.heal(new_stance.value)} stance.")

        old_stance = player.stance
        player.stance = new_stance
        modifier, desc = stance_info[new_stance]
        return (True, f"\nYou shift from {old_stance.value} to {colors.heal(new_stance.value)} stance. ({modifier})")

    # No match found - suggest valid options
    valid_stances = ", ".join(s.value.lower() for s in FightingStance)
    return (True, f"\nUnknown stance '{stance_name}'. Valid options: {valid_stances}")


def handle_conversation_input(game_state: GameState, user_input: str) -> tuple[bool, str]:
    """Handle player input during conversation mode.

    Args:
        game_state: Current game state (must have current_npc set)
        user_input: The player's input text

    Returns:
        Tuple of (continue_game, message)
    """
    npc = game_state.current_npc
    if npc is None:
        return (True, "No one to talk to.")

    # Check for exit commands
    exit_commands = {"bye", "leave", "exit"}
    if user_input.lower().strip() in exit_commands:
        npc_name = npc.name
        game_state.current_npc = None
        game_state.current_shop = None
        return (True, f"\nYou say goodbye to {npc_name}.")

    # Generate AI response if available
    if game_state.ai_service:
        try:
            # Determine NPC role
            if npc.is_merchant:
                role = "merchant"
            elif npc.is_quest_giver:
                role = "quest_giver"
            else:
                role = "villager"

            response = game_state.ai_service.generate_conversation_response(
                npc_name=npc.name,
                npc_description=npc.description,
                npc_role=role,
                theme=game_state.theme,
                location_name=game_state.current_location,
                conversation_history=npc.conversation_history,
                player_input=user_input
            )

            # Add both player input and NPC response to history
            npc.add_conversation("player", user_input)
            npc.add_conversation("npc", response)

            return (True, f'\n{npc.name}: "{response}"')

        except Exception:
            # Fallback on any AI error
            pass

    # Fallback without AI service
    return (True, f"\n{npc.name} nods thoughtfully.")


def handle_combat_command(game_state: GameState, command: str, args: list[str], non_interactive: bool = False) -> tuple[bool, str]:
    """Handle commands during combat.

    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments

    Returns:
        Tuple of (continue_game, message)
    """
    if not game_state.is_in_combat():
        return (True, "\n✗ Not in combat.")

    combat = game_state.current_combat
    if combat is None:
        return (True, "\n✗ Not in combat.")

    if command == "attack":
        # Parse target from args (e.g., "attack goblin")
        target = " ".join(args) if args else ""
        victory, message = combat.player_attack(target=target)
        output = f"\n{message}"

        if victory:
            # Check if this was a hallucination-only fight
            all_hallucinations = all(e.is_hallucination for e in combat.enemies)
            if all_hallucinations:
                # Hallucination dispelled - reduce dread, skip XP/bestiary
                from cli_rpg.hallucinations import DREAD_REDUCTION_ON_DISPEL
                from cli_rpg import colors
                game_state.current_character.dread_meter.reduce_dread(DREAD_REDUCTION_ON_DISPEL)
                output += f"\n{colors.heal('Your mind clears slightly as the illusion fades.')}"
                game_state.current_combat = None
                return (True, output)

            # All enemies defeated - record each in bestiary
            for enemy in combat.enemies:
                game_state.current_character.record_enemy_defeat(enemy)
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives (for each enemy)
            for enemy in combat.enemies:
                quest_messages = game_state.current_character.record_kill(enemy.name)
                for msg in quest_messages:
                    output += f"\n{msg}"
                # Record the kill as a choice for reputation tracking
                game_state.record_choice(
                    choice_type="combat_kill",
                    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
                    description=f"Killed {enemy.name}",
                    target=enemy.name,
                )
            # Process companion reactions to combat kill
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
            # Check for invasion resolution
            from cli_rpg.world_events import resolve_invasion_on_victory
            invasion_msg = resolve_invasion_on_victory(game_state)
            if invasion_msg:
                output += f"\n{invasion_msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
        else:
            # Not all enemies dead - check if attack was valid
            if "not found" not in message.lower():
                # Valid attack - enemies attack back
                enemy_message = combat.enemy_turn()
                output += f"\n{enemy_message}"

                # Check if player died
                if not game_state.current_character.is_alive():
                    death_message = combat.end_combat(victory=False)
                    output += f"\n{death_message}"
                    output += "\n\n=== GAME OVER ==="
                    sound_death()
                    game_state.current_combat = None

        return (True, output)

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
            sound_death()
            game_state.current_combat = None

        return (True, output)

    elif command == "block":
        _, message = combat.player_block()
        output = f"\n{message}"

        # If block failed (not enough stamina or stunned), don't trigger enemy turn
        if "Not enough stamina" not in message and "stunned" not in message.lower():
            # Enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "parry":
        _, message = combat.player_parry()
        output = f"\n{message}"

        # If parry failed (not enough stamina or stunned), don't trigger enemy turn
        if "Not enough stamina" not in message and "stunned" not in message.lower():
            # Enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "sneak":
        victory, message = combat.player_sneak()
        output = f"\n{message}"

        # If sneak failed (non-Rogue), don't trigger enemy turn
        if "Only Rogues" not in message:
            # Enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "hide":
        victory, message = combat.player_hide()
        output = f"\n{message}"

        # If hide failed (not enough stamina or stunned), don't trigger enemy turn
        if "Not enough stamina" not in message and "stunned" not in message.lower():
            # Enemy turn
            enemy_turn_message = combat.enemy_turn()
            output += f"\n\n{enemy_turn_message}"

            # Check if player died
            if not player.is_alive():
                output += f"\n\n{combat.end_combat(victory=False)}"
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "bash":
        # Parse target from args (e.g., "bash orc")
        target = " ".join(args) if args else ""
        victory, message = combat.player_bash(target=target)
        output = f"\n{message}"

        if victory:
            # Check if this was a hallucination-only fight
            all_hallucinations = all(e.is_hallucination for e in combat.enemies)
            if all_hallucinations:
                # Hallucination dispelled - reduce dread, skip XP/bestiary
                from cli_rpg.hallucinations import DREAD_REDUCTION_ON_DISPEL
                from cli_rpg import colors
                game_state.current_character.dread_meter.reduce_dread(DREAD_REDUCTION_ON_DISPEL)
                output += f"\n{colors.heal('Your mind clears slightly as the illusion fades.')}"
                game_state.current_combat = None
                return (True, output)

            # All enemies defeated - record each in bestiary
            for enemy in combat.enemies:
                game_state.current_character.record_enemy_defeat(enemy)
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives (for each enemy)
            for enemy in combat.enemies:
                quest_messages = game_state.current_character.record_kill(enemy.name)
                for msg in quest_messages:
                    output += f"\n{msg}"
                # Record the kill as a choice for reputation tracking
                game_state.record_choice(
                    choice_type="combat_kill",
                    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
                    description=f"Killed {enemy.name} with bash",
                    target=enemy.name,
                )
            # Process companion reactions to combat kill
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
            # Check for invasion resolution
            from cli_rpg.world_events import resolve_invasion_on_victory
            invasion_msg = resolve_invasion_on_victory(game_state)
            if invasion_msg:
                output += f"\n{invasion_msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
        else:
            # Bash didn't result in victory - check if it was successful
            if "Only Warriors" not in message and "Not enough stamina" not in message and "stunned" not in message.lower():
                # Valid bash - enemies attack back
                enemy_message = combat.enemy_turn()
                output += f"\n{enemy_message}"

                # Check if player died
                if not game_state.current_character.is_alive():
                    death_message = combat.end_combat(victory=False)
                    output += f"\n{death_message}"
                    output += "\n\n=== GAME OVER ==="
                    sound_death()
                    game_state.current_combat = None

        return (True, output)

    elif command == "flee":
        success, message = combat.player_flee()
        output = f"\n{message}"

        if success:
            # Fled successfully - record choice for each enemy fled from
            for enemy in combat.enemies:
                game_state.record_choice(
                    choice_type="combat_flee",
                    choice_id=f"flee_{enemy.name}",
                    description=f"Fled from {enemy.name}",
                    target=enemy.name
                )
            # Process companion reactions to fleeing
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_flee")
            for msg in reaction_msgs:
                output += f"\n{msg}"
            game_state.current_combat = None
            combat.is_active = False
            # Autosave after successful flee
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
        else:
            # Flee failed, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "cast":
        # Parse target from args (e.g., "cast goblin")
        target = " ".join(args) if args else ""
        victory, message = combat.player_cast(target=target)
        output = f"\n{message}"

        if victory:
            # Check if this was a hallucination-only fight
            all_hallucinations = all(e.is_hallucination for e in combat.enemies)
            if all_hallucinations:
                # Hallucination dispelled - reduce dread, skip XP/bestiary
                from cli_rpg.hallucinations import DREAD_REDUCTION_ON_DISPEL
                from cli_rpg import colors
                game_state.current_character.dread_meter.reduce_dread(DREAD_REDUCTION_ON_DISPEL)
                output += f"\n{colors.heal('Your mind clears slightly as the illusion fades.')}"
                game_state.current_combat = None
                return (True, output)

            # All enemies defeated - record each in bestiary
            for enemy in combat.enemies:
                game_state.current_character.record_enemy_defeat(enemy)
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives (for each enemy)
            for enemy in combat.enemies:
                quest_messages = game_state.current_character.record_kill(enemy.name)
                for msg in quest_messages:
                    output += f"\n{msg}"
                # Record the kill as a choice for reputation tracking
                game_state.record_choice(
                    choice_type="combat_kill",
                    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
                    description=f"Killed {enemy.name}",
                    target=enemy.name,
                )
            # Process companion reactions to combat kill
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
            # Check for invasion resolution
            from cli_rpg.world_events import resolve_invasion_on_victory
            invasion_msg = resolve_invasion_on_victory(game_state)
            if invasion_msg:
                output += f"\n{invasion_msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
        else:
            # Not all enemies dead - check if cast was valid
            if "not found" not in message.lower():
                # Valid cast - enemies attack back
                enemy_message = combat.enemy_turn()
                output += f"\n{enemy_message}"

                # Check if player died
                if not game_state.current_character.is_alive():
                    death_message = combat.end_combat(victory=False)
                    output += f"\n{death_message}"
                    output += "\n\n=== GAME OVER ==="
                    sound_death()
                    game_state.current_combat = None

        return (True, output)

    elif command == "fireball":
        # Parse target from args (e.g., "fireball goblin")
        target = " ".join(args) if args else ""
        victory, message = combat.player_fireball(target=target)
        output = f"\n{message}"

        if victory:
            # Check if this was a hallucination-only fight
            all_hallucinations = all(e.is_hallucination for e in combat.enemies)
            if all_hallucinations:
                # Hallucination dispelled - reduce dread, skip XP/bestiary
                from cli_rpg.hallucinations import DREAD_REDUCTION_ON_DISPEL
                from cli_rpg import colors
                game_state.current_character.dread_meter.reduce_dread(DREAD_REDUCTION_ON_DISPEL)
                output += f"\n{colors.heal('Your mind clears slightly as the illusion fades.')}"
                game_state.current_combat = None
                return (True, output)

            # All enemies defeated - record each in bestiary
            for enemy in combat.enemies:
                game_state.current_character.record_enemy_defeat(enemy)
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives (for each enemy)
            for enemy in combat.enemies:
                quest_messages = game_state.current_character.record_kill(enemy.name)
                for msg in quest_messages:
                    output += f"\n{msg}"
                # Record the kill as a choice for reputation tracking
                game_state.record_choice(
                    choice_type="combat_kill",
                    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
                    description=f"Killed {enemy.name} with Fireball",
                    target=enemy.name,
                )
            # Process companion reactions to combat kill
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
            # Check for invasion resolution
            from cli_rpg.world_events import resolve_invasion_on_victory
            invasion_msg = resolve_invasion_on_victory(game_state)
            if invasion_msg:
                output += f"\n{invasion_msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
        else:
            # Not all enemies dead - check if fireball was valid
            if "not found" not in message.lower() and "Only Mages" not in message and "mana" not in message.lower() and "stunned" not in message.lower():
                # Valid fireball - enemies attack back
                enemy_message = combat.enemy_turn()
                output += f"\n{enemy_message}"

                # Check if player died
                if not game_state.current_character.is_alive():
                    death_message = combat.end_combat(victory=False)
                    output += f"\n{death_message}"
                    output += "\n\n=== GAME OVER ==="
                    sound_death()
                    game_state.current_combat = None

        return (True, output)

    elif command == "ice_bolt":
        # Parse target from args (e.g., "ice_bolt goblin")
        target = " ".join(args) if args else ""
        victory, message = combat.player_ice_bolt(target=target)
        output = f"\n{message}"

        if victory:
            # Check if this was a hallucination-only fight
            all_hallucinations = all(e.is_hallucination for e in combat.enemies)
            if all_hallucinations:
                # Hallucination dispelled - reduce dread, skip XP/bestiary
                from cli_rpg.hallucinations import DREAD_REDUCTION_ON_DISPEL
                from cli_rpg import colors
                game_state.current_character.dread_meter.reduce_dread(DREAD_REDUCTION_ON_DISPEL)
                output += f"\n{colors.heal('Your mind clears slightly as the illusion fades.')}"
                game_state.current_combat = None
                return (True, output)

            # All enemies defeated - record each in bestiary
            for enemy in combat.enemies:
                game_state.current_character.record_enemy_defeat(enemy)
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives (for each enemy)
            for enemy in combat.enemies:
                quest_messages = game_state.current_character.record_kill(enemy.name)
                for msg in quest_messages:
                    output += f"\n{msg}"
                # Record the kill as a choice for reputation tracking
                game_state.record_choice(
                    choice_type="combat_kill",
                    choice_id=f"kill_{enemy.name}_{game_state.game_time.hour}",
                    description=f"Killed {enemy.name} with Ice Bolt",
                    target=enemy.name,
                )
            # Process companion reactions to combat kill
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
            # Check for invasion resolution
            from cli_rpg.world_events import resolve_invasion_on_victory
            invasion_msg = resolve_invasion_on_victory(game_state)
            if invasion_msg:
                output += f"\n{invasion_msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
        else:
            # Not all enemies dead - check if ice bolt was valid
            if "not found" not in message.lower() and "Only Mages" not in message and "mana" not in message.lower() and "stunned" not in message.lower():
                # Valid ice bolt - enemies attack back
                enemy_message = combat.enemy_turn()
                output += f"\n{enemy_message}"

                # Check if player died
                if not game_state.current_character.is_alive():
                    death_message = combat.end_combat(victory=False)
                    output += f"\n{death_message}"
                    output += "\n\n=== GAME OVER ==="
                    sound_death()
                    game_state.current_combat = None

        return (True, output)

    elif command == "heal":
        # Heal has no target, it's always self
        victory, message = combat.player_heal()
        output = f"\n{message}"

        # Heal is never a victory (only offensive spells can defeat enemies)
        # Check if heal was valid (success or at least valid attempt)
        if "Only Mages" not in message and "mana" not in message.lower() and "stunned" not in message.lower() and "full health" not in message.lower():
            # Valid heal - enemies attack back
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "bless":
        # Bless has no target, it buffs player and companions
        victory, message = combat.player_bless()
        output = f"\n{message}"

        # Bless is never a victory (buff ability)
        # Check if bless was valid
        if "Only Clerics" not in message and "mana" not in message.lower() and "stunned" not in message.lower():
            # Valid bless - enemies attack back
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "smite":
        # Parse target from args (e.g., "smite skeleton")
        target = " ".join(args) if args else ""
        victory, message = combat.player_smite(target=target)
        output = f"\n{message}"

        if victory:
            # Check if this was a hallucination-only fight
            all_hallucinations = all(e.is_hallucination for e in combat.enemies)
            if all_hallucinations:
                # Hallucination dispelled - reduce dread, skip XP/bestiary
                from cli_rpg.hallucinations import DREAD_REDUCTION_ON_DISPEL
                from cli_rpg import colors
                game_state.current_character.dread_meter.reduce_dread(DREAD_REDUCTION_ON_DISPEL)
                output += f"\n{colors.heal('Your mind clears slightly as the illusion fades.')}"
                game_state.current_combat = None
                return (True, output)

            # All enemies defeated - record each in bestiary
            for enemy in combat.enemies:
                game_state.current_character.record_enemy_defeat(enemy)

            # Quest progress: record kills for all enemies
            for enemy in combat.enemies:
                quest_messages = game_state.current_character.record_kill(enemy.name)
                for msg in quest_messages:
                    output += f"\n{msg}"

            # Check if this was a boss fight
            if any(e.is_boss for e in combat.enemies):
                game_state.mark_boss_defeated()

            # Combat ends with victory - award XP and loot
            victory_message = combat.end_combat(victory=True)
            output += f"\n{victory_message}"
            game_state.current_combat = None

            # Trigger companion reaction after combat
            reaction_msgs = process_companion_reactions(game_state.companions, "combat_kill")
            for msg in reaction_msgs:
                output += f"\n{msg}"
        else:
            # Check if smite was valid (not class/mana/stun error)
            if "Only Clerics" not in message and "mana" not in message.lower() and "stunned" not in message.lower() and "not found" not in message.lower():
                # Valid smite - enemies attack back
                enemy_message = combat.enemy_turn()
                output += f"\n{enemy_message}"

                # Check if player died
                if not game_state.current_character.is_alive():
                    death_message = combat.end_combat(victory=False)
                    output += f"\n{death_message}"
                    output += "\n\n=== GAME OVER ==="
                    sound_death()
                    game_state.current_combat = None

        return (True, output)

    elif command == "stance":
        # Handle stance command - works in and out of combat
        return handle_stance_command(game_state, args)

    elif command == "status":
        return (True, "\n" + combat.get_status())

    elif command == "use":
        if not args:
            return (True, "\nUse what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
            # Check if item is equipped
            inv = game_state.current_character.inventory
            item_name_lower = item_name.lower()
            if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
                return (True, f"\n{inv.equipped_weapon.name} is currently equipped as your weapon and cannot be used.")
            if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
                return (True, f"\n{inv.equipped_armor.name} is currently equipped as your armor and cannot be used.")
            return (True, f"\nYou don't have '{item_name}' in your inventory.")
        success, message = game_state.current_character.use_item(item)
        output = f"\n{message}"

        if success:
            # Using item counts as a turn, enemy attacks
            enemy_message = combat.enemy_turn()
            output += f"\n{enemy_message}"

            # Check if player died
            if not game_state.current_character.is_alive():
                death_message = combat.end_combat(victory=False)
                output += f"\n{death_message}"
                output += "\n\n=== GAME OVER ==="
                sound_death()
                game_state.current_combat = None

        return (True, output)

    elif command == "help":
        return (True, "\n" + get_command_reference())

    elif command == "quit":
        if non_interactive:
            # In non-interactive mode, skip confirmation and exit directly
            return (False, "\nExiting game...")
        print("\n" + "=" * 50)
        print("⚠️  Warning: You are in combat! Saving is disabled during combat.")
        print("If you quit now, your combat progress will be lost.")
        sys.stdout.flush()  # Ensure prompt is visible before blocking
        response = input("Quit without saving? (y/n): ").strip().lower()
        if response == 'y':
            print("\nReturning to main menu...")
            return (False, "")
        print("\nContinuing combat...")
        return (True, "")  # Cancel quit, continue combat

    elif command == "unknown":
        # Provide "did you mean?" suggestion during combat
        combat_commands = {"attack", "defend", "block", "parry", "cast", "fireball", "ice_bolt", "heal", "bless", "smite", "flee", "sneak", "bash", "hide", "stance", "use", "status", "help", "quit"}
        if args and args[0]:
            suggestion = suggest_command(args[0], combat_commands)
            if suggestion:
                return (True, f"\n✗ Unknown command '{args[0]}'. Did you mean '{suggestion}'?")
        return (True, "\n✗ Can't do that during combat! Use: attack, defend, block, parry, cast, flee, sneak, hide, use, status, help, or quit")

    else:
        return (True, "\n✗ Can't do that during combat! Use: attack, defend, block, parry, cast, flee, sneak, hide, use, status, help, or quit")


def handle_exploration_command(game_state: GameState, command: str, args: list[str], non_interactive: bool = False) -> tuple[bool, str]:
    """Handle commands during exploration.
    
    Args:
        game_state: Current game state
        command: Parsed command
        args: Command arguments
        
    Returns:
        Tuple of (continue_game, message)
    """
    # Decrement haggle cooldown on current NPC (if any)
    npc = game_state.current_npc
    if npc is not None and isinstance(getattr(npc, 'haggle_cooldown', None), int):
        if npc.haggle_cooldown > 0:
            npc.haggle_cooldown -= 1

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

    elif command == "enter":
        target_name = " ".join(args) if args else None
        success, message = game_state.enter(target_name)
        return (True, f"\n{message}")

    elif command in ("exit", "leave"):
        success, message = game_state.exit_location()
        return (True, f"\n{message}")

    elif command == "search":
        from cli_rpg.secrets import perform_active_search
        location = game_state.get_current_location()
        found, message = perform_active_search(game_state.current_character, location)
        return (True, f"\n{message}")

    elif command == "track":
        from cli_rpg.ranger import execute_track
        success, message = execute_track(game_state)
        return (True, f"\n{message}")

    elif command == "sneak":
        # Exploration sneak for Rogues (separate from combat sneak)
        from cli_rpg.models.character import CharacterClass
        from cli_rpg.game_state import calculate_sneak_success_chance

        # Rogue-only check
        if game_state.current_character.character_class != CharacterClass.ROGUE:
            return (True, "\nOnly Rogues can sneak past encounters!")

        # Stamina check (10 stamina cost)
        if not game_state.current_character.use_stamina(10):
            stamina = game_state.current_character.stamina
            max_stamina = game_state.current_character.max_stamina
            return (True, f"\nNot enough stamina to sneak! ({stamina}/{max_stamina})")

        # Enable sneaking mode
        game_state.is_sneaking = True
        success_chance = calculate_sneak_success_chance(game_state.current_character)
        return (True, f"\nYou move carefully into the shadows... ({success_chance}% chance to avoid encounters on next move)")

    elif command == "stance":
        # Handle stance command - works in and out of combat
        return handle_stance_command(game_state, args)

    elif command == "status":
        status_output = str(game_state.current_character)
        time_display = game_state.game_time.get_display()
        weather_display = game_state.weather.get_display()
        dread_display = game_state.current_character.dread_meter.get_display()
        return (True, f"\n{status_output}\nTime: {time_display}\nWeather: {weather_display}\n{dread_display}")

    elif command == "inventory":
        return (True, "\n" + str(game_state.current_character.inventory))

    elif command == "equip":
        if not args:
            return (True, "\nEquip what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
            # Check if item is already equipped (following pattern from 'use' command fix)
            inv = game_state.current_character.inventory
            item_name_lower = item_name.lower()
            if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
                return (True, f"\n{inv.equipped_weapon.name} is already equipped.")
            if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
                return (True, f"\n{inv.equipped_armor.name} is already equipped.")
            return (True, f"\nYou don't have '{item_name}' in your inventory.")
        success = game_state.current_character.inventory.equip(item)
        if success:
            return (True, f"\nYou equipped {item.name}.")
        else:
            if item.item_type == ItemType.CONSUMABLE:
                return (True, f"\nYou can only equip weapons or armor. Use 'use {item.name}' for consumables.")
            else:
                return (True, "\nYou can only equip weapons or armor.")

    elif command == "unequip":
        if not args:
            return (True, "\nUnequip what? Specify 'weapon' or 'armor'.")
        slot = args[0].lower()
        if slot not in ("weapon", "armor"):
            return (True, "\nYou can only unequip 'weapon' or 'armor'.")
        inv = game_state.current_character.inventory
        if slot == "weapon" and inv.equipped_weapon is None:
            return (True, "\nYou don't have a weapon equipped.")
        if slot == "armor" and inv.equipped_armor is None:
            return (True, "\nYou don't have armor equipped.")
        success = inv.unequip(slot)
        if success:
            return (True, f"\nYou unequipped your {slot}.")
        else:
            return (True, "\nCan't unequip - inventory is full.")

    elif command == "use":
        if not args:
            return (True, "\nUse what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
            # Check if item is equipped
            inv = game_state.current_character.inventory
            item_name_lower = item_name.lower()
            if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
                return (True, f"\n{inv.equipped_weapon.name} is currently equipped as your weapon and cannot be used.")
            if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
                return (True, f"\n{inv.equipped_armor.name} is currently equipped as your armor and cannot be used.")
            return (True, f"\nYou don't have '{item_name}' in your inventory.")
        success, message = game_state.current_character.use_item(item)
        return (True, f"\n{message}")

    elif command == "talk":
        location = game_state.get_current_location()
        if location is None or not location.npcs:
            return (True, "\nThere are no NPCs here to talk to.")

        if not args:
            # Get available NPCs (respecting night availability)
            if game_state.game_time.is_night():
                available_npcs = [n for n in location.npcs if n.available_at_night]
            else:
                available_npcs = location.npcs

            if not available_npcs:
                return (True, "\nAll NPCs have gone home for the night.")

            if len(available_npcs) == 1:
                # Auto-select the single available NPC
                npc = available_npcs[0]
            else:
                # Multiple NPCs - list them
                npc_names = [n.name for n in available_npcs]
                return (True, f"\nTalk to whom? Available: {', '.join(npc_names)}")
        else:
            npc_name = " ".join(args)
            npc = location.find_npc_by_name(npc_name)
            if npc is None:
                return (True, f"\nYou don't see '{npc_name}' here.")

        # Check night availability
        if game_state.game_time.is_night() and not npc.available_at_night:
            return (True, f"\n{npc.name} has gone home for the night.")

        # Store current NPC for accept command context
        game_state.current_npc = npc

        # Generate or get NPC ASCII art
        if not npc.ascii_art:
            # Determine NPC role for art generation
            role = "merchant" if npc.is_merchant else ("quest_giver" if npc.is_quest_giver else "villager")

            if game_state.ai_service:
                try:
                    npc.ascii_art = game_state.ai_service.generate_npc_ascii_art(
                        npc_name=npc.name,
                        npc_description=npc.description,
                        npc_role=role,
                        theme=game_state.theme
                    )
                except Exception:
                    # Fall back to template-based art
                    from cli_rpg.npc_art import get_fallback_npc_ascii_art
                    npc.ascii_art = get_fallback_npc_ascii_art(role, npc.name)
            else:
                # No AI available, use fallback
                from cli_rpg.npc_art import get_fallback_npc_ascii_art
                npc.ascii_art = get_fallback_npc_ascii_art(role, npc.name)

        # Generate AI dialogue if available and NPC needs more greetings
        if game_state.ai_service and len(npc.greetings) < 3:
            try:
                role = "merchant" if npc.is_merchant else ("quest_giver" if npc.is_quest_giver else "villager")
                dialogue = game_state.ai_service.generate_npc_dialogue(
                    npc_name=npc.name,
                    npc_description=npc.description,
                    npc_role=role,
                    theme=game_state.theme,
                    location_name=game_state.current_location
                )
                npc.greetings.append(dialogue)
            except Exception:
                pass  # Silent fallback to existing greetings

        # Build output with ASCII art first
        from cli_rpg import colors
        output = ""
        if npc.ascii_art:
            output = f"\n{npc.ascii_art}\n"
        greeting = npc.get_greeting(choices=game_state.choices)
        dialogue_text = f'"{greeting}"'
        output += f"\n{colors.npc(npc.name)}: {colors.dialogue(dialogue_text)}"

        # Record talk for TALK quest progress tracking
        talk_messages = game_state.current_character.record_talk(npc.name)
        if talk_messages:
            output += "\n\n" + "\n".join(talk_messages)

        # Talking to NPCs reduces dread by 5
        if game_state.current_character.dread_meter.dread > 0:
            game_state.current_character.dread_meter.reduce_dread(5)

        if npc.is_merchant and npc.shop:
            game_state.current_shop = npc.shop
            output += "\n\nType 'shop' to see items, 'buy <item>' to purchase, 'sell <item>' to sell."
        else:
            game_state.current_shop = None  # Clear shop context for non-merchants

        # Check for quests ready to turn in to this NPC
        from cli_rpg.models.quest import QuestStatus
        ready_to_turn_in = [
            q for q in game_state.current_character.quests
            if q.status == QuestStatus.READY_TO_TURN_IN and q.quest_giver == npc.name
        ]
        if ready_to_turn_in:
            output += "\n\nQuests ready to turn in:"
            for q in ready_to_turn_in:
                output += f"\n  ★ {q.name}"
            output += "\n\nType 'complete <quest>' to turn in a quest and claim rewards."

        # Generate AI quest if NPC is quest-giver with no available quests
        if npc.is_quest_giver and game_state.ai_service:
            available_quests = [
                q for q in npc.offered_quests
                if not game_state.current_character.has_quest(q.name)
            ]
            if not available_quests:
                try:
                    from cli_rpg.models.quest import Quest, ObjectiveType
                    # Build set of valid location names for EXPLORE quest validation
                    valid_locations = {loc.lower() for loc in game_state.world.keys()}
                    # Build set of valid NPC names for TALK quest validation
                    valid_npcs = {
                        npc_in_loc.name.lower()
                        for location in game_state.world.values()
                        for npc_in_loc in location.npcs
                    }
                    # Get world and region context for cohesive quest generation
                    world_ctx = game_state.get_or_create_world_context()
                    current_loc = game_state.world.get(game_state.current_location)
                    region_ctx = None
                    if current_loc and current_loc.coordinates:
                        region_ctx = game_state.get_or_create_region_context(
                            current_loc.coordinates
                        )

                    quest_data = game_state.ai_service.generate_quest(
                        theme=game_state.theme,
                        npc_name=npc.name,
                        player_level=game_state.current_character.level,
                        location_name=game_state.current_location,
                        valid_locations=valid_locations,
                        valid_npcs=valid_npcs,
                        world_context=world_ctx,
                        region_context=region_ctx
                    )
                    new_quest = Quest(
                        name=quest_data["name"],
                        description=quest_data["description"],
                        objective_type=ObjectiveType(quest_data["objective_type"]),
                        target=quest_data["target"],
                        target_count=quest_data["target_count"],
                        gold_reward=quest_data["gold_reward"],
                        xp_reward=quest_data["xp_reward"],
                        quest_giver=quest_data["quest_giver"]
                    )
                    npc.offered_quests.append(new_quest)
                except Exception:
                    pass  # Silent fallback - NPC just has no new quests

        # Show available quests if NPC is a quest giver
        if npc.is_quest_giver and npc.offered_quests:
            available = [
                q for q in npc.offered_quests
                if not game_state.current_character.has_quest(q.name)
            ]
            if available:
                output += "\n\nAvailable Quests:"
                for q in available:
                    output += f"\n  - {q.name} [{q.difficulty.value.capitalize()}]"
                output += "\n\nType 'accept <quest>' to accept a quest."

        # Add conversation prompt
        output += "\n\n(Continue chatting or type 'bye' to leave)"

        return (True, output)

    elif command == "shop":
        if game_state.current_shop is None:
            # Auto-detect merchant in current location
            location = game_state.get_current_location()
            merchant = next((npc for npc in location.npcs if npc.is_merchant and npc.shop), None)
            if merchant is None:
                # Check for active caravan event at this location
                from cli_rpg.world_events import get_caravan_shop
                caravan_shop = get_caravan_shop(game_state)
                if caravan_shop is not None:
                    game_state.current_shop = caravan_shop
                else:
                    return (True, "\nThere's no merchant here.")
            else:
                # Check if merchant is available at night
                if game_state.game_time.is_night() and not merchant.available_at_night:
                    return (True, "\nThe shop is closed for the night.")
                game_state.current_shop = merchant.shop
        # Check faction reputation and show status message
        from cli_rpg.faction_shop import (
            get_faction_price_modifiers,
            get_merchant_guild_faction,
            get_faction_price_message,
        )
        faction_buy_mod, faction_sell_mod, trade_refused = get_faction_price_modifiers(
            game_state.factions
        )
        if trade_refused:
            return (True, "\nThe merchants eye you with hostility and refuse to serve you.")
        shop = game_state.current_shop
        lines = [f"\n=== {shop.name} ===", f"Your gold: {game_state.current_character.gold}", ""]
        # Add reputation status message if not neutral
        merchant_guild = get_merchant_guild_faction(game_state.factions)
        if merchant_guild is not None:
            rep_message = get_faction_price_message(merchant_guild.get_reputation_level())
            if rep_message:
                lines.append(rep_message)
                lines.append("")
        # Calculate price modifiers for display (same as buy command)
        from cli_rpg.social_skills import get_cha_price_modifier
        cha_modifier = get_cha_price_modifier(game_state.current_character.charisma)
        for si in shop.inventory:
            # Calculate display price with all modifiers (matches buy logic)
            display_price = int(si.buy_price * cha_modifier)
            if faction_buy_mod is not None:
                display_price = int(display_price * faction_buy_mod)
            if game_state.current_npc and game_state.current_npc.persuaded:
                display_price = int(display_price * 0.8)
            if game_state.haggle_bonus > 0:
                display_price = int(display_price * (1 - game_state.haggle_bonus))
            lines.append(f"  {si.item.name} - {display_price} gold")
        return (True, "\n".join(lines))

    elif command == "buy":
        if game_state.current_shop is None:
            return (True, "\nYou're not at a shop. Talk to a merchant first.")
        # Check faction reputation before allowing purchase
        from cli_rpg.faction_shop import get_faction_price_modifiers
        faction_buy_mod, faction_sell_mod, trade_refused = get_faction_price_modifiers(
            game_state.factions
        )
        if trade_refused:
            return (True, "\nThe merchants refuse to trade with you due to your poor reputation.")
        if not args:
            return (True, "\nBuy what? Specify an item name.")
        item_name = " ".join(args)
        shop_item = game_state.current_shop.find_item_by_name(item_name)
        if shop_item is None:
            # Try partial match
            matches = game_state.current_shop.find_items_by_partial_name(item_name)
            if len(matches) == 1:
                shop_item = matches[0]  # Unique partial match - use it
            elif len(matches) > 1:
                names = ", ".join(f"'{m.item.name}'" for m in matches)
                return (True, f"\nMultiple items match '{item_name}': {names}. Please be more specific.")
            else:
                # No matches - list available items
                available_items = ", ".join(f"'{si.item.name}'" for si in game_state.current_shop.inventory)
                return (True, f"\nThe shop doesn't have '{item_name}'. Available: {available_items}")
        # Calculate final price with CHA modifier and persuade discount
        from cli_rpg.social_skills import get_cha_price_modifier
        cha_modifier = get_cha_price_modifier(game_state.current_character.charisma)
        final_price = int(shop_item.buy_price * cha_modifier)
        # Apply faction reputation modifier
        if faction_buy_mod is not None:
            final_price = int(final_price * faction_buy_mod)
        # Apply 20% persuade discount if NPC was persuaded
        if game_state.current_npc and game_state.current_npc.persuaded:
            final_price = int(final_price * 0.8)
        # Apply haggle bonus if active
        if game_state.haggle_bonus > 0:
            final_price = int(final_price * (1 - game_state.haggle_bonus))
        if game_state.current_character.gold < final_price:
            return (True, f"\nYou can't afford {shop_item.item.name} ({final_price} gold). You have {game_state.current_character.gold} gold.")
        if game_state.current_character.inventory.is_full():
            return (True, "\nYour inventory is full!")
        # Create a copy of the item for the player
        new_item = Item(
            name=shop_item.item.name,
            description=shop_item.item.description,
            item_type=shop_item.item.item_type,
            damage_bonus=shop_item.item.damage_bonus,
            defense_bonus=shop_item.item.defense_bonus,
            heal_amount=shop_item.item.heal_amount
        )
        game_state.current_character.remove_gold(final_price)
        game_state.current_character.inventory.add_item(new_item)
        # Track quest progress for collect objectives
        quest_messages = game_state.current_character.record_collection(new_item.name)
        # Consume haggle bonus after purchase
        game_state.haggle_bonus = 0.0
        autosave(game_state)
        output = f"\nYou bought {new_item.name} for {final_price} gold."
        if quest_messages:
            output += "\n" + "\n".join(quest_messages)
        return (True, output)

    elif command == "sell":
        if game_state.current_shop is None:
            return (True, "\nYou're not at a shop. Talk to a merchant first.")
        # Check faction reputation before allowing sale
        from cli_rpg.faction_shop import get_faction_price_modifiers
        faction_buy_mod, faction_sell_mod, trade_refused = get_faction_price_modifiers(
            game_state.factions
        )
        if trade_refused:
            return (True, "\nThe merchants refuse to trade with you due to your poor reputation.")
        if not args:
            return (True, "\nSell what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
            # Check if item is equipped (not in regular inventory but still owned)
            inv = game_state.current_character.inventory
            item_name_lower = item_name.lower()
            if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
                return (
                    True,
                    f"\nYou can't sell {inv.equipped_weapon.name} because it's currently "
                    "equipped. Unequip it first with 'unequip weapon'.",
                )
            if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
                return (
                    True,
                    f"\nYou can't sell {inv.equipped_armor.name} because it's currently "
                    "equipped. Unequip it first with 'unequip armor'.",
                )
            return (True, f"\nYou don't have '{item_name}' in your inventory.")
        # Base sell price calculation with CHA modifier
        from cli_rpg.social_skills import get_cha_sell_modifier
        base_sell_price = 10 + (item.damage_bonus + item.defense_bonus + item.heal_amount) * 2
        cha_modifier = get_cha_sell_modifier(game_state.current_character.charisma)
        sell_price = int(base_sell_price * cha_modifier)
        # Apply faction reputation modifier
        if faction_sell_mod is not None:
            sell_price = int(sell_price * faction_sell_mod)
        # Apply haggle bonus if active
        if game_state.haggle_bonus > 0:
            sell_price = int(sell_price * (1 + game_state.haggle_bonus))
        game_state.current_character.inventory.remove_item(item)
        game_state.current_character.add_gold(sell_price)
        # Consume haggle bonus after sale
        game_state.haggle_bonus = 0.0
        autosave(game_state)
        return (True, f"\nYou sold {item.name} for {sell_price} gold.")

    elif command == "drop":
        if not args:
            return (True, "\nDrop what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
            # Check if item is equipped
            inv = game_state.current_character.inventory
            item_name_lower = item_name.lower()
            if inv.equipped_weapon and inv.equipped_weapon.name.lower() == item_name_lower:
                return (
                    True,
                    f"\nYou can't drop {inv.equipped_weapon.name} because it's equipped. "
                    "Unequip it first with 'unequip weapon'.",
                )
            if inv.equipped_armor and inv.equipped_armor.name.lower() == item_name_lower:
                return (
                    True,
                    f"\nYou can't drop {inv.equipped_armor.name} because it's equipped. "
                    "Unequip it first with 'unequip armor'.",
                )
            return (True, f"\nYou don't have '{item_name}' in your inventory.")
        game_state.current_character.inventory.remove_item(item)
        return (True, f"\nYou dropped {item.name}.")

    elif command == "persuade":
        # Social skill: Attempt to persuade the current NPC for benefits
        from cli_rpg.social_skills import attempt_persuade
        success, message = attempt_persuade(
            game_state.current_character, game_state.current_npc
        )
        return (True, f"\n{message}")

    elif command == "intimidate":
        # Social skill: Attempt to intimidate the current NPC
        from cli_rpg.social_skills import attempt_intimidate
        # Count kills from choices for reputation bonus
        kill_count = sum(
            1 for c in game_state.choices if c.get("choice_type") == "combat_kill"
        )
        success, message = attempt_intimidate(
            game_state.current_character, game_state.current_npc, kill_count
        )
        return (True, f"\n{message}")

    elif command == "bribe":
        # Social skill: Attempt to bribe the current NPC with gold
        from cli_rpg.social_skills import attempt_bribe
        amount = None
        if args:
            try:
                amount = int(args[0])
            except ValueError:
                return (True, "\nInvalid amount. Usage: bribe <gold amount>")
        success, message = attempt_bribe(
            game_state.current_character, game_state.current_npc, amount
        )
        return (True, f"\n{message}")

    elif command == "haggle":
        # Social skill: Attempt to haggle with merchant for better prices
        if game_state.current_shop is None:
            return (True, "\nYou're not at a shop. Talk to a merchant first.")
        from cli_rpg.social_skills import attempt_haggle
        success, message, bonus, cooldown = attempt_haggle(
            game_state.current_character, game_state.current_npc
        )
        # Apply effects
        if success:
            game_state.haggle_bonus = bonus
        if cooldown > 0:
            game_state.current_npc.haggle_cooldown = cooldown
        return (True, f"\n{message}")

    elif command == "accept":
        # Accept a quest from the current NPC
        if game_state.current_npc is None:
            return (True, "\nYou need to talk to an NPC first.")

        from cli_rpg.models.quest import Quest, QuestStatus

        npc = game_state.current_npc

        # Handle bare "accept" command - auto-accept if exactly one available quest
        if not args:
            # Check if NPC offers quests at all
            if not npc.is_quest_giver or not npc.offered_quests:
                return (True, f"\n{npc.name} doesn't offer any quests.")

            # Get available quests (filter out quests player already has)
            available_quests = [
                q for q in npc.offered_quests
                if not game_state.current_character.has_quest(q.name)
            ]

            if len(available_quests) == 0:
                return (True, f"\n{npc.name} doesn't offer any quests.")
            elif len(available_quests) == 1:
                # Auto-accept the single available quest
                args = [available_quests[0].name]
            else:
                # Multiple available quests - list them
                quest_names = ", ".join(q.name for q in available_quests)
                return (True, f"\nAccept what? Available: {quest_names}")

        quest_name = " ".join(args)
        npc = game_state.current_npc

        # Check if NPC offers quests
        if not npc.is_quest_giver or not npc.offered_quests:
            return (True, f"\n{npc.name} doesn't offer any quests.")

        # Find the quest by name (case-insensitive)
        matching_quest = None
        for q in npc.offered_quests:
            if q.name.lower() == quest_name.lower():
                matching_quest = q
                break

        if matching_quest is None:
            return (True, f"\n{npc.name} doesn't offer a quest called '{quest_name}'.")

        # Check if character already has this quest
        if game_state.current_character.has_quest(matching_quest.name):
            return (True, f"\nYou already have the quest '{matching_quest.name}'.")

        # Check faction reputation requirement
        if matching_quest.required_reputation is not None and matching_quest.faction_affiliation:
            from cli_rpg.faction_combat import _find_faction_by_name

            faction = _find_faction_by_name(
                game_state.factions, matching_quest.faction_affiliation
            )
            if faction and faction.reputation < matching_quest.required_reputation:
                return (
                    True,
                    f"\n{npc.name} refuses to give you this quest. "
                    f"You need higher reputation with {matching_quest.faction_affiliation}.",
                )

        # Check prerequisite quests
        if matching_quest.prerequisite_quests:
            completed_names = [
                q.name for q in game_state.current_character.quests
                if q.status == QuestStatus.COMPLETED
            ]
            if not matching_quest.prerequisites_met(completed_names):
                missing = [p for p in matching_quest.prerequisite_quests
                           if p.lower() not in {c.lower() for c in completed_names}]
                return (True, f"\nYou must first complete: {', '.join(missing)}")

        # Clone quest and set status to ACTIVE, then add to character
        # Bug fix: Include gold_reward, xp_reward, item_rewards, and set quest_giver
        new_quest = Quest(
            name=matching_quest.name,
            description=matching_quest.description,
            objective_type=matching_quest.objective_type,
            target=matching_quest.target,
            target_count=matching_quest.target_count,
            status=QuestStatus.ACTIVE,
            current_count=0,
            gold_reward=matching_quest.gold_reward,
            xp_reward=matching_quest.xp_reward,
            item_rewards=matching_quest.item_rewards.copy(),
            quest_giver=npc.name,
            faction_affiliation=matching_quest.faction_affiliation,
            faction_reward=matching_quest.faction_reward,
            faction_penalty=matching_quest.faction_penalty,
            required_reputation=matching_quest.required_reputation,
            chain_id=matching_quest.chain_id,
            chain_position=matching_quest.chain_position,
            prerequisite_quests=matching_quest.prerequisite_quests.copy(),
            unlocks_quests=matching_quest.unlocks_quests.copy(),
            difficulty=matching_quest.difficulty,
            recommended_level=matching_quest.recommended_level,
        )
        game_state.current_character.quests.append(new_quest)
        autosave(game_state)

        return (True, f"\nQuest accepted: {new_quest.name}\n{new_quest.description}")

    elif command == "complete":
        # Complete/turn in a quest to the current NPC
        if game_state.current_npc is None:
            return (True, "\nYou need to talk to an NPC first to turn in a quest.")

        if not args:
            return (True, "\nComplete which quest? Specify a quest name (e.g., 'complete goblin slayer').")

        quest_name = " ".join(args).lower()
        npc = game_state.current_npc

        # Find matching quest that is ready to turn in
        from cli_rpg.models.quest import QuestStatus
        matching_quest = None
        for q in game_state.current_character.quests:
            if (
                q.status == QuestStatus.READY_TO_TURN_IN
                and quest_name in q.name.lower()
            ):
                matching_quest = q
                break

        if matching_quest is None:
            return (True, f"\nNo quest ready to turn in matching '{' '.join(args)}'.")

        # Verify quest was given by this NPC
        if matching_quest.quest_giver != npc.name:
            return (
                True,
                f"\nYou can't turn in '{matching_quest.name}' to {npc.name}. "
                f"Return to {matching_quest.quest_giver} instead."
            )

        # Claim rewards and mark as completed
        reward_messages = game_state.current_character.claim_quest_rewards(
            matching_quest, factions=game_state.factions
        )
        matching_quest.status = QuestStatus.COMPLETED
        autosave(game_state)
        sound_quest_complete()

        output_lines = [f"\nQuest completed: {matching_quest.name}!"]
        output_lines.extend(reward_messages)

        # Check for companion quest bonus
        from cli_rpg.companion_quests import check_companion_quest_completion
        for companion in game_state.companions:
            bonus_messages = check_companion_quest_completion(companion, matching_quest.name)
            output_lines.extend(bonus_messages)

        return (True, "\n".join(output_lines))

    elif command == "abandon":
        # Abandon an active quest
        if not args:
            return (True, "\nAbandon which quest? Specify a quest name (e.g., 'abandon goblin slayer').")

        quest_name = " ".join(args)
        success, message = game_state.current_character.abandon_quest(quest_name)
        return (True, f"\n{message}")

    elif command == "map":
        map_output = render_map(
            game_state.world,
            game_state.current_location,
            game_state.current_sub_grid,
            game_state.chunk_manager,
        )
        return (True, f"\n{map_output}")

    elif command == "worldmap":
        worldmap_location = game_state.current_location
        if game_state.in_sub_location:
            current_loc = game_state.get_current_location()
            if current_loc.parent_location:
                worldmap_location = current_loc.parent_location
        worldmap_output = render_worldmap(game_state.world, worldmap_location)
        return (True, f"\n{worldmap_output}")

    elif command == "travel":
        if not args:
            # List destinations with travel times
            destinations = game_state.get_fast_travel_destinations()
            if not destinations:
                return (True, "\nNo fast travel destinations available yet.\nExplore named locations (towns, cities, dungeons) to unlock them.")
            else:
                current = game_state.get_current_location()
                lines = [f"\n{colors.location('Fast Travel Destinations:')}"]
                for dest in destinations:
                    loc = game_state.world[dest]
                    dx = abs(loc.coordinates[0] - current.coordinates[0])
                    dy = abs(loc.coordinates[1] - current.coordinates[1])
                    distance = dx + dy
                    hours = max(1, min(8, distance // 4))
                    lines.append(f"  {dest} ({hours}h travel)")
                lines.append("\nUsage: travel <location name>")
                return (True, "\n".join(lines))
        else:
            dest = " ".join(args)
            success, message = game_state.fast_travel(dest)
            return (True, f"\n{message}")

    elif command == "quests":
        quests = game_state.current_character.quests
        if not quests:
            return (True, "\n=== Quest Journal ===\nNo active quests.")

        # Separate active, ready to turn in, and completed quests
        from cli_rpg.models.quest import QuestStatus
        active_quests = [q for q in quests if q.status == QuestStatus.ACTIVE]
        ready_quests = [q for q in quests if q.status == QuestStatus.READY_TO_TURN_IN]
        completed_quests = [q for q in quests if q.status == QuestStatus.COMPLETED]

        lines = ["\n=== Quest Journal ==="]

        if ready_quests:
            lines.append("\nReady to Turn In:")
            for quest in ready_quests:
                giver_hint = f" (Return to {quest.quest_giver})" if quest.quest_giver else ""
                lines.append(f"  ★ {quest.name}{giver_hint}")

        if active_quests:
            lines.append("\nActive Quests:")
            diff_icons = {"trivial": ".", "easy": "-", "normal": "~", "hard": "!", "deadly": "!!"}
            for quest in active_quests:
                diff_icon = diff_icons.get(quest.difficulty.value, "~")
                lines.append(f"  {diff_icon} {quest.name} [{quest.current_count}/{quest.target_count}]")

        if completed_quests:
            lines.append("\nCompleted Quests:")
            for quest in completed_quests:
                lines.append(f"  ✓ {quest.name}")

        if not active_quests and not ready_quests and not completed_quests:
            # Handle edge case: quests exist but are in other states (AVAILABLE, FAILED)
            lines.append("No active quests.")

        return (True, "\n".join(lines))

    elif command == "quest":
        if not args:
            return (True, "\nWhich quest? Specify a quest name (e.g., 'quest kill goblins').")

        quest_name = " ".join(args).lower()
        quests = game_state.current_character.quests

        # Find quest by partial name match (case-insensitive)
        matching_quests = [q for q in quests if quest_name in q.name.lower()]

        if not matching_quests:
            return (True, f"\nNo quest found matching '{' '.join(args)}'.")

        # Show details of first matching quest
        quest = matching_quests[0]
        # Format status - show "Ready to Turn In" in a user-friendly way
        status_display = quest.status.value.replace("_", " ").title()
        lines = [
            f"\n=== {quest.name} ===",
            f"Status: {status_display}",
        ]
        if quest.quest_giver:
            lines.append(f"Quest Giver: {quest.quest_giver}")
        if quest.chain_id:
            chain_info = f"Part {quest.chain_position}" if quest.chain_position > 0 else "Prologue"
            lines.append(f"Chain: {quest.chain_id} ({chain_info})")
        if quest.prerequisite_quests:
            lines.append(f"Prerequisites: {', '.join(quest.prerequisite_quests)}")
        lines.extend([
            "",
            f"{quest.description}",
            "",
            f"Difficulty: {quest.difficulty.value.capitalize()} (Recommended: Lv.{quest.recommended_level})",
            f"Objective: {quest.objective_type.value.capitalize()} {quest.target}",
            f"Progress: {quest.current_count}/{quest.target_count}",
        ])
        return (True, "\n".join(lines))

    elif command == "bestiary":
        bestiary = game_state.current_character.bestiary
        if not bestiary:
            return (True, "\n=== Bestiary ===\nNo enemies defeated yet.")

        lines = ["\n=== Bestiary ===", ""]
        total_kills = 0

        # Sort by enemy name for consistent output
        for key in sorted(bestiary.keys()):
            entry = bestiary[key]
            count = entry["count"]
            data = entry["enemy_data"]
            total_kills += count

            lines.append(f"{data['name']} (x{count})")
            # Show ASCII art if available
            if data.get("ascii_art"):
                for art_line in data["ascii_art"].rstrip().split("\n"):
                    lines.append(f"  {art_line}")
            lines.append(f"  Level {data['level']} | ATK: {data['attack_power']} | DEF: {data['defense']}")
            if data.get("description"):
                lines.append(f'  "{data["description"]}"')
            lines.append("")

        lines.append(f"Total enemies defeated: {total_kills}")
        return (True, "\n".join(lines))

    elif command == "proficiency":
        from cli_rpg.models.weapon_proficiency import WeaponType, ProficiencyLevel
        from cli_rpg import colors

        proficiencies = game_state.current_character.weapon_proficiencies
        if not proficiencies:
            return (True, "\n=== Weapon Proficiencies ===\nNo weapon proficiencies yet. Attack with weapons to gain experience!")

        lines = ["\n=== Weapon Proficiencies ===", ""]

        # Sort by weapon type name for consistent output
        for weapon_type in sorted(proficiencies.keys(), key=lambda x: x.value):
            prof = proficiencies[weapon_type]
            level = prof.get_level()
            xp = prof.xp
            bonus = prof.get_damage_bonus()

            # Create progress bar (20 chars wide)
            progress = min(xp, 100)
            filled = int(progress / 5)  # 100 XP / 5 = 20 chars
            bar = "█" * filled + "░" * (20 - filled)

            # Level color based on rank
            if level == ProficiencyLevel.MASTER:
                level_str = colors.gold(level.value)
            elif level == ProficiencyLevel.EXPERT:
                level_str = colors.heal(level.value)
            elif level == ProficiencyLevel.JOURNEYMAN:
                level_str = colors.location(level.value)
            else:
                level_str = level.value

            # Damage bonus display
            bonus_pct = int((bonus - 1.0) * 100)
            if bonus_pct > 0:
                bonus_str = colors.heal(f"+{bonus_pct}% damage")
            else:
                bonus_str = "+0% damage"

            # Special move status
            if prof.is_special_enhanced():
                special_str = colors.gold(" [Special: Enhanced]")
            elif prof.can_use_special():
                special_str = colors.location(" [Special: Unlocked]")
            else:
                special_str = ""

            weapon_name = weapon_type.value.capitalize()
            lines.append(f"{weapon_name}: {level_str}")
            lines.append(f"  XP: [{bar}] {xp}/100")
            lines.append(f"  Bonus: {bonus_str}{special_str}")
            lines.append("")

        return (True, "\n".join(lines))

    elif command == "events":
        from cli_rpg.world_events import get_active_events_display
        return (True, get_active_events_display(game_state))

    elif command == "resolve":
        from cli_rpg.world_events import (
            find_event_by_name,
            can_resolve_event,
            try_resolve_event,
            get_resolution_requirements,
        )

        if not args:
            # List all active events with resolution requirements
            active = [e for e in game_state.world_events if e.is_active]
            if not active:
                return (True, "\nNo active events to resolve.")

            lines = ["\n=== Active Events ==="]
            for event in active:
                location = event.affected_locations[0] if event.affected_locations else "Unknown"
                at_location = game_state.current_location in event.affected_locations
                location_marker = " ← You are here" if at_location else ""
                requirements = get_resolution_requirements(event)
                lines.append(f"\n{event.name} ({event.event_type})")
                lines.append(f"  Location: {location}{location_marker}")
                lines.append(f"  How to resolve: {requirements}")
            lines.append("\nUse: resolve <event name>")
            return (True, "\n".join(lines))

        event_name = " ".join(args)
        event = find_event_by_name(game_state, event_name)

        if event is None:
            return (True, f"\nNo active event matching '{event_name}'.")

        # Try to resolve
        success, message = try_resolve_event(game_state, event)
        return (True, f"\n{message}")

    elif command == "companions":
        if not game_state.companions:
            return (True, "\nNo companions in your party.")

        lines = ["\n=== Your Companions ==="]
        for companion in game_state.companions:
            lines.append(f"\n{companion.name}")
            lines.append(f"  {companion.description}")
            lines.append(f"  {companion.get_bond_display()}")
            lines.append(f"  Recruited at: {companion.recruited_at}")
        return (True, "\n".join(lines))

    elif command == "reputation":
        if not game_state.factions:
            return (True, "\nNo factions discovered yet.")

        lines = ["\n=== Faction Reputation ==="]
        for faction in game_state.factions:
            lines.append(f"\n{faction.name}")
            lines.append(f"  {faction.description}")
            lines.append(f"  {faction.get_reputation_display()}")
        return (True, "\n".join(lines))

    elif command == "recruit":
        if not args:
            return (True, "\nRecruit whom? Specify an NPC name.")

        from cli_rpg.models.companion import Companion

        npc_name = " ".join(args)
        location = game_state.get_current_location()

        # Find NPC by name (case-insensitive)
        npc = location.find_npc_by_name(npc_name)
        if npc is None:
            return (True, f"\nYou don't see '{npc_name}' here.")

        # Check if NPC is recruitable
        if not npc.is_recruitable:
            return (True, f"\n{npc.name} cannot be recruited to join your party.")

        # Check if already in party
        if any(c.name.lower() == npc.name.lower() for c in game_state.companions):
            return (True, f"\n{npc.name} is already in your party.")

        # Create companion from NPC data
        companion = Companion(
            name=npc.name,
            description=npc.description,
            recruited_at=game_state.current_location,
            bond_points=0
        )
        game_state.companions.append(companion)

        return (True, f"\n{npc.name} has joined your party!")

    elif command == "dismiss":
        if not args:
            return (True, "\nDismiss whom? Specify a companion name.")

        companion_name = " ".join(args).lower()
        matching = [c for c in game_state.companions if c.name.lower() == companion_name]

        if not matching:
            return (True, f"\nNo companion named '{' '.join(args)}' in your party.")

        companion = matching[0]

        # Skip confirmation in non-interactive mode
        if non_interactive:
            game_state.companions.remove(companion)
            return (True, f"\n{companion.name} has left your party.")

        # Show confirmation with bond info
        from cli_rpg.models.companion import BondLevel
        bond_level = companion.get_bond_level()
        if bond_level in (BondLevel.TRUSTED, BondLevel.DEVOTED):
            print(f"\n⚠️  {companion.name} is {bond_level.value} ({companion.bond_points}% bond).")
            print("Dismissing will reduce their bond significantly if you meet again.")
        else:
            print(f"\n{companion.name} ({bond_level.value}, {companion.bond_points}% bond)")

        sys.stdout.flush()
        response = input(f"Dismiss {companion.name}? (y/n): ").strip().lower()

        if response == 'y':
            game_state.companions.remove(companion)
            return (True, f"\n{companion.name} has left your party.")
        else:
            return (True, f"\n{companion.name} remains in your party.")

    elif command == "companion-quest":
        # View/accept a companion's personal quest
        if not args:
            return (True, "\nWhich companion? Use: companion-quest <name>")

        companion_name = " ".join(args).lower()
        matching = [c for c in game_state.companions if c.name.lower() == companion_name]

        if not matching:
            return (True, f"\nNo companion named '{' '.join(args)}' in your party.")

        companion = matching[0]

        from cli_rpg.companion_quests import is_quest_available, accept_companion_quest

        if companion.personal_quest is None:
            return (True, f"\n{companion.name} has no personal quest.")

        if not is_quest_available(companion):
            bond_level = companion.get_bond_level().value
            return (
                True,
                f"\n{companion.name}'s personal quest is not yet available.\n"
                f"Build more trust. (Current: {bond_level}, Need: Trusted)"
            )

        # Check if already have quest
        if game_state.current_character.has_quest(companion.personal_quest.name):
            return (
                True,
                f"\nYou already have {companion.name}'s quest: {companion.personal_quest.name}"
            )

        # Accept quest
        new_quest = accept_companion_quest(companion)
        if new_quest is None:
            return (True, f"\nFailed to accept {companion.name}'s quest.")

        game_state.current_character.quests.append(new_quest)

        return (
            True,
            f"\n{companion.name}'s Quest Accepted: {new_quest.name}\n{new_quest.description}"
        )

    elif command == "pick":
        # Lockpicking command - Rogue only
        import random
        from cli_rpg.models.character import CharacterClass

        # Check if character is a Rogue
        if game_state.current_character.character_class != CharacterClass.ROGUE:
            return (True, "\nOnly Rogues can pick locks. This requires specialized training.")

        # Check for lockpick in inventory
        lockpick = game_state.current_character.inventory.find_item_by_name("Lockpick")
        if lockpick is None:
            return (True, "\nYou need a Lockpick to attempt picking a lock.")

        if not args:
            return (True, "\nPick what? Specify a chest name.")

        # Find the chest by name (partial match)
        chest_name = " ".join(args).lower()
        location = game_state.get_current_location()

        if not hasattr(location, 'treasures') or not location.treasures:
            return (True, "\nThere are no chests here.")

        target_chest = None
        for treasure in location.treasures:
            if chest_name in treasure["name"].lower():
                target_chest = treasure
                break

        if target_chest is None:
            return (True, f"\nNo chest matching '{' '.join(args)}' found here.")

        if not target_chest["locked"]:
            return (True, f"\n{target_chest['name']} is not locked.")

        if target_chest["opened"]:
            return (True, f"\n{target_chest['name']} has already been opened.")

        # Consume the lockpick
        game_state.current_character.inventory.remove_item(lockpick)

        # Calculate success chance: 20% base + (DEX * 2%), capped at 80%
        dexterity = game_state.current_character.dexterity
        base_chance = 20 + (dexterity * 2)

        # Apply difficulty modifier: +20%/+10%/0%/-10%/-20% for difficulty 1-5
        difficulty = target_chest.get("difficulty", 3)
        difficulty_mod = {1: 20, 2: 10, 3: 0, 4: -10, 5: -20}.get(difficulty, 0)
        success_chance = min(80, base_chance + difficulty_mod)

        # Roll for success (lower is better - roll must be below success_chance / 100)
        roll = random.random() * 100
        if roll < success_chance:
            target_chest["locked"] = False
            return (True, f"\n✓ Success! You picked the lock on {target_chest['name']}.")
        else:
            return (True, f"\n✗ The lockpick breaks in the lock. {target_chest['name']} remains locked.")

    elif command == "open":
        # Open a chest (anyone can use for unlocked chests)
        if not args:
            return (True, "\nOpen what? Specify a chest name.")

        chest_name = " ".join(args).lower()
        location = game_state.get_current_location()

        if not hasattr(location, 'treasures') or not location.treasures:
            return (True, "\nThere are no chests here.")

        target_chest = None
        for treasure in location.treasures:
            if chest_name in treasure["name"].lower():
                target_chest = treasure
                break

        if target_chest is None:
            return (True, f"\nNo chest matching '{' '.join(args)}' found here.")

        if target_chest["locked"]:
            return (True, f"\n{target_chest['name']} is locked. You need to unlock it first.")

        if target_chest["opened"]:
            return (True, f"\n{target_chest['name']} has already been opened. It's empty now.")

        # Open the chest and transfer items
        target_chest["opened"] = True

        items_added = []
        for item_data in target_chest.get("items", []):
            # Create item from data
            item_type_str = item_data.get("item_type", "misc")
            try:
                item_type = ItemType(item_type_str)
            except ValueError:
                item_type = ItemType.MISC

            new_item = Item(
                name=item_data["name"],
                description=item_data.get("description", "An item from the chest"),
                item_type=item_type,
                damage_bonus=item_data.get("damage_bonus", 0),
                defense_bonus=item_data.get("defense_bonus", 0),
                heal_amount=item_data.get("heal_amount", 0)
            )
            if game_state.current_character.inventory.add_item(new_item):
                items_added.append(new_item.name)

        if items_added:
            items_list = ", ".join(items_added)
            return (True, f"\nYou open {target_chest['name']} and find: {items_list}")
        else:
            return (True, f"\nYou open {target_chest['name']}, but it's empty.")

    elif command == "help":
        return (True, "\n" + get_command_reference())

    elif command == "dump-state":
        import json
        state_dict = game_state.to_dict()
        return (True, f"\n{json.dumps(state_dict, indent=2)}")

    elif command == "save":
        try:
            filepath = save_game_state(game_state)
            return (True, f"\n✓ Game saved successfully!\n  Save location: {filepath}")
        except IOError as e:
            return (True, f"\n✗ Failed to save game: {e}")
    
    elif command == "quit":
        if non_interactive:
            # In non-interactive mode, skip save prompt and exit directly
            return (False, "\nExiting game...")
        print("\n" + "=" * 50)
        response = input("Save before quitting? (y/n): ").strip().lower()
        if response == 'y':
            try:
                filepath = save_game_state(game_state)
                print("\n✓ Game saved successfully!")
                print(f"  Save location: {filepath}")
            except IOError as e:
                print(f"\n✗ Failed to save game: {e}")

        print("\nReturning to main menu...")
        return (False, "")

    elif command == "lore":
        import random
        if game_state.ai_service is None:
            return (True, "\n=== Ancient Lore ===\nNo mystical knowledge is available in this realm.")

        categories = ["history", "legend", "secret"]
        category = random.choice(categories)
        headers = {
            "history": "Ancient History",
            "legend": "Local Legend",
            "secret": "Forbidden Secret"
        }

        try:
            lore = game_state.ai_service.generate_lore(
                theme=game_state.theme,
                location_name=game_state.current_location,
                lore_category=category
            )
            return (True, f"\n=== {headers[category]} ===\n{lore}")
        except Exception:
            return (True, "\n=== Ancient Lore ===\nThe mysteries of this place remain hidden...")

    elif command == "rest":
        # Parse --quick or -q flag to skip dreams
        skip_dream = "--quick" in args or "-q" in args
        # Remove flags from args for any future processing
        args = [a for a in args if a not in ("--quick", "-q")]

        # Check if already at full health, stamina, dread, and tiredness
        char = game_state.current_character
        at_full_health = char.health >= char.max_health
        at_full_stamina = char.stamina >= char.max_stamina
        no_dread = char.dread_meter.dread == 0
        no_tiredness = char.tiredness.current == 0
        # Save pre-rest tiredness for dream check (dreams occur based on how tired you were)
        pre_rest_tiredness = char.tiredness.current

        if at_full_health and at_full_stamina and no_dread and no_tiredness:
            return (True, "\nYou're already at full health, stamina, and feeling calm and rested!")

        messages = []

        # Calculate heal amount: 25% of max HP, minimum 1
        if at_full_health:
            messages.append(f"HP: {char.health}/{char.max_health} (already full)")
        else:
            heal_amount = max(1, char.max_health // 4)
            actual_heal = min(heal_amount, char.max_health - char.health)
            char.heal(actual_heal)
            messages.append(f"You rest and recover {actual_heal} health.")

        # Calculate stamina restore: 25% of max stamina, minimum 1
        if at_full_stamina:
            messages.append(f"Stamina: {char.stamina}/{char.max_stamina} (already full)")
        else:
            stamina_amount = max(1, char.max_stamina // 4)
            old_stamina = char.stamina
            char.restore_stamina(stamina_amount)
            actual_restore = char.stamina - old_stamina
            if actual_restore > 0:
                messages.append(f"You recover {actual_restore} stamina.")

        # Reduce dread by 20
        if not no_dread:
            old_dread = char.dread_meter.dread
            char.dread_meter.reduce_dread(20)
            dread_reduced = old_dread - char.dread_meter.dread
            if dread_reduced > 0:
                messages.append(f"The peaceful rest eases your mind (Dread -{dread_reduced}%).")

        # Reduce tiredness based on sleep quality
        if not no_tiredness:
            quality = char.tiredness.sleep_quality()
            if quality == "deep":
                tiredness_reduction = 80
            elif quality == "normal":
                tiredness_reduction = 50
            else:  # light
                tiredness_reduction = 25
            old_tiredness = char.tiredness.current
            char.tiredness.decrease(tiredness_reduction)
            actual_reduction = old_tiredness - char.tiredness.current
            if actual_reduction > 0:
                messages.append(f"Tiredness -{actual_reduction}% ({quality} rest).")

        # Advance time by 4 hours for rest
        game_state.game_time.advance(4)

        # Build the rest message first
        result_message = "\n" + " ".join(messages)

        # Check for dream during rest (skip if --quick flag)
        # Use pre-rest tiredness - dreams are based on how tired you were when going to sleep
        if not skip_dream:
            dream = maybe_trigger_dream(
                dread=char.dread_meter.dread,
                choices=getattr(game_state, 'choices', None),
                theme=getattr(game_state, 'theme', 'fantasy'),
                ai_service=getattr(game_state, 'ai_service', None),
                location_name=game_state.current_location,
                tiredness=pre_rest_tiredness,
                last_dream_hour=game_state.last_dream_hour,
                current_hour=game_state.game_time.total_hours,
            )
            if dream:
                # Update last_dream_hour for cooldown tracking
                game_state.last_dream_hour = game_state.game_time.total_hours
                # Print rest message first, then display dream with typewriter effect
                print(result_message)
                display_dream(dream)
                return (True, result_message)  # Return message for test assertions

        return (True, result_message)

    elif command == "camp":
        from cli_rpg.camping import execute_camp
        success, msg = execute_camp(game_state)
        return (True, f"\n{msg}" if msg else "\n")

    elif command == "forage":
        from cli_rpg.camping import execute_forage
        success, msg = execute_forage(game_state)
        return (True, f"\n{msg}")

    elif command == "hunt":
        from cli_rpg.camping import execute_hunt
        success, msg = execute_hunt(game_state)
        return (True, f"\n{msg}")

    elif command == "gather":
        from cli_rpg.crafting import execute_gather
        success, msg = execute_gather(game_state)
        return (True, f"\n{msg}")

    elif command == "craft":
        from cli_rpg.crafting import execute_craft
        if not args:
            return (True, "\nCraft what? Use 'recipes' to see available recipes.")
        recipe_name = " ".join(args)
        success, msg = execute_craft(game_state, recipe_name)
        return (True, f"\n{msg}")

    elif command == "recipes":
        from cli_rpg.crafting import get_recipes_list
        return (True, f"\n{get_recipes_list()}")

    elif command in ["attack", "defend", "block", "parry", "flee", "rest", "cast",
                      "fireball", "ice_bolt", "heal", "bash", "bless", "smite", "hide"]:
        return (True, "\n✗ Not in combat.")
    
    elif command == "unknown":
        if args and args[0]:
            # Handle "bye" specially - it's for ending conversations, don't suggest "buy"
            if args[0] == "bye":
                return (True, "\n✗ The 'bye' command ends conversations. Use it while talking to an NPC.")
            suggestion = suggest_command(args[0], KNOWN_COMMANDS)
            if suggestion:
                return (True, f"\n✗ Unknown command '{args[0]}'. Did you mean '{suggestion}'?")
        return (True, "\n✗ Unknown command. Type 'help' for a list of commands.")

    else:
        return (True, "\n✗ Unknown command. Type 'help' for a list of commands.")


def run_game_loop(game_state: GameState) -> None:
    """Run the main gameplay loop.

    Args:
        game_state: The game state to run the loop for
    """
    # Set up completer context for tab completion
    set_completer_context(game_state)

    try:
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

            # Show conversation prompt if in conversation
            if game_state.is_in_conversation and game_state.current_npc is not None:
                print(f"\n[Talking to {game_state.current_npc.name}]")

            print()
            command_input = get_input("> ")

            if not command_input:
                continue

            # Parse command
            command, args = parse_command(command_input)

            # Route command based on combat state
            if game_state.is_in_combat():
                continue_game, message = handle_combat_command(game_state, command, args)
                print(message)

                if not continue_game:
                    break

                # Show combat status after each action if still in combat
                if game_state.is_in_combat() and game_state.current_combat is not None:
                    print("\n" + game_state.current_combat.get_status())
            elif game_state.is_in_conversation and command == "unknown":
                # In conversation mode - route to conversation handler
                continue_game, message = handle_conversation_input(game_state, command_input)
                print(message)

                if not continue_game:
                    break
            else:
                continue_game, message = handle_exploration_command(game_state, command, args)
                print(message)

                if not continue_game:
                    break
    finally:
        # Clear completer context when exiting the game loop
        set_completer_context(None)


def start_game(
    character: Character,
    ai_service: Optional[AIService] = None,
    theme: str = "fantasy",
    strict: bool = True,
    use_wfc: bool = True,
) -> None:
    """Start the gameplay loop with the given character.

    Args:
        character: The player's character to start the game with
        ai_service: Optional AIService for AI-powered world generation
        theme: World theme for generation (default: "fantasy")
        strict: If True (default), AI generation failures raise exceptions.
                If False, falls back to default world on AI error.
        use_wfc: If True, enable WFC terrain generation for procedural world
    """
    # Create game state with AI-powered or default world
    try:
        world, starting_location = create_world(
            ai_service=ai_service, theme=theme, strict=strict
        )
    except Exception as e:
        # AI generation failed in strict mode - offer options to user
        print(f"\n{'=' * 50}")
        print(f"AI world generation failed: {e}")
        print("=" * 50)
        print("\nOptions:")
        print("1. Retry AI generation")
        print("2. Use default world")
        print("3. Return to main menu")

        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            if choice == "1":
                # Retry with same parameters
                return start_game(
                    character, ai_service=ai_service, theme=theme, strict=strict, use_wfc=use_wfc
                )
            elif choice == "2":
                # Use default world (non-strict mode)
                world, starting_location = create_world(
                    ai_service=ai_service, theme=theme, strict=False
                )
                break
            elif choice == "3":
                # Return to main menu
                return
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    # Validate world is not empty
    if not world:
        raise ValueError("create_world() returned empty world")
    
    # Validate starting location exists in world
    if starting_location not in world:
        raise ValueError(f"Starting location '{starting_location}' not found in world")

    # Initialize WFC ChunkManager if enabled
    chunk_manager = None
    if use_wfc:
        import random as rnd
        from cli_rpg.wfc_chunks import ChunkManager
        from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY
        chunk_manager = ChunkManager(
            tile_registry=DEFAULT_TILE_REGISTRY,
            world_seed=rnd.randint(0, 2**32 - 1),
        )
        # Sync WFC terrain with existing location coordinates
        chunk_manager.sync_with_locations(world)
        print("✓ WFC terrain generation enabled!")

    game_state = GameState(
        character,
        world,
        starting_location=starting_location,
        ai_service=ai_service,
        theme=theme,
        chunk_manager=chunk_manager,
    )

    # Initialize default factions
    from cli_rpg.world import get_default_factions
    game_state.factions = get_default_factions()

    # Display welcome message
    print("\n" + "=" * 50)
    print(f"Welcome to the adventure, {character.name}!")
    if ai_service:
        print(f"Exploring a {theme} world powered by AI...")
    print("=" * 50)
    print("\n" + get_command_reference())
    print("=" * 50)

    # Show starting location
    print("\n" + game_state.look())
    
    # Run the game loop
    run_game_loop(game_state)


def show_main_menu() -> str:
    """Display main menu and get user choice.

    Returns:
        User's choice as a string
    """
    print("\n" + "=" * 50)
    print("MAIN MENU")
    print("=" * 50)
    print("1. Create New Character")
    print("2. Load Character")
    print("3. Exit")
    print("=" * 50)
    choice = input("Enter your choice: ").strip()
    return choice


def run_json_mode(
    log_file: Optional[str] = None,
    delay_ms: int = 0,
    skip_character_creation: bool = False,
    seed: Optional[int] = None
) -> int:
    """Run game in JSON mode, emitting structured JSON Lines output.

    This mode is designed for programmatic consumption by external tools
    or AI agents. It can either create a custom character from stdin or
    use a default character.

    Args:
        log_file: Optional path to write session transcript (JSON Lines format)
        delay_ms: Delay in milliseconds between commands (0 = no delay)
        skip_character_creation: If True, use default character. If False, read
            character creation inputs from stdin.
        seed: Optional RNG seed. If None, a random seed will be generated.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import time
    from cli_rpg.colors import set_colors_enabled
    from cli_rpg.models.character import Character
    from cli_rpg.json_output import (
        emit_state, emit_narrative, emit_actions, emit_error, emit_combat,
        classify_output, emit_session_info
    )
    from cli_rpg.logging_service import GameplayLogger

    # Disable ANSI colors, typewriter effects, and sounds for machine-readable output
    set_colors_enabled(False)
    set_effects_enabled(False)
    set_sound_enabled(False)

    # Load AI configuration
    ai_config = load_ai_config()
    ai_service = None
    if ai_config:
        try:
            ai_service = AIService(ai_config)
        except Exception:
            pass  # Silently fall back to non-AI mode

    # Create character
    if skip_character_creation:
        # Use default character (backward compatible behavior)
        character = Character(name="Agent", strength=10, dexterity=10, intelligence=10)
    else:
        # Read character creation from stdin
        character, error = create_character_non_interactive(json_mode=True)
        if character is None:
            emit_error(code="character_creation_failed", message=error)
            return 1

    world, starting_location = create_world(ai_service=ai_service, theme="fantasy", strict=False)

    # Generate seed if not provided, and use it for ChunkManager
    import random as rnd
    if seed is None:
        seed = rnd.randint(0, 2**31 - 1)

    # Initialize WFC ChunkManager for terrain generation
    from cli_rpg.wfc_chunks import ChunkManager
    from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY
    chunk_manager = ChunkManager(
        tile_registry=DEFAULT_TILE_REGISTRY,
        world_seed=seed,
    )
    # Sync WFC terrain with existing location coordinates
    chunk_manager.sync_with_locations(world)

    game_state = GameState(
        character,
        world,
        starting_location=starting_location,
        ai_service=ai_service,
        theme="fantasy",
        chunk_manager=chunk_manager,
    )

    # Initialize default factions
    from cli_rpg.world import get_default_factions
    game_state.factions = get_default_factions()

    # Initialize logger if log file specified
    logger: Optional[GameplayLogger] = None
    if log_file:
        logger = GameplayLogger(log_file)
        logger.log_session_start(
            character_name=character.name,
            location=starting_location,
            theme="fantasy",
            seed=seed
        )

    # Emit session info with seed for reproducibility
    emit_session_info(seed=seed, theme="fantasy")

    def get_available_commands() -> list[str]:
        """Get list of available commands based on current state."""
        if game_state.is_in_combat():
            return ["attack", "defend", "block", "parry", "cast", "flee", "use", "status", "help", "quit"]
        return list(KNOWN_COMMANDS)

    def emit_current_state() -> None:
        """Emit current game state as JSON."""
        char = game_state.current_character
        emit_state(
            location=game_state.current_location,
            health=char.health,
            max_health=char.max_health,
            gold=char.gold,
            level=char.level
        )

    def emit_current_actions() -> None:
        """Emit available actions as JSON."""
        location = game_state.get_current_location()
        # Get exits from coordinate-based directions
        if game_state.in_sub_location:
            exits = location.get_available_directions(sub_grid=game_state.current_sub_grid)
        else:
            exits = location.get_available_directions(world=game_state.world)
        npcs = [npc.name for npc in location.npcs] if location.npcs else []
        commands = get_available_commands()
        emit_actions(exits=exits, npcs=npcs, commands=commands)

    def emit_combat_state() -> None:
        """Emit combat state if in combat."""
        if game_state.is_in_combat() and game_state.current_combat:
            combat = game_state.current_combat
            emit_combat(
                enemy=combat.enemy.name,
                enemy_health=combat.enemy.health,
                player_health=game_state.current_character.health
            )

    # Emit initial state
    emit_current_state()
    look_output = game_state.look()
    emit_narrative(look_output)
    emit_current_actions()

    # Log initial state if logger is active
    if logger:
        logger.log_response(look_output)
        logger.log_state(
            location=game_state.current_location,
            health=character.health,
            max_health=character.max_health,
            gold=character.gold,
            level=character.level
        )

    end_reason = "eof"

    # Read commands from stdin until EOF
    for line in sys.stdin:
        command_input = line.strip()
        if not command_input:
            continue

        # Log command
        if logger:
            logger.log_command(command_input)

        # Parse and execute command
        command, args = parse_command(command_input)

        if game_state.is_in_combat():
            continue_game, message = handle_combat_command(game_state, command, args, non_interactive=True)
        elif game_state.is_in_conversation and command == "unknown":
            continue_game, message = handle_conversation_input(game_state, command_input)
        else:
            continue_game, message = handle_exploration_command(game_state, command, args, non_interactive=True)

        # Clean up message (remove leading newlines)
        message = message.strip()

        # Special handling for dump-state command in JSON mode
        if command == "dump-state":
            from cli_rpg.json_output import emit_dump_state
            state_dict = game_state.to_dict()
            emit_dump_state(state_dict)
        # Classify and emit output
        elif message:
            msg_type, error_code = classify_output(message)
            if msg_type == "error" and error_code:
                emit_error(code=error_code, message=message)
            else:
                emit_narrative(message)

        # Log response and state
        if logger:
            logger.log_response(message)
            logger.log_state(
                location=game_state.current_location,
                health=game_state.current_character.health,
                max_health=game_state.current_character.max_health,
                gold=game_state.current_character.gold,
                level=game_state.current_character.level
            )

        # Emit state after each command
        emit_current_state()

        # Emit combat state if in combat
        if game_state.is_in_combat():
            emit_combat_state()
        else:
            emit_current_actions()

        if not continue_game:
            end_reason = "quit"
            break

        # Check if player died
        if not game_state.current_character.is_alive():
            emit_narrative("GAME OVER - You have fallen in battle.")
            end_reason = "death"
            break

        # Apply delay between commands if specified
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

    # Close logger
    if logger:
        logger.log_session_end(end_reason)
        logger.close()

    return 0


def run_non_interactive(
    log_file: Optional[str] = None,
    delay_ms: int = 0,
    skip_character_creation: bool = False,
    seed: Optional[int] = None
) -> int:
    """Run game in non-interactive mode, reading commands from stdin.

    This mode is designed for automated testing and AI agent playtesting.
    It can either create a custom character from stdin or use a default character.

    Args:
        log_file: Optional path to write session transcript (JSON Lines format)
        delay_ms: Delay in milliseconds between commands (0 = no delay)
        skip_character_creation: If True, use default character. If False, read
            character creation inputs from stdin.
        seed: Optional RNG seed. If None, a random seed will be generated.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    import time
    from cli_rpg.colors import set_colors_enabled
    from cli_rpg.models.character import Character
    from cli_rpg.logging_service import GameplayLogger

    # Disable ANSI colors, typewriter effects, and sounds for machine-readable output
    set_colors_enabled(False)
    set_effects_enabled(False)
    set_sound_enabled(False)

    # Load AI configuration
    ai_config = load_ai_config()
    ai_service = None
    if ai_config:
        try:
            ai_service = AIService(ai_config)
        except Exception:
            pass  # Silently fall back to non-AI mode

    # Create character
    if skip_character_creation:
        # Use default character (backward compatible behavior)
        character = Character(name="Agent", strength=10, dexterity=10, intelligence=10)
    else:
        # Read character creation from stdin
        character, error = create_character_non_interactive(json_mode=False)
        if character is None:
            print(error)
            return 1

    world, starting_location = create_world(ai_service=ai_service, theme="fantasy", strict=False)

    # Generate seed if not provided, and use it for ChunkManager
    import random as rnd
    if seed is None:
        seed = rnd.randint(0, 2**31 - 1)

    # Initialize WFC ChunkManager for terrain generation
    from cli_rpg.wfc_chunks import ChunkManager
    from cli_rpg.world_tiles import DEFAULT_TILE_REGISTRY
    chunk_manager = ChunkManager(
        tile_registry=DEFAULT_TILE_REGISTRY,
        world_seed=seed,
    )
    # Sync WFC terrain with existing location coordinates
    chunk_manager.sync_with_locations(world)

    game_state = GameState(
        character,
        world,
        starting_location=starting_location,
        ai_service=ai_service,
        theme="fantasy",
        chunk_manager=chunk_manager,
    )

    # Initialize default factions
    from cli_rpg.world import get_default_factions
    game_state.factions = get_default_factions()

    # Initialize logger if log file specified
    logger: Optional[GameplayLogger] = None
    if log_file:
        logger = GameplayLogger(log_file)
        logger.log_session_start(
            character_name=character.name,
            location=starting_location,
            theme="fantasy",
            seed=seed
        )

    # Show starting location
    look_output = game_state.look()
    print(look_output)
    if logger:
        logger.log_response(look_output)
        logger.log_state(
            location=game_state.current_location,
            health=character.health,
            max_health=character.max_health,
            gold=character.gold,
            level=character.level
        )

    end_reason = "eof"

    # Read commands from stdin until EOF
    for line in sys.stdin:
        command_input = line.strip()
        if not command_input:
            continue

        # Log command
        if logger:
            logger.log_command(command_input)

        # Parse and execute command
        command, args = parse_command(command_input)

        if game_state.is_in_combat():
            continue_game, message = handle_combat_command(game_state, command, args, non_interactive=True)
        elif game_state.is_in_conversation and command == "unknown":
            continue_game, message = handle_conversation_input(game_state, command_input)
        else:
            continue_game, message = handle_exploration_command(game_state, command, args, non_interactive=True)

        print(message)

        # Log response and state
        if logger:
            logger.log_response(message.strip())
            logger.log_state(
                location=game_state.current_location,
                health=game_state.current_character.health,
                max_health=game_state.current_character.max_health,
                gold=game_state.current_character.gold,
                level=game_state.current_character.level
            )

        # Show combat status if in combat
        if game_state.is_in_combat() and game_state.current_combat is not None:
            print(game_state.current_combat.get_status())

        if not continue_game:
            end_reason = "quit"
            break

        # Check if player died
        if not game_state.current_character.is_alive():
            print("GAME OVER - You have fallen in battle.")
            end_reason = "death"
            break

        # Apply delay between commands if specified
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

    # Close logger
    if logger:
        logger.log_session_end(end_reason)
        logger.close()

    return 0


def parse_args(args: Optional[list] = None):
    """Parse command-line arguments.

    Args:
        args: Command-line arguments. If None, uses sys.argv[1:].
              Pass [] in tests to avoid parsing pytest arguments.

    Returns:
        Parsed arguments namespace.
    """
    import argparse

    parser = argparse.ArgumentParser(description="CLI RPG - A command-line role-playing game")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode, reading commands from stdin"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON Lines (implies --non-interactive)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        metavar="PATH",
        help="Write session transcript to file (JSON Lines format)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        metavar="N",
        help="Set random seed for reproducible gameplay"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        metavar="MS",
        help="Delay in milliseconds between commands (non-interactive/JSON modes)"
    )
    parser.add_argument(
        "--skip-character-creation",
        action="store_true",
        help="Skip character creation and use default character (non-interactive/JSON modes only)"
    )
    parser.add_argument(
        "--no-wfc",
        action="store_true",
        help="Disable WFC terrain generation (use fixed world instead)"
    )
    return parser.parse_args(args)


def main(args: Optional[list] = None) -> int:
    """Main function to start the CLI RPG game.

    Args:
        args: Command-line arguments. If None, uses sys.argv[1:].
              Pass [] in tests to avoid parsing pytest arguments.

    Returns:
        Exit code (0 for success)
    """
    parsed_args = parse_args(args)

    # Generate seed early if not provided, for consistent use across all modes
    import random
    if parsed_args.seed is not None:
        seed = parsed_args.seed
    else:
        seed = random.randint(0, 2**31 - 1)
    random.seed(seed)

    # Clamp delay to valid range (0-60000ms)
    delay_ms = max(0, min(60000, parsed_args.delay))

    if parsed_args.json:
        return run_json_mode(
            log_file=parsed_args.log_file,
            delay_ms=delay_ms,
            skip_character_creation=parsed_args.skip_character_creation,
            seed=seed
        )

    if parsed_args.non_interactive:
        return run_non_interactive(
            log_file=parsed_args.log_file,
            delay_ms=delay_ms,
            skip_character_creation=parsed_args.skip_character_creation,
            seed=seed
        )

    # Initialize readline for command history (arrow keys navigation)
    init_readline()

    print("\n" + "=" * 50)
    print("Welcome to CLI RPG!")
    print("=" * 50)

    # Load AI configuration at startup
    ai_config = load_ai_config()
    ai_service = None
    strict_mode = is_ai_strict_mode()
    use_wfc = not parsed_args.no_wfc

    if ai_config:
        try:
            ai_service = AIService(ai_config)
            print("\n✓ AI world generation enabled!")
            if strict_mode:
                print("  Strict mode: AI failures will prompt for action.")
            else:
                print("  Fallback mode: Will use default world if AI fails.")
        except Exception as e:
            print(f"\n⚠ AI initialization failed: {e}")
            print("  Falling back to default world generation.")
    else:
        print("\n⚠ AI world generation not available.")
        print("  Set OPENAI_API_KEY to enable AI features.")
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            # Create new character
            character = create_character()
            if character:
                print(f"\n✓ {character.name} has been created successfully!")
                
                # Theme selection (if AI is available)
                theme = "fantasy"
                if ai_service:
                    theme = get_theme_selection()
                    print(f"\n✓ Selected theme: {theme}")
                
                print("Your character is ready for adventure!")

                # Start the game with AI service and theme
                start_game(
                    character, ai_service=ai_service, theme=theme, strict=strict_mode, use_wfc=use_wfc
                )
                
        elif choice == "2":
            # Load character or game state
            character, game_state = select_and_load_character()
            
            if game_state:
                # Resume from saved game state
                print("\n✓ Resuming game from saved state...")
                # Re-attach AI service if available for continued world expansion
                game_state.ai_service = ai_service
                
                # Display welcome message
                print("\n" + "=" * 50)
                print(f"Welcome back, {game_state.current_character.name}!")
                print("=" * 50)
                print("\n" + get_command_reference())
                print("=" * 50)

                # Show current location
                print("\n" + game_state.look())
                
                # Run game loop with restored state
                run_game_loop(game_state)
                
            elif character:
                # For backward compatibility, if loading an old character-only save,
                # start a new game with that character
                print("\n✓ Starting new adventure with loaded character...")
                start_game(
                    character, ai_service=ai_service, theme="fantasy", strict=strict_mode, use_wfc=use_wfc
                )
                
        elif choice == "3":
            print("\nThank you for playing CLI RPG!")
            print("Goodbye!")
            break
        else:
            print("\n✗ Invalid choice. Please enter 1, 2, or 3.")
    
    return 0


if __name__ == "__main__":
    exit(main())
