"""Main entry point for CLI RPG."""
import sys
from typing import Optional
from cli_rpg.character_creation import create_character, get_theme_selection
from cli_rpg.models.character import Character
from cli_rpg.models.item import Item, ItemType
from cli_rpg.persistence import save_character, load_character, list_saves, save_game_state, load_game_state, detect_save_type
from cli_rpg.game_state import GameState, parse_command
from cli_rpg.world import create_world
from cli_rpg.config import load_ai_config, is_ai_strict_mode
from cli_rpg.ai_service import AIService
from cli_rpg.autosave import autosave
from cli_rpg.map_renderer import render_map


def get_command_reference() -> str:
    """Return the full command reference string.

    Returns:
        Formatted string containing all available commands.
    """
    lines = [
        "Exploration Commands:",
        "  look (l)           - Look around at your surroundings",
        "  go (g) <direction> - Move in a direction (north, south, east, west)",
        "  status (s)         - View your character status",
        "  inventory (i)      - View your inventory and equipped items",
        "  equip (e) <item>   - Equip a weapon or armor from inventory",
        "  unequip <slot>     - Unequip weapon or armor (slot: weapon/armor)",
        "  use (u) <item>     - Use a consumable item",
        "  drop (dr) <item>   - Drop an item from your inventory",
        "  talk (t) <npc>     - Talk to an NPC (then chat freely, 'bye' to leave)",
        "  accept <quest>     - Accept a quest from the current NPC",
        "  complete <quest>   - Turn in a completed quest to the current NPC",
        "  abandon <quest>    - Abandon an active quest from your journal",
        "  shop               - View shop inventory (when at a shop)",
        "  buy <item>         - Buy an item from the shop",
        "  sell <item>        - Sell an item to the shop",
        "  map (m)            - Display a map of explored areas",
        "  lore               - Discover lore about your current location",
        "  rest (r)           - Rest to recover health (25% of max HP)",
        "  quests (q)         - View your quest journal",
        "  quest <name>       - View details of a specific quest",
        "  help (h)           - Display this command reference",
        "  save               - Save your game (not available during combat)",
        "  quit               - Return to main menu",
        "",
        "Combat Commands:",
        "  attack (a)    - Attack the enemy",
        "  defend (d)    - Take a defensive stance",
        "  cast (c)      - Cast a magic attack (intelligence-based)",
        "  flee (f)      - Attempt to flee from combat",
        "  use (u) <item> - Use a consumable item",
        "  status (s)    - View combat status",
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
    saves = list_saves()
    
    if not saves:
        print("\n⚠ No saved characters found.")
        print("  Create a new character first!")
        return (None, None)
    
    print("\n" + "=" * 50)
    print("LOAD CHARACTER")
    print("=" * 50)
    print("\nAvailable saved characters:")
    
    for idx, save in enumerate(saves, start=1):
        print(f"{idx}. {save['name']} (saved: {save['timestamp']})")
    
    print(f"{len(saves) + 1}. Cancel")
    print("=" * 50)
    
    try:
        choice = input("Select character to load: ").strip()
        choice_num = int(choice)
        
        if choice_num == len(saves) + 1:
            print("\nLoad cancelled.")
            return (None, None)
        
        if 1 <= choice_num <= len(saves):
            selected_save = saves[choice_num - 1]
            
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


def handle_conversation_input(game_state: GameState, user_input: str) -> tuple[bool, str]:
    """Handle player input during conversation mode.

    Args:
        game_state: Current game state (must have current_npc set)
        user_input: The player's input text

    Returns:
        Tuple of (continue_game, message)
    """
    npc = game_state.current_npc

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


def handle_combat_command(game_state: GameState, command: str, args: list[str]) -> tuple[bool, str]:
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
    
    if command == "attack":
        victory, message = combat.player_attack()
        output = f"\n{message}"

        if victory:
            # Enemy defeated
            enemy_name = combat.enemy.name
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives
            quest_messages = game_state.current_character.record_kill(enemy_name)
            for msg in quest_messages:
                output += f"\n{msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
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
            game_state.current_combat = None

        return (True, output)
    
    elif command == "flee":
        success, message = combat.player_flee()
        output = f"\n{message}"

        if success:
            # Fled successfully
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
                game_state.current_combat = None

        return (True, output)

    elif command == "cast":
        victory, message = combat.player_cast()
        output = f"\n{message}"

        if victory:
            # Enemy defeated
            enemy_name = combat.enemy.name
            end_message = combat.end_combat(victory=True)
            output += f"\n{end_message}"
            # Track quest progress for kill objectives
            quest_messages = game_state.current_character.record_kill(enemy_name)
            for msg in quest_messages:
                output += f"\n{msg}"
            game_state.current_combat = None
            # Autosave after combat victory
            try:
                autosave(game_state)
            except IOError:
                pass  # Silent failure
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

        return (True, output)

    elif command == "status":
        return (True, "\n" + combat.get_status())

    elif command == "use":
        if not args:
            return (True, "\nUse what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
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
                game_state.current_combat = None

        return (True, output)

    elif command == "help":
        return (True, "\n" + get_command_reference())

    elif command == "quit":
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

    else:
        return (True, "\n✗ Can't do that during combat! Use: attack, defend, cast, flee, use, status, help, or quit")


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
            return (True, "\nGo where? Specify a direction (north, south, east, west)")
        
        direction = args[0]
        success, message = game_state.move(direction)
        output = f"\n{message}"
        
        if success:
            # Show new location
            output += "\n\n" + game_state.look()
        
        return (True, output)
    
    elif command == "status":
        return (True, "\n" + str(game_state.current_character))

    elif command == "inventory":
        return (True, "\n" + str(game_state.current_character.inventory))

    elif command == "equip":
        if not args:
            return (True, "\nEquip what? Specify an item name.")
        item_name = " ".join(args)
        item = game_state.current_character.inventory.find_item_by_name(item_name)
        if item is None:
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
            return (True, f"\nYou don't have '{item_name}' in your inventory.")
        success, message = game_state.current_character.use_item(item)
        return (True, f"\n{message}")

    elif command == "talk":
        if not args:
            location = game_state.world.get(game_state.current_location)
            if location is None or not location.npcs:
                return (True, "\nThere are no NPCs here to talk to.")
            return (True, "\nTalk to whom? Specify an NPC name.")
        npc_name = " ".join(args)
        location = game_state.world.get(game_state.current_location)
        npc = location.find_npc_by_name(npc_name) if location else None
        if npc is None:
            return (True, f"\nYou don't see '{npc_name}' here.")

        # Store current NPC for accept command context
        game_state.current_npc = npc

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

        output = f"\n{npc.name}: \"{npc.get_greeting()}\""

        # Record talk for TALK quest progress tracking
        talk_messages = game_state.current_character.record_talk(npc.name)
        if talk_messages:
            output += "\n\n" + "\n".join(talk_messages)

        if npc.is_merchant and npc.shop:
            game_state.current_shop = npc.shop
            output += "\n\nType 'shop' to see items, 'buy <item>' to purchase, 'sell <item>' to sell."

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
                    quest_data = game_state.ai_service.generate_quest(
                        theme=game_state.theme,
                        npc_name=npc.name,
                        player_level=game_state.current_character.level,
                        location_name=game_state.current_location
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
                    output += f"\n  - {q.name}"
                output += "\n\nType 'accept <quest>' to accept a quest."

        # Add conversation prompt
        output += "\n\n(Continue chatting or type 'bye' to leave)"

        return (True, output)

    elif command == "shop":
        if game_state.current_shop is None:
            return (True, "\nYou're not at a shop. Talk to a merchant first.")
        shop = game_state.current_shop
        lines = [f"\n=== {shop.name} ===", f"Your gold: {game_state.current_character.gold}", ""]
        for si in shop.inventory:
            lines.append(f"  {si.item.name} - {si.buy_price} gold")
        return (True, "\n".join(lines))

    elif command == "buy":
        if game_state.current_shop is None:
            return (True, "\nYou're not at a shop. Talk to a merchant first.")
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
                available = ", ".join(f"'{si.item.name}'" for si in game_state.current_shop.inventory)
                return (True, f"\nThe shop doesn't have '{item_name}'. Available: {available}")
        if game_state.current_character.gold < shop_item.buy_price:
            return (True, f"\nYou can't afford {shop_item.item.name} ({shop_item.buy_price} gold). You have {game_state.current_character.gold} gold.")
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
        game_state.current_character.remove_gold(shop_item.buy_price)
        game_state.current_character.inventory.add_item(new_item)
        # Track quest progress for collect objectives
        quest_messages = game_state.current_character.record_collection(new_item.name)
        autosave(game_state)
        output = f"\nYou bought {new_item.name} for {shop_item.buy_price} gold."
        if quest_messages:
            output += "\n" + "\n".join(quest_messages)
        return (True, output)

    elif command == "sell":
        if game_state.current_shop is None:
            return (True, "\nYou're not at a shop. Talk to a merchant first.")
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
        # Base sell price calculation
        sell_price = 10 + (item.damage_bonus + item.defense_bonus + item.heal_amount) * 2
        game_state.current_character.inventory.remove_item(item)
        game_state.current_character.add_gold(sell_price)
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

    elif command == "accept":
        # Accept a quest from the current NPC
        if game_state.current_npc is None:
            return (True, "\nYou need to talk to an NPC first.")
        if not args:
            return (True, "\nAccept what? Specify a quest name.")

        from cli_rpg.models.quest import Quest, QuestStatus

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
        reward_messages = game_state.current_character.claim_quest_rewards(matching_quest)
        matching_quest.status = QuestStatus.COMPLETED
        autosave(game_state)

        output_lines = [f"\nQuest completed: {matching_quest.name}!"]
        output_lines.extend(reward_messages)
        return (True, "\n".join(output_lines))

    elif command == "abandon":
        # Abandon an active quest
        if not args:
            return (True, "\nAbandon which quest? Specify a quest name (e.g., 'abandon goblin slayer').")

        quest_name = " ".join(args)
        success, message = game_state.current_character.abandon_quest(quest_name)
        return (True, f"\n{message}")

    elif command == "map":
        map_output = render_map(game_state.world, game_state.current_location)
        return (True, f"\n{map_output}")

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
            for quest in active_quests:
                lines.append(f"  • {quest.name} [{quest.current_count}/{quest.target_count}]")

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
        lines.extend([
            "",
            f"{quest.description}",
            "",
            f"Objective: {quest.objective_type.value.capitalize()} {quest.target}",
            f"Progress: {quest.current_count}/{quest.target_count}",
        ])
        return (True, "\n".join(lines))

    elif command == "help":
        return (True, "\n" + get_command_reference())

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
        # Check if already at full health
        char = game_state.current_character
        if char.health >= char.max_health:
            return (True, "\nYou're already at full health!")

        # Calculate heal amount: 25% of max HP, minimum 1
        heal_amount = max(1, char.max_health // 4)

        # Cap healing at what's actually needed
        actual_heal = min(heal_amount, char.max_health - char.health)

        # Apply healing
        char.heal(actual_heal)

        return (True, f"\nYou rest and recover {actual_heal} health.")

    elif command in ["attack", "defend", "flee", "rest"]:
        return (True, "\n✗ Not in combat.")
    
    elif command == "unknown":
        return (True, "\n✗ Unknown command. Type 'help' for a list of commands.")

    else:
        return (True, "\n✗ Unknown command. Type 'help' for a list of commands.")


def run_game_loop(game_state: GameState) -> None:
    """Run the main gameplay loop.

    Args:
        game_state: The game state to run the loop for
    """
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
        if game_state.is_in_conversation:
            print(f"\n[Talking to {game_state.current_npc.name}]")

        print()
        command_input = input("> ").strip()

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


def start_game(
    character: Character,
    ai_service: Optional[AIService] = None,
    theme: str = "fantasy",
    strict: bool = True
) -> None:
    """Start the gameplay loop with the given character.

    Args:
        character: The player's character to start the game with
        ai_service: Optional AIService for AI-powered world generation
        theme: World theme for generation (default: "fantasy")
        strict: If True (default), AI generation failures raise exceptions.
                If False, falls back to default world on AI error.
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
                    character, ai_service=ai_service, theme=theme, strict=strict
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
    
    game_state = GameState(
        character, 
        world, 
        starting_location=starting_location,
        ai_service=ai_service, 
        theme=theme
    )
    
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


def main() -> int:
    """Main function to start the CLI RPG game.
    
    Returns:
        Exit code (0 for success)
    """
    print("\n" + "=" * 50)
    print("Welcome to CLI RPG!")
    print("=" * 50)
    
    # Load AI configuration at startup
    ai_config = load_ai_config()
    ai_service = None
    strict_mode = is_ai_strict_mode()

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
                    character, ai_service=ai_service, theme=theme, strict=strict_mode
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
                    character, ai_service=ai_service, theme="fantasy", strict=strict_mode
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
