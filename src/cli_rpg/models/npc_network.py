"""NPC Network Manager for managing NPC relationship networks."""
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from cli_rpg.models.npc import NPC
from cli_rpg.models.npc_relationship import RelationshipType


class FamilyRole(Enum):
    """Roles within a family unit."""

    SPOUSE = "spouse"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"


@dataclass
class NPCNetworkManager:
    """Manages NPC relationship networks.

    Provides functionality for:
    - Registering and looking up NPCs by name
    - Creating bidirectional relationships
    - Generating family units
    - Querying relationship networks

    Attributes:
        _npcs: Dictionary mapping lowercase NPC names to NPC instances
    """

    _npcs: Dict[str, NPC] = field(default_factory=dict)

    def add_npc(self, npc: NPC) -> None:
        """Register an NPC by name (case-insensitive).

        Args:
            npc: The NPC to register
        """
        self._npcs[npc.name.lower()] = npc

    def get_npc(self, name: str) -> Optional[NPC]:
        """Look up an NPC by name (case-insensitive).

        Args:
            name: The name to look up

        Returns:
            The NPC if found, None otherwise
        """
        return self._npcs.get(name.lower())

    def get_all_npcs(self) -> List[NPC]:
        """Get all registered NPCs.

        Returns:
            List of all NPCs in the network
        """
        return list(self._npcs.values())

    def add_relationship(
        self,
        source_name: str,
        target_name: str,
        rel_type: RelationshipType,
        trust: int = 50,
        desc: Optional[str] = None,
        bidirectional: bool = True,
    ) -> None:
        """Add a relationship between two NPCs.

        Args:
            source_name: Name of the source NPC
            target_name: Name of the target NPC
            rel_type: Type of relationship
            trust: Trust level (1-100, default 50)
            desc: Optional description (e.g., "sister", "former master")
            bidirectional: If True, add reciprocal relationship to target NPC

        Raises:
            ValueError: If either NPC is not found in the network
        """
        source = self.get_npc(source_name)
        target = self.get_npc(target_name)

        if source is None:
            raise ValueError(f"NPC not found: {source_name}")
        if target is None:
            raise ValueError(f"NPC not found: {target_name}")

        source.add_relationship(target.name, rel_type, trust, desc)

        if bidirectional:
            target.add_relationship(source.name, rel_type, trust, desc)

    def generate_spouse(
        self,
        npc_name: str,
        spouse_name: str,
        desc: Optional[str] = None,
    ) -> NPC:
        """Generate a spouse NPC and link them with FAMILY relationship.

        Args:
            npc_name: Name of the existing NPC
            spouse_name: Name for the new spouse NPC
            desc: Optional description override (default: "spouse")

        Returns:
            The newly created spouse NPC

        Raises:
            ValueError: If the NPC is not found in the network
        """
        npc = self.get_npc(npc_name)
        if npc is None:
            raise ValueError(f"NPC not found: {npc_name}")

        desc = desc or "spouse"

        # Create minimal spouse NPC
        spouse = NPC(
            name=spouse_name,
            description=f"Spouse of {npc.name}",
            dialogue=f"Hello, I'm {spouse_name}.",
        )
        self.add_npc(spouse)

        # Add bidirectional FAMILY relationship with "spouse" description
        npc.add_relationship(spouse.name, RelationshipType.FAMILY, trust=90, desc=desc)
        spouse.add_relationship(npc.name, RelationshipType.FAMILY, trust=90, desc=desc)

        return spouse

    def generate_child(
        self,
        parent_names: List[str],
        child_name: str,
    ) -> NPC:
        """Generate a child NPC linked to parents.

        Args:
            parent_names: List of parent NPC names
            child_name: Name for the new child NPC

        Returns:
            The newly created child NPC

        Raises:
            ValueError: If any parent NPC is not found in the network
        """
        parents = []
        for parent_name in parent_names:
            parent = self.get_npc(parent_name)
            if parent is None:
                raise ValueError(f"NPC not found: {parent_name}")
            parents.append(parent)

        # Create child NPC
        child = NPC(
            name=child_name,
            description=f"Child of {' and '.join(parent_names)}",
            dialogue=f"Hello, I'm {child_name}.",
        )
        self.add_npc(child)

        # Add relationships: child -> parent with "parent" description
        # parent -> child with "child" description
        for parent in parents:
            child.add_relationship(parent.name, RelationshipType.FAMILY, trust=90, desc="parent")
            parent.add_relationship(child.name, RelationshipType.FAMILY, trust=90, desc="child")

        return child

    def generate_sibling(
        self,
        npc_name: str,
        sibling_name: str,
    ) -> NPC:
        """Generate a sibling NPC with reciprocal relationship.

        Args:
            npc_name: Name of the existing NPC
            sibling_name: Name for the new sibling NPC

        Returns:
            The newly created sibling NPC

        Raises:
            ValueError: If the NPC is not found in the network
        """
        npc = self.get_npc(npc_name)
        if npc is None:
            raise ValueError(f"NPC not found: {npc_name}")

        # Create sibling NPC
        sibling = NPC(
            name=sibling_name,
            description=f"Sibling of {npc.name}",
            dialogue=f"Hello, I'm {sibling_name}.",
        )
        self.add_npc(sibling)

        # Add bidirectional FAMILY relationship with "sibling" description
        npc.add_relationship(sibling.name, RelationshipType.FAMILY, trust=80, desc="sibling")
        sibling.add_relationship(npc.name, RelationshipType.FAMILY, trust=80, desc="sibling")

        return sibling

    def generate_family_unit(
        self,
        head_name: str,
        spouse_name: Optional[str] = None,
        child_names: Optional[List[str]] = None,
    ) -> List[NPC]:
        """Generate a connected family unit.

        Creates a head NPC, optionally a spouse, and optionally children linked to
        both parents. Children are also linked as siblings to each other.

        Args:
            head_name: Name for the family head NPC
            spouse_name: Optional name for spouse NPC
            child_names: Optional list of names for child NPCs

        Returns:
            List of all created NPCs in the family unit
        """
        family = []

        # Create head NPC
        head = NPC(
            name=head_name,
            description=f"Head of the {head_name} family",
            dialogue=f"Hello, I'm {head_name}.",
        )
        self.add_npc(head)
        family.append(head)

        parent_names = [head_name]

        # Optionally create spouse
        if spouse_name:
            spouse = self.generate_spouse(head_name, spouse_name)
            family.append(spouse)
            parent_names.append(spouse_name)

        # Optionally create children
        if child_names:
            children = []
            for child_name in child_names:
                child = self.generate_child(parent_names, child_name)
                family.append(child)
                children.append(child)

            # Make children siblings of each other
            for i, child in enumerate(children):
                for j, other_child in enumerate(children):
                    if i != j:
                        # Only add if relationship doesn't exist
                        if child.get_relationship(other_child.name) is None:
                            child.add_relationship(
                                other_child.name, RelationshipType.FAMILY, trust=80, desc="sibling"
                            )

        return family

    def get_npcs_with_relationship(
        self,
        npc_name: str,
        rel_type: RelationshipType,
    ) -> List[str]:
        """Get names of NPCs connected to the given NPC by relationship type.

        Args:
            npc_name: Name of the NPC to query
            rel_type: Type of relationship to filter by

        Returns:
            List of NPC names connected via the specified relationship type
        """
        npc = self.get_npc(npc_name)
        if npc is None:
            return []

        relationships = npc.get_relationships_by_type(rel_type)
        return [rel.target_npc for rel in relationships]

    def get_family_members(self, npc_name: str) -> List[str]:
        """Get names of all family members of an NPC.

        Args:
            npc_name: Name of the NPC to query

        Returns:
            List of NPC names with FAMILY relationship
        """
        return self.get_npcs_with_relationship(npc_name, RelationshipType.FAMILY)

    def get_connections(self, npc_name: str, max_degrees: int = 1) -> Set[str]:
        """Get all NPCs connected within N degrees of separation.

        Uses BFS traversal to find all connected NPCs up to max_degrees hops.

        Args:
            npc_name: Name of the starting NPC
            max_degrees: Maximum number of hops to traverse (default 1)

        Returns:
            Set of NPC names within max_degrees hops (excluding the starting NPC)
        """
        start_npc = self.get_npc(npc_name)
        if start_npc is None:
            return set()

        visited: Set[str] = set()
        queue: deque[Tuple[str, int]] = deque()

        # Start from all direct connections of the starting NPC
        for rel in start_npc.relationships:
            queue.append((rel.target_npc, 1))

        while queue:
            current_name, degree = queue.popleft()

            if current_name in visited or current_name.lower() == npc_name.lower():
                continue

            if degree > max_degrees:
                continue

            visited.add(current_name)

            # Add connections of current NPC to queue for next degree
            current_npc = self.get_npc(current_name)
            if current_npc and degree < max_degrees:
                for rel in current_npc.relationships:
                    if rel.target_npc not in visited:
                        queue.append((rel.target_npc, degree + 1))

        return visited

    def find_path(
        self,
        start_name: str,
        end_name: str,
    ) -> Optional[List[Tuple[str, RelationshipType]]]:
        """Find the shortest path between two NPCs.

        Uses BFS to find the shortest relationship chain between NPCs.

        Args:
            start_name: Name of the starting NPC
            end_name: Name of the target NPC

        Returns:
            List of (npc_name, relationship_type) tuples representing the path,
            or None if no path exists
        """
        start_npc = self.get_npc(start_name)
        end_npc = self.get_npc(end_name)

        if start_npc is None or end_npc is None:
            return None

        if start_name.lower() == end_name.lower():
            return []

        # BFS with path tracking
        visited: Set[str] = {start_name.lower()}
        # Queue contains: (current_npc_name, path_so_far)
        queue: deque[Tuple[str, List[Tuple[str, RelationshipType]]]] = deque()

        # Start from direct connections
        for rel in start_npc.relationships:
            path = [(rel.target_npc, rel.relationship_type)]
            if rel.target_npc.lower() == end_name.lower():
                return path
            queue.append((rel.target_npc, path))
            visited.add(rel.target_npc.lower())

        while queue:
            current_name, current_path = queue.popleft()
            current_npc = self.get_npc(current_name)

            if current_npc is None:
                continue

            for rel in current_npc.relationships:
                if rel.target_npc.lower() in visited:
                    continue

                new_path = current_path + [(rel.target_npc, rel.relationship_type)]

                if rel.target_npc.lower() == end_name.lower():
                    return new_path

                visited.add(rel.target_npc.lower())
                queue.append((rel.target_npc, new_path))

        return None

    def to_dict(self) -> dict:
        """Serialize the manager to a dictionary.

        Returns:
            Dictionary containing all NPCs
        """
        return {
            "npcs": [npc.to_dict() for npc in self._npcs.values()]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPCNetworkManager":
        """Deserialize the manager from a dictionary.

        Args:
            data: Dictionary containing NPC data

        Returns:
            NPCNetworkManager instance
        """
        manager = cls()
        for npc_data in data.get("npcs", []):
            npc = NPC.from_dict(npc_data)
            manager.add_npc(npc)
        return manager
