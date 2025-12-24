"""Tests to verify documentation accuracy."""
import re


def test_readme_character_creation_accuracy():
    """Verify README accurately describes character creation stats.
    
    Tests that README.md:
    - Lists only 3 customizable stats (strength, dexterity, intelligence)
    - Does NOT list constitution as a customizable stat in character creation
    - Clarifies constitution is derived or auto-calculated
    """
    with open("README.md", "r") as f:
        readme_content = f.read()
    
    # Find the character creation section
    creation_section = ""
    lines = readme_content.split("\n")
    in_creation_section = False
    for i, line in enumerate(lines):
        if "### Character Creation" in line:
            in_creation_section = True
            # Capture until next ### section or end
            for j in range(i, len(lines)):
                if j > i and lines[j].startswith("###"):
                    break
                creation_section += lines[j] + "\n"
            break
    
    assert creation_section, "Character Creation section not found in README"
    
    # Test: Constitution should NOT be listed as a customizable stat in character creation section
    # Look for patterns like "- **Constitution**:" in the character creation section
    constitution_as_stat = re.search(r'^\s*-\s*\*\*Constitution\*\*:', creation_section, re.MULTILINE)
    assert constitution_as_stat is None, (
        "Constitution should not be listed as a customizable stat in Character Creation section. "
        "It is derived from strength."
    )
    
    # Test: Strength, Dexterity, Intelligence should be mentioned
    assert "Strength" in creation_section, "Strength should be mentioned in Character Creation"
    assert "Dexterity" in creation_section, "Dexterity should be mentioned in Character Creation"
    assert "Intelligence" in creation_section, "Intelligence should be mentioned in Character Creation"
    
    # Test: Constitution should be mentioned as derived/automatic
    # Look for constitution being mentioned in context of being derived or automatic
    constitution_mentioned = "constitution" in creation_section.lower()
    if constitution_mentioned:
        # If mentioned, it should be in a note or clarification context
        assert (
            "derived" in creation_section.lower() or 
            "automatically" in creation_section.lower() or
            "calculated" in creation_section.lower()
        ), "If constitution is mentioned, it should be described as derived/automatic"


def test_readme_no_four_attributes_claim():
    """Verify README does not claim four attributes are customizable.
    
    Tests that README.md:
    - Does NOT claim "four attributes" in character creation context
    - Does NOT mention "30 stat points" (from old system)
    """
    with open("README.md", "r") as f:
        readme_content = f.read()
    
    # Find character creation related sections (both features and gameplay)
    creation_related_text = ""
    lines = readme_content.split("\n")
    
    # Get the Features section
    for i, line in enumerate(lines):
        if "## Features" in line:
            for j in range(i, min(i + 20, len(lines))):
                if lines[j].startswith("##") and j > i:
                    break
                creation_related_text += lines[j] + "\n"
            break
    
    # Get the Character Creation section
    for i, line in enumerate(lines):
        if "### Character Creation" in line:
            for j in range(i, len(lines)):
                if j > i and lines[j].startswith("###"):
                    break
                creation_related_text += lines[j] + "\n"
            break
    
    # Test: Should not mention "four attributes" in character creation context
    # Look for patterns like "four attributes", "4 attributes"
    four_attrs_pattern = re.search(r'\bfour\s+attributes\b|\b4\s+attributes\b', 
                                   creation_related_text, re.IGNORECASE)
    assert four_attrs_pattern is None, (
        "README should not claim 'four attributes' are customizable. "
        "Only three attributes (strength, dexterity, intelligence) are customizable."
    )
    
    # Test: Should not mention "30 stat points" (old point distribution system)
    thirty_points_pattern = re.search(r'\b30\s+stat\s+points\b', 
                                     creation_related_text, re.IGNORECASE)
    assert thirty_points_pattern is None, (
        "README should not mention '30 stat points'. "
        "The actual system allows choosing 1-20 for each of three stats."
    )


def test_readme_features_section_accuracy():
    """Verify Features section lists only three customizable attributes.
    
    Tests that the quick features list at the top of README accurately
    describes the character creation system.
    """
    with open("README.md", "r") as f:
        readme_content = f.read()
    
    # Find the Features section
    features_section = ""
    lines = readme_content.split("\n")
    in_features = False
    for i, line in enumerate(lines):
        if "## Features" in line:
            in_features = True
            for j in range(i, len(lines)):
                if j > i and lines[j].startswith("##"):
                    break
                features_section += lines[j] + "\n"
            break
    
    assert features_section, "Features section not found in README"
    
    # Find the Character Creation bullet point
    char_creation_line = ""
    for line in features_section.split("\n"):
        if "Character Creation" in line:
            char_creation_line = line
            break
    
    assert char_creation_line, "Character Creation feature not found in Features section"
    
    # Test: Should NOT mention constitution as a customizable attribute
    # Pattern: (attribute1, attribute2, constitution, attribute3)
    if "constitution" in char_creation_line.lower():
        # If constitution is mentioned, fail the test
        assert False, (
            "Features section should not list constitution as a customizable attribute. "
            "Found: " + char_creation_line
        )
    
    # Test: Should mention the three actual customizable attributes
    assert "strength" in char_creation_line.lower(), "Strength should be in Character Creation feature"
    assert "dexterity" in char_creation_line.lower(), "Dexterity should be in Character Creation feature"
    assert "intelligence" in char_creation_line.lower(), "Intelligence should be in Character Creation feature"
