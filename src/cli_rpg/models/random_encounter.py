"""Random encounter model for travel events."""
from dataclasses import dataclass
from typing import Union

from cli_rpg.models.enemy import Enemy
from cli_rpg.models.npc import NPC


@dataclass
class RandomEncounter:
    """Represents a random encounter triggered during travel.

    Attributes:
        encounter_type: Type of encounter ("hostile", "merchant", "wanderer")
        entity: The encounter entity (Enemy for hostile, NPC for merchant/wanderer)
        description: Flavor text describing the encounter
    """

    encounter_type: str
    entity: Union[Enemy, NPC]
    description: str

    def __post_init__(self):
        """Validate encounter attributes."""
        valid_types = {"hostile", "merchant", "wanderer"}
        if self.encounter_type not in valid_types:
            raise ValueError(
                f"encounter_type must be one of {valid_types}, got '{self.encounter_type}'"
            )
        if self.encounter_type == "hostile" and not isinstance(self.entity, Enemy):
            raise ValueError("hostile encounters must have an Enemy entity")
        if self.encounter_type in ("merchant", "wanderer") and not isinstance(self.entity, NPC):
            raise ValueError(f"{self.encounter_type} encounters must have an NPC entity")

    def to_dict(self) -> dict:
        """Serialize RandomEncounter to dictionary.

        Returns:
            Dictionary containing encounter data
        """
        entity_data = self.entity.to_dict()
        entity_type = "enemy" if isinstance(self.entity, Enemy) else "npc"

        return {
            "encounter_type": self.encounter_type,
            "entity_type": entity_type,
            "entity": entity_data,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RandomEncounter":
        """Deserialize RandomEncounter from dictionary.

        Args:
            data: Dictionary containing encounter data

        Returns:
            RandomEncounter instance
        """
        entity_type = data["entity_type"]
        if entity_type == "enemy":
            entity = Enemy.from_dict(data["entity"])
        else:
            entity = NPC.from_dict(data["entity"])

        return cls(
            encounter_type=data["encounter_type"],
            entity=entity,
            description=data["description"],
        )
