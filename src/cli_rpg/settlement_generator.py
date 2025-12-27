"""Settlement generator for partitioning large settlements into districts.

This module provides functions to generate themed districts within mega-settlements
(cities, metropolises, capitals). Districts are created using a quadrant-based
partitioning approach that divides the settlement bounds into distinct areas.
"""

from random import Random
from typing import List, Optional

from cli_rpg.models.district import District, DistrictType


# Settlement categories that receive district partitioning
MEGA_SETTLEMENT_CATEGORIES = frozenset({"city", "metropolis", "capital"})

# Minimum width/height to qualify for district generation
MEGA_SETTLEMENT_THRESHOLD = 17


# Default configurations for each district type
DISTRICT_CONFIGS = {
    DistrictType.MARKET: {
        "name_templates": ["The Grand Market", "{city} Market", "Market District", "Bazaar Quarter"],
        "atmospheres": ["bustling", "chaotic", "lively", "crowded"],
        "prosperity_weights": {"modest": 0.3, "prosperous": 0.5, "wealthy": 0.2},
        "features": ["Central Fountain", "Merchant Stalls", "Trade Hall", "Money Changers"],
    },
    DistrictType.TEMPLE: {
        "name_templates": ["Temple Quarter", "Sacred Grounds", "The Sanctum", "Holy District"],
        "atmospheres": ["serene", "reverent", "peaceful", "solemn"],
        "prosperity_weights": {"modest": 0.2, "prosperous": 0.3, "wealthy": 0.5},
        "features": ["Grand Cathedral", "Temple Gardens", "Shrine Row", "Pilgrim's Rest"],
    },
    DistrictType.RESIDENTIAL: {
        "name_templates": ["Hearthstone Ward", "Citizen's Quarter", "The Commons", "Homstead District"],
        "atmospheres": ["quiet", "homely", "peaceful", "neighborly"],
        "prosperity_weights": {"poor": 0.1, "modest": 0.6, "prosperous": 0.3},
        "features": ["Community Well", "Village Green", "Local Tavern", "Neighborhood Shrine"],
    },
    DistrictType.NOBLE: {
        "name_templates": ["Noble Quarter", "Highborn Heights", "The Estates", "Aristocrat's Row"],
        "atmospheres": ["refined", "elegant", "exclusive", "proud"],
        "prosperity_weights": {"prosperous": 0.2, "wealthy": 0.8},
        "features": ["Lord's Manor", "Sculpted Gardens", "Private Chapel", "Gated Grounds"],
    },
    DistrictType.SLUMS: {
        "name_templates": ["The Warrens", "Lowtown", "Beggar's Quarter", "The Dregs"],
        "atmospheres": ["desperate", "dangerous", "grim", "shadowy"],
        "prosperity_weights": {"poor": 0.9, "modest": 0.1},
        "features": ["Thieves' Den", "Broken Fountain", "Abandoned Mill", "Dark Alleys"],
    },
    DistrictType.CRAFTSMEN: {
        "name_templates": ["Artisan Quarter", "Crafters' Row", "Guildhall District", "The Forges"],
        "atmospheres": ["industrious", "smoky", "busy", "productive"],
        "prosperity_weights": {"modest": 0.4, "prosperous": 0.5, "wealthy": 0.1},
        "features": ["Smithy Row", "Weavers' Guild", "Carpenter's Square", "Tannery Lane"],
    },
    DistrictType.DOCKS: {
        "name_templates": ["The Docks", "Harbor Quarter", "Waterfront", "Sailor's Rest"],
        "atmospheres": ["salty", "bustling", "rough", "lively"],
        "prosperity_weights": {"poor": 0.2, "modest": 0.5, "prosperous": 0.3},
        "features": ["Warehouse Row", "Fishmonger's Wharf", "Sailor's Tavern", "Chandlery"],
    },
    DistrictType.ENTERTAINMENT: {
        "name_templates": ["Pleasure District", "The Revelry", "Festival Quarter", "Merrymaker's Row"],
        "atmospheres": ["festive", "raucous", "colorful", "lively"],
        "prosperity_weights": {"modest": 0.3, "prosperous": 0.5, "wealthy": 0.2},
        "features": ["Grand Theater", "Gambling Hall", "Music Halls", "Dancing Pavilion"],
    },
    DistrictType.MILITARY: {
        "name_templates": ["Garrison District", "The Barracks", "Soldier's Quarter", "Fortress Ward"],
        "atmospheres": ["disciplined", "orderly", "austere", "vigilant"],
        "prosperity_weights": {"modest": 0.4, "prosperous": 0.6},
        "features": ["Training Grounds", "Armory", "Guard Towers", "War Memorial"],
    },
}


def _pick_weighted(choices: dict, rng: Random) -> str:
    """Pick an item based on weighted probabilities.

    Args:
        choices: Dict mapping items to their probability weights
        rng: Random instance for determinism

    Returns:
        Selected item
    """
    items = list(choices.keys())
    weights = list(choices.values())
    total = sum(weights)
    r = rng.random() * total
    cumulative = 0
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1]


def _generate_district(
    district_type: DistrictType,
    bounds: tuple[int, int, int, int],
    settlement_name: str,
    rng: Random,
) -> District:
    """Generate a single district with random attributes.

    Args:
        district_type: Type of district to generate
        bounds: (min_x, max_x, min_y, max_y) bounds for this district
        settlement_name: Name of parent settlement for name templates
        rng: Random instance for determinism

    Returns:
        Generated District instance
    """
    config = DISTRICT_CONFIGS[district_type]

    # Pick random name template and fill in city name
    name_template = rng.choice(config["name_templates"])
    name = name_template.replace("{city}", settlement_name)

    # Pick random atmosphere
    atmosphere = rng.choice(config["atmospheres"])

    # Pick weighted prosperity level
    prosperity = _pick_weighted(config["prosperity_weights"], rng)

    # Pick 1-2 random notable features
    num_features = rng.randint(1, 2)
    features = rng.sample(config["features"], min(num_features, len(config["features"])))

    # Generate thematic description
    descriptions = {
        DistrictType.MARKET: f"The commercial heart of {settlement_name}, where merchants hawk their wares.",
        DistrictType.TEMPLE: f"Sacred grounds where the faithful gather to honor the gods.",
        DistrictType.RESIDENTIAL: f"Where the common folk of {settlement_name} make their homes.",
        DistrictType.NOBLE: f"The exclusive domain of {settlement_name}'s aristocracy.",
        DistrictType.SLUMS: f"A desperate corner of {settlement_name} where the poor struggle to survive.",
        DistrictType.CRAFTSMEN: f"The industrious heart of {settlement_name}, filled with workshops and forges.",
        DistrictType.DOCKS: f"The waterfront district, smelling of salt and fish.",
        DistrictType.ENTERTAINMENT: f"Where the people of {settlement_name} come to forget their troubles.",
        DistrictType.MILITARY: f"The disciplined quarter where {settlement_name}'s defenders are trained.",
    }

    return District(
        name=name,
        district_type=district_type,
        description=descriptions[district_type],
        bounds=bounds,
        atmosphere=atmosphere,
        prosperity=prosperity,
        notable_features=features,
    )


def _compute_quadrant_bounds(
    settlement_bounds: tuple[int, int, int, int, int, int],
    num_districts: int,
) -> list[tuple[int, int, int, int]]:
    """Compute district bounds using quadrant-based partitioning.

    Divides the settlement into quadrants based on the number of districts:
    - 2 districts: East/West split
    - 3 districts: Three vertical strips
    - 4 districts: Four quadrants
    - 5+ districts: Grid-based approach

    Args:
        settlement_bounds: 6-tuple bounds of the settlement (min_x, max_x, min_y, max_y, min_z, max_z)
        num_districts: Number of districts to create

    Returns:
        List of 4-tuple bounds for each district
    """
    min_x, max_x, min_y, max_y, _, _ = settlement_bounds
    mid_x = (min_x + max_x) // 2
    mid_y = (min_y + max_y) // 2

    if num_districts == 2:
        # East/West split
        return [
            (min_x, mid_x, min_y, max_y),  # West
            (mid_x + 1, max_x, min_y, max_y),  # East
        ]
    elif num_districts == 3:
        # Three vertical strips
        third_x = (max_x - min_x) // 3
        return [
            (min_x, min_x + third_x, min_y, max_y),  # West
            (min_x + third_x + 1, max_x - third_x - 1, min_y, max_y),  # Center
            (max_x - third_x, max_x, min_y, max_y),  # East
        ]
    elif num_districts == 4:
        # Four quadrants
        return [
            (min_x, mid_x, mid_y + 1, max_y),  # NW
            (mid_x + 1, max_x, mid_y + 1, max_y),  # NE
            (min_x, mid_x, min_y, mid_y),  # SW
            (mid_x + 1, max_x, min_y, mid_y),  # SE
        ]
    else:
        # 5+ districts: 2x3 grid or 3x2 grid based on aspect ratio
        width = max_x - min_x + 1
        height = max_y - min_y + 1

        if width >= height:
            # 3 columns x 2 rows
            cols, rows = 3, 2
        else:
            # 2 columns x 3 rows
            cols, rows = 2, 3

        cell_w = (max_x - min_x + 1) // cols
        cell_h = (max_y - min_y + 1) // rows

        bounds_list = []
        for row in range(rows):
            for col in range(cols):
                if len(bounds_list) >= num_districts:
                    break
                cell_min_x = min_x + col * cell_w
                cell_max_x = min_x + (col + 1) * cell_w - 1 if col < cols - 1 else max_x
                cell_min_y = min_y + row * cell_h
                cell_max_y = min_y + (row + 1) * cell_h - 1 if row < rows - 1 else max_y
                bounds_list.append((cell_min_x, cell_max_x, cell_min_y, cell_max_y))

        return bounds_list[:num_districts]


def generate_districts(
    bounds: tuple[int, int, int, int, int, int],
    category: str,
    settlement_name: str,
    rng: Optional[Random] = None,
) -> List[District]:
    """Generate districts for a mega-settlement.

    Partitions the settlement bounds into themed districts appropriate
    for the settlement category. Larger settlements get more districts.

    Args:
        bounds: 6-tuple SubGrid bounds (min_x, max_x, min_y, max_y, min_z, max_z)
        category: Settlement category (city, metropolis, capital)
        settlement_name: Name of the settlement for district naming
        rng: Optional Random instance for determinism (creates one if None)

    Returns:
        List of generated District instances covering the settlement
    """
    if rng is None:
        rng = Random()

    # Determine number of districts based on category
    if category == "city":
        num_districts = rng.randint(2, 4)
    elif category == "metropolis":
        num_districts = rng.randint(4, 6)
    elif category == "capital":
        num_districts = rng.randint(5, 8)
    else:
        num_districts = rng.randint(2, 3)

    # Cap at number of district types available
    num_districts = min(num_districts, len(DistrictType))

    # Compute quadrant bounds for each district
    quadrant_bounds = _compute_quadrant_bounds(bounds, num_districts)

    # Select district types - prefer variety
    available_types = list(DistrictType)
    rng.shuffle(available_types)
    selected_types = available_types[:num_districts]

    # Generate districts
    districts = []
    for i, district_type in enumerate(selected_types):
        district = _generate_district(
            district_type=district_type,
            bounds=quadrant_bounds[i],
            settlement_name=settlement_name,
            rng=rng,
        )
        districts.append(district)

    return districts


def get_district_at_coords(
    districts: List[District],
    x: int,
    y: int,
) -> Optional[District]:
    """Find which district contains the given coordinates.

    Args:
        districts: List of districts to search
        x: X coordinate
        y: Y coordinate

    Returns:
        District containing the coordinates, or None if not found
    """
    for district in districts:
        if district.contains(x, y):
            return district
    return None
