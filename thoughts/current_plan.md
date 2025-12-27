# Issue 11: NPC Network Manager

## Spec

Create `NPCNetworkManager` class to manage NPC relationship networks including:
- **Family generation**: Generate family units (spouses, children, siblings) for NPCs
- **Relationship propagation**: When NPC A knows NPC B, optionally have B know A (bidirectional)
- **Network queries**: Find NPCs by relationship type, find connected NPCs within N degrees

## Files

- **Create**: `src/cli_rpg/models/npc_network.py`
- **Create**: `tests/test_npc_network.py`

## Tests (TDD)

### FamilyRole Enum
- `test_family_role_spouse_exists` - FamilyRole.SPOUSE exists with value "spouse"
- `test_family_role_parent_exists` - FamilyRole.PARENT exists with value "parent"
- `test_family_role_child_exists` - FamilyRole.CHILD exists with value "child"
- `test_family_role_sibling_exists` - FamilyRole.SIBLING exists with value "sibling"

### NPCNetworkManager Initialization
- `test_network_manager_init_empty` - Manager initializes with empty NPC dict
- `test_network_manager_add_npc` - `add_npc(npc)` registers NPC by name
- `test_network_manager_get_npc` - `get_npc(name)` returns NPC or None
- `test_network_manager_get_all_npcs` - `get_all_npcs()` returns list of all NPCs

### Bidirectional Relationships
- `test_add_relationship_bidirectional` - `add_relationship(npc_a, npc_b, type, bidirectional=True)` adds to both
- `test_add_relationship_unidirectional` - `add_relationship(npc_a, npc_b, type, bidirectional=False)` adds to A only
- `test_add_relationship_with_trust` - Trust level is set correctly on both sides

### Family Generation
- `test_generate_spouse` - `generate_spouse(npc, name)` creates spouse NPC with FAMILY relationship
- `test_generate_child` - `generate_child(parents, name)` creates child linked to both parents
- `test_generate_sibling` - `generate_sibling(npc, name)` creates sibling with reciprocal relationships
- `test_generate_family_unit` - `generate_family_unit(head_name, size)` creates connected family

### Network Queries
- `test_get_npcs_by_relationship` - `get_npcs_with_relationship(npc, type)` returns list of connected NPCs
- `test_get_family_members` - `get_family_members(npc)` returns all FAMILY relationships
- `test_get_connections_within_degrees` - `get_connections(npc, max_degrees=2)` returns NPCs within N hops
- `test_find_path_between_npcs` - `find_path(npc_a, npc_b)` returns relationship chain or None

### Serialization
- `test_to_dict` - Manager serializes to dict with all NPCs
- `test_from_dict` - Manager deserializes from dict
- `test_roundtrip` - Roundtrip preserves all NPCs and relationships

## Implementation Steps

1. **Create test file** `tests/test_npc_network.py` with all tests above (initially failing)

2. **Create FamilyRole enum** in `npc_network.py`:
   ```python
   class FamilyRole(Enum):
       SPOUSE = "spouse"
       PARENT = "parent"
       CHILD = "child"
       SIBLING = "sibling"
   ```

3. **Create NPCNetworkManager class**:
   - `__init__()` - Initialize `_npcs: dict[str, NPC]`
   - `add_npc(npc)` - Register NPC by name (lowercase key for case-insensitive lookup)
   - `get_npc(name)` - Lookup by name
   - `get_all_npcs()` - Return list of all NPCs

4. **Implement bidirectional relationships**:
   - `add_relationship(source, target, rel_type, trust=50, desc=None, bidirectional=True)`:
     - Get inverse description for bidirectional (e.g., "sister" -> "sister")
     - Add relationship to source NPC
     - If bidirectional, add reciprocal relationship to target NPC

5. **Implement family generation**:
   - `generate_spouse(npc, spouse_name, desc_a="spouse", desc_b="spouse")`:
     - Create new NPC with minimal attributes
     - Register in manager
     - Add bidirectional FAMILY relationship with descriptions
   - `generate_child(parent_names: list[str], child_name)`:
     - Create child NPC
     - Add FAMILY relationships to each parent (child->parent, parent->child)
   - `generate_sibling(npc, sibling_name)`:
     - Create sibling NPC
     - Add bidirectional FAMILY relationship with "sibling" description
   - `generate_family_unit(head_name, spouse_name=None, child_names=None)`:
     - Create head NPC
     - Optionally add spouse
     - Optionally add children linked to both parents

6. **Implement network queries**:
   - `get_npcs_with_relationship(npc_name, rel_type)`:
     - Return list of NPC names connected via that relationship type
   - `get_family_members(npc_name)`:
     - Shortcut for `get_npcs_with_relationship(npc_name, RelationshipType.FAMILY)`
   - `get_connections(npc_name, max_degrees=1)`:
     - BFS traversal up to max_degrees hops
     - Return set of NPC names (excluding starting NPC)
   - `find_path(npc_a, npc_b)`:
     - BFS to find shortest path between NPCs
     - Return list of (npc_name, relationship_type) tuples or None

7. **Implement serialization**:
   - `to_dict()`: Return `{"npcs": [npc.to_dict() for npc in self._npcs.values()]}`
   - `from_dict(data)`: Create manager, add each NPC from data

8. **Run tests** to verify all pass
