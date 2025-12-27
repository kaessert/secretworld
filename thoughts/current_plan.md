# Issue 10: NPC Relationship Networks - Implementation Plan

## Spec

Create a relationship model to track connections between NPCs with:
- **Relationship types**: FAMILY, FRIEND, RIVAL, MENTOR, EMPLOYER, ACQUAINTANCE
- **Trust levels**: 1-100 scale representing relationship strength
- **Bidirectional references**: Each NPC stores its relationships to other NPCs (by name)

## Files to Create

### 1. `src/cli_rpg/models/npc_relationship.py`
```python
# RelationshipType enum with values: FAMILY, FRIEND, RIVAL, MENTOR, EMPLOYER, ACQUAINTANCE
# NPCRelationship dataclass:
#   - target_npc: str (name of related NPC)
#   - relationship_type: RelationshipType
#   - trust_level: int (1-100, default 50)
#   - description: Optional[str] (e.g., "sister", "former master")
# Methods:
#   - to_dict() -> dict
#   - from_dict(cls, data) -> NPCRelationship
```

### 2. `tests/test_npc_relationship.py`
```python
# Test RelationshipType enum values exist
# Test NPCRelationship creation with all fields
# Test trust_level clamping to 1-100
# Test to_dict() serialization
# Test from_dict() deserialization
# Test roundtrip serialization
```

## Files to Modify

### 3. `src/cli_rpg/models/npc.py`
Add to NPC dataclass:
```python
relationships: List["NPCRelationship"] = field(default_factory=list)
```

Add methods:
```python
def add_relationship(self, target: str, rel_type: RelationshipType, trust: int = 50, desc: str = None) -> None
def get_relationship(self, target: str) -> Optional[NPCRelationship]
def get_relationships_by_type(self, rel_type: RelationshipType) -> List[NPCRelationship]
```

Update `to_dict()` and `from_dict()` to include relationships.

### 4. `tests/test_npc.py`
Add tests:
```python
# test_npc_relationships_default_empty()
# test_add_relationship_basic()
# test_get_relationship_by_name()
# test_get_relationships_by_type()
# test_npc_with_relationships_serialization()
# test_npc_backward_compat_no_relationships()
```

## Implementation Order

1. Create `tests/test_npc_relationship.py` with tests for NPCRelationship model
2. Create `src/cli_rpg/models/npc_relationship.py` - run tests until passing
3. Add relationship tests to `tests/test_npc.py`
4. Modify `src/cli_rpg/models/npc.py` to add relationships field and methods - run tests until passing
5. Run full test suite to verify no regressions
