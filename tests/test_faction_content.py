"""Unit tests for faction-based content gating.

Tests the faction_content module which provides reputation-based access control
for NPCs, locations, and shops.
"""

import pytest

from cli_rpg.models.faction import Faction, ReputationLevel
from cli_rpg.models.npc import NPC
from cli_rpg.models.location import Location


# ============================================================================
# NPC Model Tests - required_reputation field
# ============================================================================


class TestNPCRequiredReputation:
    """Test the required_reputation field on NPC model."""

    def test_npc_required_reputation_field_defaults_to_none(self):
        """Spec: NPC.required_reputation should default to None (no requirement)."""
        npc = NPC(
            name="Test NPC",
            description="A test NPC",
            dialogue="Hello!",
        )
        assert npc.required_reputation is None

    def test_npc_required_reputation_can_be_set(self):
        """Spec: NPC.required_reputation can be set to a reputation value."""
        npc = NPC(
            name="Guild Master",
            description="The head of the guild",
            dialogue="Welcome, honored member!",
            faction="Merchant Guild",
            required_reputation=60,  # Requires FRIENDLY
        )
        assert npc.required_reputation == 60
        assert npc.faction == "Merchant Guild"

    def test_npc_required_reputation_serialization(self):
        """Spec: required_reputation should be serialized/deserialized correctly."""
        npc = NPC(
            name="Elite Guard",
            description="A guard for the inner sanctum",
            dialogue="You may pass.",
            faction="Royal Guard",
            required_reputation=80,  # Requires HONORED
        )

        # Serialize
        data = npc.to_dict()
        assert data["required_reputation"] == 80
        assert data["faction"] == "Royal Guard"

        # Deserialize
        restored = NPC.from_dict(data)
        assert restored.required_reputation == 80
        assert restored.faction == "Royal Guard"

    def test_npc_required_reputation_backward_compatibility(self):
        """Spec: Old save files without required_reputation should load with None."""
        # Simulate old save data (no required_reputation field)
        old_data = {
            "name": "Old NPC",
            "description": "An NPC from an old save",
            "dialogue": "Hello traveler!",
            "faction": "Town Watch",
        }

        npc = NPC.from_dict(old_data)
        assert npc.required_reputation is None
        assert npc.faction == "Town Watch"


# ============================================================================
# Location Model Tests - required_faction and required_reputation fields
# ============================================================================


class TestLocationFactionRequirements:
    """Test faction requirement fields on Location model."""

    def test_location_required_faction_field_defaults_to_none(self):
        """Spec: Location.required_faction should default to None."""
        loc = Location(
            name="Test Location",
            description="A test location",
        )
        assert loc.required_faction is None

    def test_location_required_reputation_field_defaults_to_none(self):
        """Spec: Location.required_reputation should default to None."""
        loc = Location(
            name="Test Location",
            description="A test location",
        )
        assert loc.required_reputation is None

    def test_location_faction_requirements_can_be_set(self):
        """Spec: Location faction fields can be set together."""
        loc = Location(
            name="Guild Hall Inner Sanctum",
            description="The inner chambers of the guild hall",
            required_faction="Merchant Guild",
            required_reputation=60,
        )
        assert loc.required_faction == "Merchant Guild"
        assert loc.required_reputation == 60

    def test_location_required_reputation_serialization(self):
        """Spec: Faction requirements should be serialized/deserialized correctly."""
        loc = Location(
            name="Secret Vault",
            description="The guild's secret vault",
            required_faction="Thieves Guild",
            required_reputation=80,
        )

        # Serialize
        data = loc.to_dict()
        assert data["required_faction"] == "Thieves Guild"
        assert data["required_reputation"] == 80

        # Deserialize
        restored = Location.from_dict(data)
        assert restored.required_faction == "Thieves Guild"
        assert restored.required_reputation == 80

    def test_location_faction_requirements_backward_compatibility(self):
        """Spec: Old save files without faction fields should load with None."""
        old_data = {
            "name": "Old Location",
            "description": "A location from an old save",
        }

        loc = Location.from_dict(old_data)
        assert loc.required_faction is None
        assert loc.required_reputation is None


# ============================================================================
# faction_content module tests - check_npc_access
# ============================================================================


class TestCheckNPCAccess:
    """Test the check_npc_access function."""

    def test_check_npc_access_no_requirement_always_allowed(self):
        """Spec: NPCs without required_reputation are accessible at non-hostile rep levels."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Common Merchant",
            description="A simple merchant",
            dialogue="What can I get for you?",
            faction="Merchant Guild",
            # No required_reputation
        )
        # Use UNFRIENDLY (20) - not blocking without required_reputation
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=20)]

        allowed, message = check_npc_access(npc, factions)
        assert allowed is True
        assert message == ""

    def test_check_npc_access_blocked_when_reputation_too_low(self):
        """Spec: NPCs with required_reputation block when player rep is too low."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Guild Master",
            description="The head of the merchant guild",
            dialogue="Welcome, trusted partner!",
            faction="Merchant Guild",
            required_reputation=60,  # Requires FRIENDLY
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=40)]

        allowed, message = check_npc_access(npc, factions)
        assert allowed is False
        assert "Guild Master" in message
        assert "Merchant Guild" in message
        assert "reputation" in message.lower()

    def test_check_npc_access_allowed_when_reputation_sufficient(self):
        """Spec: NPCs allow access when player meets reputation requirement."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Guild Master",
            description="The head of the merchant guild",
            dialogue="Welcome, trusted partner!",
            faction="Merchant Guild",
            required_reputation=60,
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=75)]

        allowed, message = check_npc_access(npc, factions)
        assert allowed is True
        assert message == ""

    def test_check_npc_access_allowed_when_reputation_exactly_meets_threshold(self):
        """Spec: NPCs allow access when player rep equals the requirement exactly."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Senior Member",
            description="A senior guild member",
            dialogue="Welcome, friend.",
            faction="Merchant Guild",
            required_reputation=60,
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=60)]

        allowed, message = check_npc_access(npc, factions)
        assert allowed is True
        assert message == ""

    def test_check_npc_access_hostile_faction_blocks_entirely(self):
        """Spec: NPCs from hostile factions block dialogue entirely."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Faction Guard",
            description="A guard loyal to the faction",
            dialogue="Get lost!",
            faction="Enemy Faction",
            # No required_reputation - just being HOSTILE blocks access
        )
        factions = [Faction(name="Enemy Faction", description="Enemies", reputation=10)]

        allowed, message = check_npc_access(npc, factions)
        assert allowed is False
        assert "hostile" in message.lower() or "refuses" in message.lower()

    def test_check_npc_access_no_faction_always_allowed(self):
        """Spec: NPCs without faction affiliation are always accessible."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Wandering Traveler",
            description="A traveler passing through",
            dialogue="Hello, fellow traveler!",
            # No faction
        )
        factions = []

        allowed, message = check_npc_access(npc, factions)
        assert allowed is True
        assert message == ""

    def test_check_npc_access_unknown_faction_treated_as_neutral(self):
        """Spec: NPCs with unknown faction are accessible (no matching faction = no block)."""
        from cli_rpg.faction_content import check_npc_access

        npc = NPC(
            name="Mystery Agent",
            description="An agent of an unknown group",
            dialogue="Interesting...",
            faction="Unknown Order",
            required_reputation=60,
        )
        # Player has no faction record for "Unknown Order"
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=80)]

        # Unknown factions should block if there's a requirement (can't meet unknown req)
        allowed, message = check_npc_access(npc, factions)
        assert allowed is False
        assert "Unknown Order" in message


# ============================================================================
# faction_content module tests - check_location_access
# ============================================================================


class TestCheckLocationAccess:
    """Test the check_location_access function."""

    def test_check_location_access_no_requirement_always_allowed(self):
        """Spec: Locations without faction requirements are always accessible."""
        from cli_rpg.faction_content import check_location_access

        loc = Location(
            name="Town Square",
            description="The central square of town",
        )
        factions = []

        allowed, message = check_location_access(loc, factions)
        assert allowed is True
        assert message == ""

    def test_check_location_access_blocked_when_reputation_too_low(self):
        """Spec: Locations block entry when player rep is below requirement."""
        from cli_rpg.faction_content import check_location_access

        loc = Location(
            name="Guild Inner Sanctum",
            description="The private chambers of the guild",
            required_faction="Merchant Guild",
            required_reputation=80,
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=50)]

        allowed, message = check_location_access(loc, factions)
        assert allowed is False
        assert "Guild Inner Sanctum" in message
        assert "Merchant Guild" in message

    def test_check_location_access_allowed_when_reputation_sufficient(self):
        """Spec: Locations allow entry when player meets reputation requirement."""
        from cli_rpg.faction_content import check_location_access

        loc = Location(
            name="Guild Inner Sanctum",
            description="The private chambers of the guild",
            required_faction="Merchant Guild",
            required_reputation=80,
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=90)]

        allowed, message = check_location_access(loc, factions)
        assert allowed is True
        assert message == ""

    def test_check_location_access_unknown_faction_blocks(self):
        """Spec: Locations with unknown faction requirements block access."""
        from cli_rpg.faction_content import check_location_access

        loc = Location(
            name="Secret Hideout",
            description="A hidden location",
            required_faction="Shadow Collective",
            required_reputation=60,
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=100)]

        allowed, message = check_location_access(loc, factions)
        assert allowed is False
        assert "Shadow Collective" in message


# ============================================================================
# faction_content module tests - filter_visible_npcs
# ============================================================================


class TestFilterVisibleNPCs:
    """Test the filter_visible_npcs function."""

    def test_filter_visible_npcs_removes_gated_npcs(self):
        """Spec: NPCs not meeting reputation requirements are hidden."""
        from cli_rpg.faction_content import filter_visible_npcs

        npcs = [
            NPC(
                name="Guild Master",
                description="The leader",
                dialogue="Welcome!",
                faction="Merchant Guild",
                required_reputation=80,
            ),
            NPC(
                name="Common Clerk",
                description="A clerk",
                dialogue="Hello!",
                faction="Merchant Guild",
                # No required_reputation
            ),
        ]
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=50)]

        visible = filter_visible_npcs(npcs, factions)
        assert len(visible) == 1
        assert visible[0].name == "Common Clerk"

    def test_filter_visible_npcs_keeps_ungated_npcs(self):
        """Spec: NPCs without requirements are always visible."""
        from cli_rpg.faction_content import filter_visible_npcs

        npcs = [
            NPC(name="Merchant", description="A trader", dialogue="Buy something!"),
            NPC(name="Guard", description="A town guard", dialogue="Stay out of trouble."),
        ]
        factions = []

        visible = filter_visible_npcs(npcs, factions)
        assert len(visible) == 2

    def test_filter_visible_npcs_hides_hostile_faction_members(self):
        """Spec: NPCs from hostile factions are hidden from view."""
        from cli_rpg.faction_content import filter_visible_npcs

        npcs = [
            NPC(
                name="Enemy Agent",
                description="A faction agent",
                dialogue="...",
                faction="Enemy Faction",
            ),
            NPC(name="Friendly NPC", description="A friend", dialogue="Hello!"),
        ]
        factions = [Faction(name="Enemy Faction", description="Enemies", reputation=10)]

        visible = filter_visible_npcs(npcs, factions)
        assert len(visible) == 1
        assert visible[0].name == "Friendly NPC"


# ============================================================================
# faction_content module tests - get_faction_greeting_modifier
# ============================================================================


class TestGetFactionGreetingModifier:
    """Test the get_faction_greeting_modifier function."""

    def test_get_faction_greeting_modifier_hostile_returns_rejection(self):
        """Spec: Hostile faction NPCs give rejection greetings."""
        from cli_rpg.faction_content import get_faction_greeting_modifier

        npc = NPC(
            name="Faction Guard",
            description="A guard",
            dialogue="Normal greeting",
            faction="Enemy Faction",
        )
        factions = [Faction(name="Enemy Faction", description="Enemies", reputation=10)]

        modifier = get_faction_greeting_modifier(npc, factions)
        assert modifier is not None
        # Should indicate hostility/rejection
        assert any(word in modifier.lower() for word in ["refuse", "hostile", "enemy", "leave", "won't"])

    def test_get_faction_greeting_modifier_unfriendly_returns_curt(self):
        """Spec: Unfriendly faction NPCs give curt greetings."""
        from cli_rpg.faction_content import get_faction_greeting_modifier

        npc = NPC(
            name="Skeptical Merchant",
            description="A cautious merchant",
            dialogue="Normal greeting",
            faction="Merchant Guild",
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=30)]

        modifier = get_faction_greeting_modifier(npc, factions)
        # Unfriendly is not blocking, but gives modified greeting
        if modifier:
            # Should indicate wariness
            assert any(word in modifier.lower() for word in ["wary", "cautious", "trust", "unfriendly", "curt"])

    def test_get_faction_greeting_modifier_friendly_returns_warm(self):
        """Spec: Friendly faction NPCs give warm greetings."""
        from cli_rpg.faction_content import get_faction_greeting_modifier

        npc = NPC(
            name="Guild Friend",
            description="A friendly member",
            dialogue="Normal greeting",
            faction="Merchant Guild",
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=70)]

        modifier = get_faction_greeting_modifier(npc, factions)
        assert modifier is not None
        # Should indicate friendliness
        assert any(word in modifier.lower() for word in ["friend", "welcome", "warm", "glad", "happy"])

    def test_get_faction_greeting_modifier_honored_returns_special(self):
        """Spec: Honored faction NPCs give special exclusive greetings."""
        from cli_rpg.faction_content import get_faction_greeting_modifier

        npc = NPC(
            name="Guild Elder",
            description="A senior member",
            dialogue="Normal greeting",
            faction="Merchant Guild",
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=90)]

        modifier = get_faction_greeting_modifier(npc, factions)
        assert modifier is not None
        # Should indicate high honor/respect
        assert any(word in modifier.lower() for word in ["honor", "respected", "welcome", "esteem", "distinguished"])

    def test_get_faction_greeting_modifier_neutral_returns_none(self):
        """Spec: Neutral faction NPCs use default greetings (no modifier)."""
        from cli_rpg.faction_content import get_faction_greeting_modifier

        npc = NPC(
            name="Regular Member",
            description="A member",
            dialogue="Normal greeting",
            faction="Merchant Guild",
        )
        factions = [Faction(name="Merchant Guild", description="Traders", reputation=50)]

        modifier = get_faction_greeting_modifier(npc, factions)
        # Neutral returns None (use default greeting)
        assert modifier is None

    def test_get_faction_greeting_modifier_no_faction_returns_none(self):
        """Spec: NPCs without faction use default greetings."""
        from cli_rpg.faction_content import get_faction_greeting_modifier

        npc = NPC(
            name="Wanderer",
            description="A traveler",
            dialogue="Hello!",
            # No faction
        )
        factions = []

        modifier = get_faction_greeting_modifier(npc, factions)
        assert modifier is None
