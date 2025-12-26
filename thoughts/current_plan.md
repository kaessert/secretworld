# Implementation Plan: WorldContext Model

## Summary
Create the `WorldContext` dataclass model as foundation for the layered AI generation architecture (Step 3 from ISSUES.md).

## Spec
`WorldContext` is a dataclass that stores cached world theme information generated once at world creation. It enables consistent AI-generated content by providing theme essence, naming conventions, and tone to all subsequent generation calls.

Fields:
- `theme: str` - Base theme keyword (e.g., "fantasy", "cyberpunk")
- `theme_essence: str` - AI-generated theme summary (e.g., "dark medieval fantasy with corrupted magic")
- `naming_style: str` - How to name locations/NPCs (e.g., "Old English with Norse influence")
- `tone: str` - Narrative tone (e.g., "gritty, morally ambiguous")
- `generated_at: Optional[datetime]` - When context was generated (None if not AI-generated)

Required methods:
- `to_dict()` - Serialize for save/load
- `from_dict()` - Deserialize from save data
- `default()` - Class method for creating fallback context when AI unavailable

## Implementation Steps

### 1. Create `src/cli_rpg/models/world_context.py`
```python
@dataclass
class WorldContext:
    theme: str
    theme_essence: str = ""
    naming_style: str = ""
    tone: str = ""
    generated_at: Optional[datetime] = None

    def to_dict(self) -> dict
    def from_dict(cls, data: dict) -> "WorldContext"
    def default(cls, theme: str = "fantasy") -> "WorldContext"
```

### 2. Add to `src/cli_rpg/models/__init__.py`
Export `WorldContext` from models package.

### 3. Create `tests/test_world_context.py`
Test cases:
- `test_world_context_creation` - Basic instantiation with all fields
- `test_world_context_to_dict` - Serialization includes all fields
- `test_world_context_from_dict` - Deserialization restores all fields
- `test_world_context_from_dict_missing_fields` - Backward compatibility with partial data
- `test_world_context_default` - Default factory creates valid context

## Files to Create
- `src/cli_rpg/models/world_context.py`
- `tests/test_world_context.py`

## Files to Modify
- `src/cli_rpg/models/__init__.py` (add export)
