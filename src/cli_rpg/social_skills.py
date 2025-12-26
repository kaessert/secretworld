"""Social skills module for Charisma-based interactions.

Provides CHA-based price modifiers and social skill commands:
- Persuade: Charm NPCs for discounts
- Intimidate: Threaten NPCs (works on weak-willed, backfires on strong)
- Bribe: Pay gold for guaranteed social success

Spec: thoughts/current_plan.md
"""
import random
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from cli_rpg.models.character import Character
    from cli_rpg.models.npc import NPC


def get_cha_price_modifier(charisma: int) -> float:
    """Calculate buy price modifier based on CHA.

    Higher CHA means lower buy prices (good for buying).
    Formula: ±1% per CHA point from baseline 10.

    Args:
        charisma: Character's charisma stat

    Returns:
        Price multiplier (e.g., 0.95 for CHA 15 = 5% discount)
    """
    # CHA 10 = baseline (1.0)
    # CHA 15 = -5% = 0.95
    # CHA 5 = +5% = 1.05
    return 1.0 - (charisma - 10) * 0.01


def get_cha_sell_modifier(charisma: int) -> float:
    """Calculate sell price modifier based on CHA.

    Higher CHA means higher sell prices (good for selling).
    Formula: ±1% per CHA point from baseline 10 (inverse of buy).

    Args:
        charisma: Character's charisma stat

    Returns:
        Price multiplier (e.g., 1.05 for CHA 15 = 5% bonus)
    """
    # CHA 10 = baseline (1.0)
    # CHA 15 = +5% = 1.05
    # CHA 5 = -5% = 0.95
    return 1.0 + (charisma - 10) * 0.01


def calculate_persuade_chance(charisma: int) -> int:
    """Calculate persuade success chance.

    Formula: 30% base + (CHA × 3%), max 90%.

    Args:
        charisma: Character's charisma stat

    Returns:
        Success chance as percentage (0-90)
    """
    chance = 30 + charisma * 3
    return min(chance, 90)


def calculate_intimidate_chance(charisma: int, kill_count: int) -> int:
    """Calculate intimidate success chance.

    Formula: 20% base + (CHA × 2%) + (kills × 5%), max 85%.

    Args:
        charisma: Character's charisma stat
        kill_count: Number of enemies player has killed

    Returns:
        Success chance as percentage (0-85)
    """
    chance = 20 + charisma * 2 + kill_count * 5
    return min(chance, 85)


def calculate_bribe_threshold(charisma: int) -> int:
    """Calculate minimum gold needed for a successful bribe.

    Formula: 50 - (CHA × 2), minimum 10 gold.

    Args:
        charisma: Character's charisma stat

    Returns:
        Minimum gold amount needed for bribe success
    """
    threshold = 50 - charisma * 2
    return max(threshold, 10)


def attempt_persuade(
    character: "Character", npc: Optional["NPC"]
) -> Tuple[bool, str]:
    """Attempt to persuade an NPC for benefits (e.g., discounts).

    Args:
        character: The player character
        npc: The NPC being persuaded (None if not in conversation)

    Returns:
        Tuple of (success, message)
    """
    if npc is None:
        return (False, "You're not talking to anyone. Use 'talk <npc>' first.")

    if npc.persuaded:
        return (False, f"You've already persuaded {npc.name}.")

    chance = calculate_persuade_chance(character.charisma)
    roll = random.randint(1, 100)

    if roll <= chance:
        npc.persuaded = True
        return (
            True,
            f"Your silver tongue works its magic! {npc.name} is charmed and "
            f"offers you a 20% discount on purchases.",
        )
    else:
        return (
            False,
            f"{npc.name} is not convinced by your words. Perhaps try a different approach.",
        )


def attempt_intimidate(
    character: "Character", npc: Optional["NPC"], kill_count: int = 0
) -> Tuple[bool, str]:
    """Attempt to intimidate an NPC.

    Works better on weak-willed NPCs. May backfire on strong-willed ones.

    Args:
        character: The player character
        npc: The NPC being intimidated (None if not in conversation)
        kill_count: Number of enemies the player has killed

    Returns:
        Tuple of (success, message)
    """
    if npc is None:
        return (False, "You're not talking to anyone. Use 'talk <npc>' first.")

    chance = calculate_intimidate_chance(character.charisma, kill_count)

    # Modify chance based on NPC willpower (high willpower = harder to intimidate)
    willpower_modifier = (npc.willpower - 5) * 5  # ±25% at extremes
    adjusted_chance = max(0, min(100, chance - willpower_modifier))

    roll = random.randint(1, 100)

    if roll <= adjusted_chance:
        # Success!
        if npc.willpower <= 3:
            return (
                True,
                f"{npc.name} cowers before your menacing presence. "
                f"\"P-please, take whatever you want! Just don't hurt me!\"",
            )
        else:
            return (
                True,
                f"You successfully intimidate {npc.name}. "
                f"They reluctantly agree to your demands.",
            )
    else:
        # Failure - stronger NPCs respond more harshly
        if npc.willpower >= 7:
            return (
                False,
                f"{npc.name} is not impressed by your threats and looks at you with anger. "
                f"\"You dare threaten me? Leave before I call the guards!\"",
            )
        else:
            return (
                False,
                f"{npc.name} seems unaffected by your intimidation attempt. "
                f"\"Nice try, but I've seen scarier things than you.\"",
            )


def attempt_bribe(
    character: "Character", npc: Optional["NPC"], amount: Optional[int]
) -> Tuple[bool, str]:
    """Attempt to bribe an NPC with gold.

    Success is guaranteed if amount meets the threshold (based on CHA).

    Args:
        character: The player character
        npc: The NPC being bribed (None if not in conversation)
        amount: Gold amount to offer (None if not specified)

    Returns:
        Tuple of (success, message)
    """
    if npc is None:
        return (False, "You're not talking to anyone. Use 'talk <npc>' first.")

    if amount is None:
        return (False, "How much gold do you want to offer? Usage: bribe <amount>")

    if not npc.bribeable:
        return (
            False,
            f"{npc.name} refuses your gold with disgust. \"I cannot be bought!\"",
        )

    if character.gold < amount:
        return (
            False,
            f"You don't have enough gold. You have {character.gold} gold but offered {amount}.",
        )

    threshold = calculate_bribe_threshold(character.charisma)

    if amount >= threshold:
        character.remove_gold(amount)
        npc.persuaded = True  # Bribe grants same effect as persuade
        return (
            True,
            f"You slip {amount} gold to {npc.name}. They pocket it discreetly "
            f"and give you a knowing nod. \"I believe we can come to an arrangement...\"",
        )
    else:
        # Not enough gold offered - don't take the gold
        return (
            False,
            f"{npc.name} looks at your meager offering and scoffs. "
            f"\"You'll need to do better than that.\" (Try at least {threshold} gold)",
        )
