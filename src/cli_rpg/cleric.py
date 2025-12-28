"""Cleric class abilities: bless party buff and smite undead."""

# Bless constants
BLESS_MANA_COST = 20
BLESS_DURATION = 3
BLESS_ATTACK_MODIFIER = 0.25  # +25% attack damage

# Smite constants
SMITE_MANA_COST = 15
SMITE_DAMAGE_MULTIPLIER = 2.5  # INT * 2.5 base damage
SMITE_UNDEAD_MULTIPLIER = 5.0  # INT * 5.0 vs undead (double damage)
SMITE_UNDEAD_STUN_CHANCE = 0.30  # 30% chance to stun undead

# Divine power bonus constants (from equipped holy symbol)
DIVINE_POWER_BLESS_BONUS = 0.01  # +1% attack modifier per divine power point
DIVINE_POWER_SMITE_BONUS = 1  # +1 damage per divine power point
DIVINE_POWER_STUN_BONUS = 0.01  # +1% stun chance per divine power point

# Undead type detection terms
UNDEAD_TERMS = {
    "skeleton",
    "zombie",
    "ghost",
    "wraith",
    "undead",
    "specter",
    "lich",
    "vampire",
}


def is_undead(enemy_name: str) -> bool:
    """Check if enemy name indicates an undead creature.

    Args:
        enemy_name: The name of the enemy to check

    Returns:
        True if the enemy name contains an undead term, False otherwise
    """
    name_lower = enemy_name.lower()
    return any(term in name_lower for term in UNDEAD_TERMS)
