"""Faction reputation effects on shop prices.

The Merchant Guild faction affects all shop transactions:
- HOSTILE (1-19): Trade refused entirely
- UNFRIENDLY (20-39): +15% buy price, -15% sell price
- NEUTRAL (40-59): No modifier
- FRIENDLY (60-79): -10% buy price, +10% sell price
- HONORED (80-100): -20% buy price, +20% sell price
"""
from typing import Optional

from cli_rpg.models.faction import Faction, ReputationLevel

# Price modifiers by reputation level (buy_modifier, sell_modifier)
# Buy: <1.0 is discount, >1.0 is premium
# Sell: <1.0 is penalty, >1.0 is bonus
FACTION_PRICE_MODIFIERS: dict[ReputationLevel, tuple[Optional[float], Optional[float]]] = {
    ReputationLevel.HOSTILE: (None, None),  # Trade refused
    ReputationLevel.UNFRIENDLY: (1.15, 0.85),
    ReputationLevel.NEUTRAL: (1.0, 1.0),
    ReputationLevel.FRIENDLY: (0.90, 1.10),
    ReputationLevel.HONORED: (0.80, 1.20),
}

# Messages for shop display by reputation level
FACTION_PRICE_MESSAGES: dict[ReputationLevel, str] = {
    ReputationLevel.HOSTILE: "The merchants eye you with hostility and refuse to serve you.",
    ReputationLevel.UNFRIENDLY: "(Prices are 15% higher due to your poor reputation)",
    ReputationLevel.NEUTRAL: "",
    ReputationLevel.FRIENDLY: "(You receive a 10% discount for your good standing)",
    ReputationLevel.HONORED: "(You receive a 20% discount as an honored customer)",
}


def get_merchant_guild_faction(factions: list[Faction]) -> Optional[Faction]:
    """Find the Merchant Guild faction in the faction list.

    Args:
        factions: List of player's faction reputations

    Returns:
        The Merchant Guild faction if found, None otherwise
    """
    for faction in factions:
        if faction.name == "Merchant Guild":
            return faction
    return None


def get_faction_price_modifiers(
    factions: list[Faction],
) -> tuple[Optional[float], Optional[float], bool]:
    """Get buy/sell price modifiers based on Merchant Guild reputation.

    Args:
        factions: List of player's faction reputations

    Returns:
        Tuple of (buy_modifier, sell_modifier, trade_refused) where:
        - buy_modifier: Multiplier for buy prices (None if refused)
        - sell_modifier: Multiplier for sell prices (None if refused)
        - trade_refused: True if HOSTILE reputation blocks trading
    """
    merchant_guild = get_merchant_guild_faction(factions)

    if merchant_guild is None:
        # No Merchant Guild faction - treat as neutral
        return (1.0, 1.0, False)

    level = merchant_guild.get_reputation_level()
    buy_mod, sell_mod = FACTION_PRICE_MODIFIERS[level]

    if level == ReputationLevel.HOSTILE:
        return (None, None, True)

    return (buy_mod, sell_mod, False)


def get_faction_price_message(level: ReputationLevel) -> str:
    """Get a message describing the price effect for a reputation level.

    Args:
        level: The reputation level

    Returns:
        Message string for display, empty string for NEUTRAL
    """
    return FACTION_PRICE_MESSAGES.get(level, "")
