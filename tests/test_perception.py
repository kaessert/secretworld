"""Tests for Perception stat and secret discovery system."""
import pytest
from cli_rpg.models.character import Character, CharacterClass, CLASS_BONUSES
from cli_rpg.models.location import Location
from cli_rpg.secrets import check_passive_detection, perform_active_search, SecretType


class TestPerceptionStat:
    """Test PER stat on Character model."""

    def test_character_has_perception_stat(self):
        """Character has perception stat with default value."""
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10)
        assert hasattr(char, "perception")
        assert char.perception == 10  # Default

    def test_perception_validated_in_range(self):
        """Perception must be 1-20."""
        with pytest.raises(ValueError, match="at least 1"):
            Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=0)
        with pytest.raises(ValueError, match="at most 20"):
            Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=21)

    def test_rogue_gets_perception_bonus(self):
        """Rogues get +2 PER from class bonus."""
        # Spec: Rogues get +2 PER from class bonus
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10,
                        perception=10, character_class=CharacterClass.ROGUE)
        assert char.perception == 12  # 10 base + 2 bonus

    def test_ranger_gets_perception_bonus(self):
        """Rangers get +1 PER from class bonus."""
        # Spec: Rangers get +1 PER from class bonus
        char = Character(name="Tracker", strength=10, dexterity=10, intelligence=10,
                        perception=10, character_class=CharacterClass.RANGER)
        assert char.perception == 11  # 10 base + 1 bonus

    def test_perception_increases_on_level_up(self):
        """PER increases by 1 on level up."""
        # Spec: PER increases by 1 on level up
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=10)
        initial_per = char.perception
        char.level_up()
        assert char.perception == initial_per + 1

    def test_perception_serialization(self):
        """PER is saved and loaded correctly."""
        # Spec: PER is saved and loaded correctly
        char = Character(name="Hero", strength=10, dexterity=10, intelligence=10, perception=15)
        data = char.to_dict()
        loaded = Character.from_dict(data)
        assert loaded.perception == 15

    def test_perception_in_class_bonuses(self):
        """CLASS_BONUSES dict includes perception bonuses."""
        # Spec: Rogue +2, Ranger +1, others 0
        assert CLASS_BONUSES[CharacterClass.ROGUE].get("perception", 0) == 2
        assert CLASS_BONUSES[CharacterClass.RANGER].get("perception", 0) == 1
        assert CLASS_BONUSES[CharacterClass.WARRIOR].get("perception", 0) == 0
        assert CLASS_BONUSES[CharacterClass.MAGE].get("perception", 0) == 0
        assert CLASS_BONUSES[CharacterClass.CLERIC].get("perception", 0) == 0


class TestLocationSecrets:
    """Test hidden_secrets field on Location."""

    def test_location_has_hidden_secrets_field(self):
        """Location has hidden_secrets list."""
        # Spec: Location has hidden_secrets list, defaults to empty
        loc = Location(name="Dark Cave", description="A dark cave.")
        assert hasattr(loc, "hidden_secrets")
        assert loc.hidden_secrets == []

    def test_location_with_secrets(self):
        """Location can have secrets with thresholds."""
        # Spec: Secrets have type, description, and threshold
        secrets = [
            {"type": "hidden_door", "description": "A hidden passage", "threshold": 12},
            {"type": "hidden_treasure", "description": "A concealed chest", "threshold": 15}
        ]
        loc = Location(name="Ruins", description="Ancient ruins.", hidden_secrets=secrets)
        assert len(loc.hidden_secrets) == 2

    def test_secrets_serialization(self):
        """Secrets are saved and loaded correctly."""
        # Spec: Secrets are serialized/deserialized properly
        secrets = [{"type": "trap", "description": "Pressure plate", "threshold": 10}]
        loc = Location(name="Hall", description="A hall.", hidden_secrets=secrets)
        data = loc.to_dict()
        loaded = Location.from_dict(data)
        assert loaded.hidden_secrets == secrets


class TestPassiveDetection:
    """Test automatic secret detection on room entry."""

    def test_detects_secret_when_per_meets_threshold(self):
        """Secrets at or below PER are detected."""
        # Spec: Passive detection when PER >= threshold
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=12)
        secrets = [{"type": "hidden_door", "description": "A hidden door", "threshold": 12}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        detected = check_passive_detection(char, loc)
        assert len(detected) == 1
        assert detected[0]["description"] == "A hidden door"

    def test_misses_secret_when_per_below_threshold(self):
        """Secrets above PER are not detected."""
        # Spec: Secrets above PER are not passively detected
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=10)
        secrets = [{"type": "hidden_door", "description": "Hidden", "threshold": 15}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        detected = check_passive_detection(char, loc)
        assert len(detected) == 0

    def test_already_discovered_secrets_not_re_detected(self):
        """Once discovered, secrets don't trigger again."""
        # Spec: Discovered secrets are not re-detected
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=15)
        secrets = [{"type": "hidden_door", "description": "Door", "threshold": 10, "discovered": True}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        detected = check_passive_detection(char, loc)
        assert len(detected) == 0


class TestActiveSearch:
    """Test 'search' command mechanics."""

    def test_search_finds_undiscovered_secrets(self):
        """Active search can find secrets above passive threshold."""
        # Spec: Search gives +5 bonus to perception
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=10)
        secrets = [{"type": "hidden_treasure", "description": "Chest", "threshold": 12}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        # Search gives +5 bonus, so 10+5=15 >= 12
        found, message = perform_active_search(char, loc)
        assert found
        assert "Chest" in message

    def test_search_with_light_bonus(self):
        """Having light gives +2 to search."""
        # Spec: Light gives +2 to active search
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=10)
        char.light_remaining = 5  # Has light
        secrets = [{"type": "trap", "description": "Pit trap", "threshold": 17}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        # 10 (PER) + 5 (search) + 2 (light) = 17 >= 17
        found, message = perform_active_search(char, loc)
        assert found

    def test_search_nothing_to_find(self):
        """Search when no secrets present."""
        # Spec: Message when no secrets to find
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=10)
        loc = Location(name="Room", description="A room.")

        found, message = perform_active_search(char, loc)
        assert not found
        assert "nothing" in message.lower()

    def test_search_marks_secret_as_discovered(self):
        """Active search marks found secrets as discovered."""
        # Spec: Discovered secrets marked to prevent re-discovery
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=10)
        secrets = [{"type": "hidden_treasure", "description": "Gold", "threshold": 10}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        # First search finds it
        found, _ = perform_active_search(char, loc)
        assert found
        assert secrets[0].get("discovered") is True

        # Second search finds nothing (already discovered)
        found2, message2 = perform_active_search(char, loc)
        assert not found2
        assert "nothing" in message2.lower() or "unusual" in message2.lower()

    def test_search_cannot_find_high_threshold_secret(self):
        """Search fails for secrets with threshold too high."""
        # Spec: Still can't find secrets with threshold > PER + bonuses
        char = Character(name="Scout", strength=10, dexterity=10, intelligence=10, perception=10)
        secrets = [{"type": "trap", "description": "Deadly trap", "threshold": 20}]
        loc = Location(name="Room", description="A room.", hidden_secrets=secrets)

        # 10 (PER) + 5 (search) = 15 < 20
        found, message = perform_active_search(char, loc)
        assert not found
        assert "unusual" in message.lower()  # "don't notice anything unusual"
