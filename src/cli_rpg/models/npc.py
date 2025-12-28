"""NPC model for non-hostile characters."""
import random
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from cli_rpg.models.npc_relationship import NPCRelationship, RelationshipType
from cli_rpg.models.npc_arc import NPCArc, NPCArcStage

if TYPE_CHECKING:
    from cli_rpg.models.shop import Shop
    from cli_rpg.models.quest import Quest
    from cli_rpg.models.quest_outcome import QuestOutcome


@dataclass
class NPC:
    """Represents a non-player character in the RPG.

    Attributes:
        name: NPC name (2-30 characters)
        description: What player sees (1-200 characters)
        dialogue: What NPC says when talked to
        is_merchant: Whether NPC runs a shop
        shop: Optional shop if NPC is a merchant
        is_quest_giver: Whether NPC offers quests
        offered_quests: List of quests this NPC offers
        conversation_history: List of conversation exchanges with player
        ascii_art: ASCII art representation of the NPC
        available_at_night: Whether NPC is available at night (default True)
        is_recruitable: Whether NPC can be recruited as a companion (default False)
        willpower: Willpower stat (1-10), affects intimidate resistance (default 5)
        bribeable: Whether NPC can be bribed (default True)
        persuaded: Whether NPC has been persuaded this session (default False)
    """

    name: str
    description: str
    dialogue: str
    is_merchant: bool = False
    shop: Optional["Shop"] = None
    is_quest_giver: bool = False
    offered_quests: List["Quest"] = field(default_factory=list)
    greetings: List[str] = field(default_factory=list)
    conversation_history: List[dict] = field(default_factory=list)
    ascii_art: str = ""  # ASCII art representation of the NPC
    available_at_night: bool = True  # Whether NPC is available at night
    is_recruitable: bool = False  # Whether NPC can be recruited as a companion
    willpower: int = 5  # Willpower 1-10, affects intimidate resistance
    bribeable: bool = True  # Whether NPC can be bribed
    persuaded: bool = False  # Whether NPC has been persuaded this session
    haggleable: bool = True  # Whether merchant allows haggling
    haggle_cooldown: int = 0  # Turns remaining before haggling allowed again
    faction: Optional[str] = None  # Faction affiliation (e.g., "Merchant Guild")
    required_reputation: Optional[int] = None  # Min faction rep to interact (1-100)
    relationships: List[NPCRelationship] = field(default_factory=list)  # Relationships to other NPCs
    arc: Optional[NPCArc] = None  # Character arc tracking (optional for backward compat)

    def __post_init__(self):
        """Validate NPC attributes."""
        if not 2 <= len(self.name) <= 30:
            raise ValueError("NPC name must be 2-30 characters")
        if not 1 <= len(self.description) <= 200:
            raise ValueError("Description must be 1-200 characters")

    def get_arc_greeting_modifier(self) -> Optional[str]:
        """Get greeting modifier based on arc stage.

        Returns:
            A warm greeting for high relationship stages (TRUSTED, DEVOTED, ACQUAINTANCE),
            or None for STRANGER and negative stages which use default greeting.
        """
        if self.arc is None:
            return None
        stage = self.arc.get_stage()
        if stage == NPCArcStage.DEVOTED:
            return "Ah, my dear friend! It's always a pleasure to see you."
        elif stage == NPCArcStage.TRUSTED:
            return "Good to see you again! What can I do for you today?"
        elif stage == NPCArcStage.ACQUAINTANCE:
            return "Oh, you again. What do you need?"
        # STRANGER and negative stages use default greeting
        return None

    def get_greeting(
        self,
        choices: Optional[List[dict]] = None,
        quest_outcomes: Optional[List["QuestOutcome"]] = None,
    ) -> str:
        """Get a greeting to display when talking to this NPC.

        Args:
            choices: Optional list of player choice dicts to check for reputation.
                     Each choice dict should have a "choice_type" key.
            quest_outcomes: Optional list of QuestOutcome objects relevant to this NPC.
                           Used to generate quest-aware greetings.

        Returns a greeting potentially modified by player reputation or quest outcomes,
        or a random greeting from the greetings list if available,
        otherwise falls back to the dialogue field.
        """
        # Check arc-based greeting first (warmest greetings for high relationship)
        arc_greeting = self.get_arc_greeting_modifier()
        if arc_greeting:
            return arc_greeting

        # Check for quest-based greetings (most recent outcomes take priority)
        if quest_outcomes:
            # Find the most recent outcome where this NPC was the quest giver
            quest_giver_outcomes = [
                o for o in quest_outcomes if o.quest_giver.lower() == self.name.lower()
            ]
            if quest_giver_outcomes:
                # Use most recent (last in list)
                latest_outcome = quest_giver_outcomes[-1]
                return self._get_quest_reaction_greeting(latest_outcome, is_quest_giver=True)

            # Check if NPC was affected by any quest outcome
            affected_outcomes = [
                o
                for o in quest_outcomes
                if self.name.lower() in [n.lower() for n in o.affected_npcs]
            ]
            if affected_outcomes:
                latest_outcome = affected_outcomes[-1]
                return self._get_quest_reaction_greeting(latest_outcome, is_quest_giver=False)

        # Check for reputation-based greetings
        if choices:
            flee_count = sum(1 for c in choices if c.get("choice_type") == "combat_flee")
            if flee_count >= 3:
                return self._get_reputation_greeting("cautious")

            # Check for aggressive reputation (10+ kills)
            kill_count = sum(1 for c in choices if c.get("choice_type") == "combat_kill")
            if kill_count >= 10:
                return self._get_reputation_greeting("aggressive")

        # Normal greeting logic
        if self.greetings:
            return random.choice(self.greetings)
        return self.dialogue

    def _get_quest_reaction_greeting(
        self, outcome: "QuestOutcome", is_quest_giver: bool
    ) -> str:
        """Get greeting based on quest outcome history.

        Args:
            outcome: The QuestOutcome to react to
            is_quest_giver: True if this NPC gave the quest, False if affected by it

        Returns:
            A quest-aware greeting string with the quest name substituted.
        """
        templates = {
            "quest_giver_success": [
                "Well done! I knew I could count on you to handle {quest_name}.",
                "You've proven yourself. {quest_name} is complete, thanks to you.",
                "Ah, the hero who completed {quest_name}! What brings you back?",
            ],
            "quest_giver_branch": [
                "I heard how you handled {quest_name}. Interesting approach...",
                "The job's done with {quest_name}, though some say your methods were... unconventional.",
                "You found your own way to complete {quest_name}. I can respect that.",
            ],
            "quest_giver_failed": [
                "You failed me with {quest_name}. I expected more from you.",
                "Time ran out on {quest_name}. Disappointing.",
                "I trusted you with {quest_name}... and you let me down.",
            ],
            "quest_giver_abandoned": [
                "You abandoned {quest_name}. I don't forget such things easily.",
                "Walking away from {quest_name}? I had higher hopes for you.",
                "I see you couldn't handle {quest_name}. Perhaps I misjudged you.",
            ],
            "affected_positive": [
                "I heard what you did. You have my gratitude.",
                "Word spreads fast. Thank you for your help with {quest_name}.",
                "You helped with {quest_name}. I won't forget that kindness.",
            ],
            "affected_negative": [
                "I know what you did with {quest_name}. Don't expect any favors from me.",
                "After what happened with {quest_name}? We have nothing to discuss.",
                "Your actions regarding {quest_name} have not gone unnoticed.",
            ],
        }

        # Determine template category
        if is_quest_giver:
            if outcome.completion_method == "main":
                category = "quest_giver_success"
            elif outcome.completion_method.startswith("branch_"):
                category = "quest_giver_branch"
            elif outcome.completion_method == "expired":
                category = "quest_giver_failed"
            elif outcome.completion_method == "abandoned":
                category = "quest_giver_abandoned"
            else:
                category = "quest_giver_success"  # Fallback
        else:
            # Affected NPC - determine positive or negative based on outcome
            if outcome.is_success:
                category = "affected_positive"
            else:
                category = "affected_negative"

        options = templates.get(category, [])
        if options:
            template = random.choice(options)
            return template.format(quest_name=outcome.quest_name)

        # Fallback to normal greeting
        return self.get_greeting(choices=None, quest_outcomes=None)

    def _get_reputation_greeting(self, reputation_type: str) -> str:
        """Get greeting based on player reputation.

        Args:
            reputation_type: The type of reputation (e.g., "cautious")

        Returns:
            A reputation-aware greeting string.
        """
        templates = {
            "cautious": [
                "Ah, I've heard of you... one who knows when to run. Smart.",
                "Word travels fast. They say you're... careful. I respect that.",
                "A survivor, they call you. Some might say coward, but you're alive.",
            ],
            "aggressive": [
                "I've heard tales of your... efficiency in combat. Many have fallen.",
                "The blood of your enemies precedes you. What brings such a warrior here?",
                "A killer walks among us. I hope we remain on friendly terms.",
            ],
        }
        options = templates.get(reputation_type, [])
        if options:
            return random.choice(options)
        return self.get_greeting(choices=None)  # Fallback to normal

    def add_conversation(self, role: str, content: str) -> None:
        """Add a conversation entry to the history.

        Maintains a maximum of 10 entries, removing oldest when exceeded.

        Args:
            role: The role of the speaker ("player" or "npc")
            content: The message content
        """
        self.conversation_history.append({"role": role, "content": content})
        # Cap at 10 entries
        while len(self.conversation_history) > 10:
            self.conversation_history.pop(0)

    def add_relationship(
        self,
        target: str,
        rel_type: RelationshipType,
        trust: int = 50,
        desc: Optional[str] = None,
    ) -> None:
        """Add a relationship to another NPC.

        Args:
            target: Name of the related NPC
            rel_type: Type of relationship
            trust: Trust level (1-100, default 50)
            desc: Optional description (e.g., "sister", "former master")
        """
        self.relationships.append(
            NPCRelationship(
                target_npc=target,
                relationship_type=rel_type,
                trust_level=trust,
                description=desc,
            )
        )

    def get_relationship(self, target: str) -> Optional[NPCRelationship]:
        """Get the relationship to a specific NPC by name.

        Args:
            target: Name of the NPC to find relationship with

        Returns:
            NPCRelationship if found, None otherwise
        """
        for rel in self.relationships:
            if rel.target_npc == target:
                return rel
        return None

    def get_relationships_by_type(
        self, rel_type: RelationshipType
    ) -> List[NPCRelationship]:
        """Get all relationships of a specific type.

        Args:
            rel_type: Type of relationship to filter by

        Returns:
            List of matching relationships
        """
        return [r for r in self.relationships if r.relationship_type == rel_type]

    def to_dict(self) -> dict:
        """Serialize NPC to dictionary.

        Returns:
            Dictionary containing all NPC attributes
        """
        result = {
            "name": self.name,
            "description": self.description,
            "dialogue": self.dialogue,
            "is_merchant": self.is_merchant,
            "shop": self.shop.to_dict() if self.shop else None,
            "is_quest_giver": self.is_quest_giver,
            "offered_quests": [q.to_dict() for q in self.offered_quests],
            "greetings": self.greetings,
            "conversation_history": self.conversation_history,
            "available_at_night": self.available_at_night,
            "is_recruitable": self.is_recruitable,
            "willpower": self.willpower,
            "bribeable": self.bribeable,
            "persuaded": self.persuaded,
            "haggleable": self.haggleable,
            "haggle_cooldown": self.haggle_cooldown,
            "faction": self.faction,
            "required_reputation": self.required_reputation,
            "relationships": [r.to_dict() for r in self.relationships],
            "arc": self.arc.to_dict() if self.arc else None,
        }
        # Only include ascii_art if it's not empty
        if self.ascii_art:
            result["ascii_art"] = self.ascii_art
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        """Deserialize NPC from dictionary.

        Args:
            data: Dictionary containing NPC attributes

        Returns:
            NPC instance
        """
        from cli_rpg.models.shop import Shop
        from cli_rpg.models.quest import Quest

        shop = Shop.from_dict(data["shop"]) if data.get("shop") else None
        offered_quests = [
            Quest.from_dict(q) for q in data.get("offered_quests", [])
        ]
        relationships = [
            NPCRelationship.from_dict(r) for r in data.get("relationships", [])
        ]
        arc_data = data.get("arc")
        arc = NPCArc.from_dict(arc_data) if arc_data else None
        return cls(
            name=data["name"],
            description=data["description"],
            dialogue=data["dialogue"],
            is_merchant=data.get("is_merchant", False),
            shop=shop,
            is_quest_giver=data.get("is_quest_giver", False),
            offered_quests=offered_quests,
            greetings=data.get("greetings", []),
            conversation_history=data.get("conversation_history", []),
            ascii_art=data.get("ascii_art", ""),
            available_at_night=data.get("available_at_night", True),
            is_recruitable=data.get("is_recruitable", False),
            willpower=data.get("willpower", 5),  # Default 5 for backward compat
            bribeable=data.get("bribeable", True),  # Default True for backward compat
            persuaded=data.get("persuaded", False),  # Default False for backward compat
            haggleable=data.get("haggleable", True),  # Default True for backward compat
            haggle_cooldown=data.get("haggle_cooldown", 0),  # Default 0 for backward compat
            faction=data.get("faction"),  # None for backward compat
            required_reputation=data.get("required_reputation"),  # None for backward compat
            relationships=relationships,  # Empty list for backward compat
            arc=arc,  # None for backward compat
        )
