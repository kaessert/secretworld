# Quest Faction Integration Implementation Plan

## Spec

Quests can be affiliated with factions, affecting reputation on completion:
1. **`faction_affiliation`** (Optional[str]): The faction this quest is associated with (e.g., "Town Guard")
2. **`faction_reward`** (int, default 0): Reputation gained with affiliated faction on completion
3. **`faction_penalty`** (int, default 0): Reputation lost with rival faction on completion
4. **`required_reputation`** (Optional[int]): Minimum reputation with faction required to accept quest

Behavior:
- On quest completion via `complete` command, apply faction reputation changes
- Display reputation change messages alongside gold/XP/item rewards
- Quest acceptance checks `required_reputation` against player's current standing
- AI quest generation includes faction fields when NPC has faction affiliation

---

## Tests (TDD)

### File: `tests/test_quest_faction.py`

```python
"""Tests for quest faction integration."""

# Quest model tests
- test_quest_faction_affiliation_field_optional
- test_quest_faction_reward_field_defaults_to_zero
- test_quest_faction_penalty_field_defaults_to_zero
- test_quest_required_reputation_field_optional
- test_quest_negative_faction_reward_rejected
- test_quest_negative_faction_penalty_rejected
- test_quest_to_dict_includes_faction_fields
- test_quest_from_dict_restores_faction_fields
- test_quest_from_dict_missing_faction_fields_uses_defaults

# Claim rewards faction integration tests
- test_claim_quest_rewards_applies_faction_reward
- test_claim_quest_rewards_applies_faction_penalty_to_rival
- test_claim_quest_rewards_returns_faction_messages
- test_claim_quest_rewards_triggers_level_up_message
- test_claim_quest_rewards_with_no_faction_affiliation_no_changes

# Quest acceptance tests
- test_accept_quest_allowed_when_reputation_meets_requirement
- test_accept_quest_blocked_when_reputation_too_low
- test_accept_quest_allowed_when_no_required_reputation
```

---

## Implementation Steps

### 1. Update Quest Model (`src/cli_rpg/models/quest.py`)

Add new fields to `Quest` dataclass:
```python
faction_affiliation: Optional[str] = field(default=None)
faction_reward: int = field(default=0)
faction_penalty: int = field(default=0)
required_reputation: Optional[int] = field(default=None)
```

Add validation in `__post_init__`:
```python
if self.faction_reward < 0:
    raise ValueError("faction_reward cannot be negative")
if self.faction_penalty < 0:
    raise ValueError("faction_penalty cannot be negative")
```

Update `to_dict()` to include:
```python
"faction_affiliation": self.faction_affiliation,
"faction_reward": self.faction_reward,
"faction_penalty": self.faction_penalty,
"required_reputation": self.required_reputation,
```

Update `from_dict()` to restore:
```python
faction_affiliation=data.get("faction_affiliation"),
faction_reward=data.get("faction_reward", 0),
faction_penalty=data.get("faction_penalty", 0),
required_reputation=data.get("required_reputation"),
```

### 2. Update Character.claim_quest_rewards() (`src/cli_rpg/models/character.py`)

Modify signature to accept optional factions list:
```python
def claim_quest_rewards(self, quest: "Quest", factions: Optional[List["Faction"]] = None) -> List[str]:
```

After existing reward logic, add faction handling:
```python
# Apply faction reputation changes
if quest.faction_affiliation and factions:
    from cli_rpg.faction_combat import _find_faction_by_name, FACTION_RIVALRIES

    affiliated = _find_faction_by_name(factions, quest.faction_affiliation)
    if affiliated and quest.faction_reward > 0:
        level_msg = affiliated.add_reputation(quest.faction_reward)
        messages.append(f"Reputation with {affiliated.name} increased by {quest.faction_reward}.")
        if level_msg:
            messages.append(level_msg)

    # Apply penalty to rival faction
    rival_name = FACTION_RIVALRIES.get(quest.faction_affiliation)
    if rival_name and quest.faction_penalty > 0:
        rival = _find_faction_by_name(factions, rival_name)
        if rival:
            level_msg = rival.reduce_reputation(quest.faction_penalty)
            messages.append(f"Reputation with {rival.name} decreased by {quest.faction_penalty}.")
            if level_msg:
                messages.append(level_msg)
```

### 3. Update main.py Complete Command (line ~1703)

Pass factions to claim_quest_rewards:
```python
# Change from:
reward_messages = game_state.current_character.claim_quest_rewards(matching_quest)
# To:
reward_messages = game_state.current_character.claim_quest_rewards(
    matching_quest, factions=game_state.factions
)
```

### 4. Update main.py Accept Command (around line 1640-1660)

Add reputation check before accepting quest:
```python
# Before creating the new quest, check required reputation
if matching_quest.required_reputation is not None:
    from cli_rpg.faction_combat import _find_faction_by_name
    if matching_quest.faction_affiliation:
        faction = _find_faction_by_name(game_state.factions, matching_quest.faction_affiliation)
        if faction and faction.reputation < matching_quest.required_reputation:
            return (True, f"\n{npc.name} refuses to give you this quest. You need higher reputation with {matching_quest.faction_affiliation}.")
```

### 5. Update AI Quest Generation Prompt (`src/cli_rpg/ai_config.py`)

Update `DEFAULT_QUEST_GENERATION_PROMPT` (around line 146-195):

Add to JSON schema section:
```
6. If the NPC has a faction affiliation, include faction fields:
   - faction_affiliation: The faction name (same as NPC's faction)
   - faction_reward: 5-15 reputation points (scaled by quest difficulty)
   - faction_penalty: 3-10 reputation points for rival faction

Respond with valid JSON in this exact format (no additional text):
{{
  "name": "Quest Name",
  "description": "A brief description of the quest objective.",
  "objective_type": "kill|collect|explore|talk|drop",
  "target": "target name",
  "target_count": <number>,
  "gold_reward": <number>,
  "xp_reward": <number>,
  "faction_affiliation": "Faction Name or null",
  "faction_reward": <number>,
  "faction_penalty": <number>
}}
```

### 6. Update AIService._parse_quest_response (`src/cli_rpg/ai_service.py`)

In the quest parsing logic (around line 1874), extract faction fields:
```python
quest_data["faction_affiliation"] = data.get("faction_affiliation")
quest_data["faction_reward"] = data.get("faction_reward", 0)
quest_data["faction_penalty"] = data.get("faction_penalty", 0)
```

---

## Verification

Run tests:
```bash
pytest tests/test_quest_faction.py -v
pytest tests/test_quest*.py -v  # Ensure no regressions
pytest tests/test_faction*.py -v  # Ensure faction tests still pass
```
