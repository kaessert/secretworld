"""NPC arc effects on shop prices.

NPCs with arc relationships offer better or worse prices based on their arc stage with the player:
- ENEMY: Trade refused entirely
- HOSTILE: +20% buy price, -20% sell price
- WARY: +10% buy price, -10% sell price
- STRANGER: No modifier (default)
- ACQUAINTANCE: -5% buy price, +5% sell price
- TRUSTED: -10% buy price, +10% sell price
- DEVOTED: -15% buy price, +15% sell price

These modifiers stack with other price modifiers (CHA, faction, economy, persuade, haggle).
"""
from typing import Optional, Tuple

from cli_rpg.models.npc_arc import NPCArc, NPCArcStage

# Price modifiers by arc stage (buy_modifier, sell_modifier)
# Buy: <1.0 is discount, >1.0 is premium
# Sell: <1.0 is penalty, >1.0 is bonus
ARC_PRICE_MODIFIERS: dict[NPCArcStage, Tuple[Optional[float], Optional[float]]] = {
    NPCArcStage.ENEMY: (None, None),  # Trade refused
    NPCArcStage.HOSTILE: (1.20, 0.80),
    NPCArcStage.WARY: (1.10, 0.90),
    NPCArcStage.STRANGER: (1.0, 1.0),
    NPCArcStage.ACQUAINTANCE: (0.95, 1.05),
    NPCArcStage.TRUSTED: (0.90, 1.10),
    NPCArcStage.DEVOTED: (0.85, 1.15),
}

# Messages for shop display by arc stage
ARC_PRICE_MESSAGES: dict[NPCArcStage, str] = {
    NPCArcStage.ENEMY: "This merchant refuses to deal with you.",
    NPCArcStage.HOSTILE: "(Prices are 20% worse due to the merchant's hostility)",
    NPCArcStage.WARY: "(Prices are 10% worse - the merchant is wary of you)",
    NPCArcStage.STRANGER: "",
    NPCArcStage.ACQUAINTANCE: "(5% better prices - the merchant recognizes you)",
    NPCArcStage.TRUSTED: "(10% better prices - the merchant trusts you)",
    NPCArcStage.DEVOTED: "(15% best prices - your bond with this merchant is strong)",
}


def get_arc_price_modifiers(
    arc: Optional[NPCArc],
) -> Tuple[Optional[float], Optional[float], bool]:
    """Get buy/sell price modifiers based on NPC arc stage.

    Args:
        arc: The NPC's arc with the player, or None

    Returns:
        Tuple of (buy_modifier, sell_modifier, trade_refused) where:
        - buy_modifier: Multiplier for buy prices (None if refused)
        - sell_modifier: Multiplier for sell prices (None if refused)
        - trade_refused: True if ENEMY stage blocks trading
    """
    if arc is None:
        return (1.0, 1.0, False)

    stage = arc.get_stage()
    buy_mod, sell_mod = ARC_PRICE_MODIFIERS[stage]

    if stage == NPCArcStage.ENEMY:
        return (None, None, True)

    return (buy_mod, sell_mod, False)


def get_arc_price_message(stage: NPCArcStage) -> str:
    """Get a message describing the price effect for an arc stage.

    Args:
        stage: The NPC arc stage

    Returns:
        Message string for display, empty string for STRANGER
    """
    return ARC_PRICE_MESSAGES.get(stage, "")
