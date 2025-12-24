Game generates a world when starting which only has three locations and the player is getting stuck:

$> cli-rpg

==================================================
Welcome to CLI RPG!
==================================================

✓ AI world generation enabled!
  Set OPENAI_API_KEY to use AI features.

==================================================
MAIN MENU
==================================================
1. Create New Character
2. Load Character
3. Exit
==================================================
Enter your choice: 2

⚠ No saved characters found.
  Create a new character first!

==================================================
MAIN MENU
==================================================
1. Create New Character
2. Load Character
3. Exit
==================================================
Enter your choice: 1

==================================================
CHARACTER CREATION
==================================================

Enter character name (2-30 characters, or 'cancel' to exit):
> asdfjkl

Choose stat allocation method:
1. Manual - Choose your own stats
2. Random - Randomly generate balanced stats
Type 'cancel' to exit
> 2

Randomly generated stats:
Strength: 11
Dexterity: 10
Intelligence: 14

==================================================
CHARACTER SUMMARY
==================================================
asdfjkl (Level 1) - Alive
Health: 155/155
Strength: 11 | Dexterity: 10 | Intelligence: 14
==================================================

Confirm character creation? (yes/no):
> yes

✓ asdfjkl has been created successfully!

==================================================
THEME SELECTION
==================================================
Select world theme (or press Enter for default 'fantasy'):
1. Fantasy (default)
2. Sci-Fi
3. Cyberpunk
4. Horror
5. Steampunk
6. Custom
==================================================
> 4

✓ Selected theme: horror
Your character is ready for adventure!

==================================================
Welcome to the adventure, asdfjkl!
Exploring a horror world powered by AI...
==================================================

Exploration Commands:
  look          - Look around at your surroundings
  go <direction> - Move in a direction (north, south, east, west)
  status        - View your character status
  save          - Save your game (not available during combat)
  quit          - Return to main menu

Combat Commands:
  attack        - Attack the enemy
  defend        - Take a defensive stance
  flee          - Attempt to flee from combat
  status        - View combat status
==================================================

Cursed Crypt
An ancient underground crypt filled with eerie whispers and chilling drafts. The walls are lined with decaying corpses, their eyes following your every move.
Exits: east, up

> go up

You head up to Haunted Tower.

Haunted Tower
A looming tower shrouded in mist, its windows glowing with an eerie light. Shadows dance along the walls, and whispers echo through the halls.
Exits: down

> go down

You head down to Cursed Crypt.

Cursed Crypt
An ancient underground crypt filled with eerie whispers and chilling drafts. The walls are lined with decaying corpses, their eyes following your every move.
Exits: east, up

> go east

You head east to Darkwood Manor.

Darkwood Manor
An eerie Victorian mansion surrounded by twisted trees and overgrown foliage. Shadows seem to move within its walls, and whispers echo through the halls.
Exits: west

> go west

You head west to Cursed Crypt.

Cursed Crypt
An ancient underground crypt filled with eerie whispers and chilling drafts. The walls are lined with decaying corpses, their eyes following your every move.
Exits: east, up

>
