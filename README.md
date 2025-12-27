# CLI RPG

A CLI-based role-playing game with AI-generated worlds and turn-based combat. The entire game world is generated on-the-fly using AI and persisted, allowing for endless exploration.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run the game
python -m cli_rpg.main
```

## Features

- **Character Creation**: Create custom characters with 5 classes (Warrior, Mage, Rogue, Ranger, Cleric) and customizable attributes (strength, dexterity, intelligence, charisma, perception, luck). Mages have a larger mana pool for casting spells; Warriors and Rangers have larger stamina pools for physical abilities
- **AI-Generated Worlds**: Dynamically generated locations using OpenAI, Anthropic, or Ollama local models (optional)
- **Turn-Based Combat**: Engage enemies with attack, defend, and flee commands
- **Inventory & Equipment**: Collect loot from defeated enemies, equip weapons and armor, use consumables
- **NPC Shops**: Interact with merchants, buy equipment, and sell items for gold
- **AI-Generated Dialogue**: NPCs feature contextual AI-generated conversations that persist across sessions
- **Gold Economy**: Earn gold from combat victories, spend it at shops
- **Persistent Saves**: Save and load complete game progress including world state, location, and theme
- **Day/Night Cycle**: Time advances as you explore (movement: +1 hour, rest: +4 hours). Night brings eerie whispers and some NPCs/shops may be unavailable
- **Seasons & Festivals**: A 120-day year with four seasons (Spring, Summer, Autumn, Winter). Seasonal dread modifiers affect gameplay, and special festivals occur throughout the year offering unique bonuses like shop discounts, XP boosts, and more
- **Weather System**: Dynamic weather (clear, rain, storm, fog) affects gameplay with dread modifiers, storm travel delays, and visibility effects. Storms reduce visibility (truncated descriptions, hidden details). Fog obscures some exits (50% chance each). Underground locations (caves) are sheltered from weather effects. Weather also affects combat: rain/storms can extinguish Burn effects (40% chance per turn), and storms extend Freeze duration (+1 turn when applied).
- **Dread System**: Psychological horror element that tracks your fear level (0-100%). Dangerous areas build dread; high dread causes paranoid whispers and combat penalties. At 75-99% dread, hallucinations may appear during travel (30% chance) - spectral enemies that dissipate when attacked, providing catharsis (-5 dread) but no rewards. At 100% dread, a Shadow Creature manifests and attacks you - defeating it reduces your dread by 50%. Reduce dread by resting, visiting towns, or talking to NPCs. Light sources (e.g., Torches from merchants) reduce dread buildup by 50% and negate the night dread bonus while active. **Dread Treasures**: Brave players who maintain 75%+ dread may discover powerful treasures when examining their surroundings (30% chance on 3rd+ look) - including Shadow Essence, Veil of Courage, Dread Blade, and Darklight Torch.
- **Grid-Based World**: Navigate a spatially consistent world where directions are reliable (going north then south returns you to the same place)
- **Procedural Terrain Generation**: Wave Function Collapse (WFC) terrain generation is enabled by default, providing coherent, infinite terrain with forests, mountains, water, and more. Terrain types affect location generation and some terrain (like water) may be impassable. Use `--no-wfc` to disable.
- **Lockpicking & Treasure Chests**: Rogues can pick locked chests using DEX-based skill checks. Treasure chests contain valuable items and can be found throughout the world
- **Secret Discovery**: Use the `search` command to actively search for hidden secrets. Perception (PER) stat determines what you can find - hidden doors, buried treasure, traps, and lore hints await observant players
- **Experience System**: Level up by defeating enemies
- **Colorized Output**: Color-coded terminal output for improved readability (enemies in red, locations in cyan, items in green, etc.)
- **Tab Completion**: Auto-complete commands and contextual arguments (directions, NPCs, items) with Tab key
- **Command History**: Navigate previous commands with up/down arrow keys (persists across sessions)

## Gameplay

### Character Creation
1. Choose a name for your character
2. Choose a character class (each provides stat bonuses):
   - **Warrior**: +3 STR, +1 DEX - melee combat specialists
   - **Mage**: +3 INT, +1 DEX - magic damage dealers
   - **Rogue**: +3 DEX, +1 STR, +1 CHA, +2 PER, +2 LCK - agile fighters with stealth (combat and exploration), backstab, and lockpicking abilities
   - **Ranger**: +2 DEX, +1 STR, +1 INT, +1 PER, +1 LCK - wilderness specialists with tracking abilities and +15% damage in forest/wilderness
   - **Cleric**: +2 INT, +1 STR, +2 CHA - hybrid support class
3. Choose your stat allocation method (manual or random)
4. Set your six core attributes (1-20 each):
   - **Strength**: Increases attack damage and max HP
   - **Dexterity**: Improves flee chance, dodge chance, and physical critical hit chance
   - **Intelligence**: Increases magic attack damage and magic critical hit chance
   - **Charisma**: Affects shop prices, persuasion, intimidation, and bribery
   - **Perception**: Determines ability to detect hidden secrets, traps, and environmental details
   - **Luck**: Influences critical hit chance, loot drop rates, loot quality, and gold rewards

**Note:** Constitution is automatically derived from your Strength stat and is used to reduce incoming damage during combat. Class bonuses are applied after your base stat allocation.

### Exploration Commands
- `look` (l) - Examine your current location (use multiple times to reveal environmental details and hidden secrets)
- `search` (sr) - Actively search the area for hidden secrets (PER-based check with +5 bonus; light sources provide additional +2)
- `go <direction>` (g) - Move in a direction (north, south, east, west)
  - Quick shortcuts: `n`, `gn` (north), `w`, `gw` (west), `gs` (south), `ge` (east)
  - Note: `s` runs `status` and `e` runs `equip`, so use `gs`/`ge` for south/east
- `enter <location>` - Enter a sub-location within the current overworld landmark (e.g., enter a tavern within a city)
- `exit` / `leave` - Exit from a sub-location back to its parent overworld landmark
- `map` (m) - Display an ASCII map of explored locations with available exits
- `worldmap` (wm) - Display the overworld map (shows only overworld landmarks)
- `status` (s, stats) - View your character's stats, gold, XP progress, current time, and weather
- `inventory` (i) - View your inventory and equipped items
- `equip <item name>` (e) - Equip a weapon or armor from your inventory
- `unequip weapon|armor` - Unequip from the specified slot and return to inventory
- `use <item name>` (u) - Use a consumable item (e.g., health potion)
- `talk [npc]` (t) - Talk to an NPC (opens shop if merchant, shows quests if quest-giver, or enter extended conversation). If only one NPC is present, starts conversation automatically. If multiple NPCs are present, lists available NPCs.
- `accept <quest>` - Accept a quest from the NPC you're talking to
- `shop` - View the current merchant's inventory and prices
- `buy <item>` - Purchase an item from the current shop
- `sell <item>` - Sell an item from your inventory for gold
- `persuade` - Attempt to persuade the current NPC (grants 20% shop discount on success)
- `intimidate` - Attempt to intimidate the current NPC (success based on CHA and kills)
- `bribe <amount>` - Attempt to bribe the current NPC with gold
- `haggle` - Negotiate better prices with merchant (CHA-based, one transaction)
- `drop <item>` (dr) - Drop an item from your inventory (cannot drop equipped items)
- `pick <chest>` (lp) - **Rogue only**: Attempt to pick the lock on a treasure chest (requires Lockpick item)
- `open <chest>` (o) - Open an unlocked treasure chest to collect its contents
- `quests` (q) - View your quest journal with all active and completed quests
- `quest <name>` - View details of a specific quest (supports partial matching)
- `complete <quest>` - Turn in a completed quest to the NPC you're talking to
- `abandon <quest>` - Abandon an active quest from your journal
- `lore` - Discover AI-generated lore snippets about your current location
- `bestiary` (b) - View all defeated enemies with ASCII art, kill counts, and stats
- `proficiency` (prof) - View your weapon proficiency levels, XP progress, and damage bonuses
- `reputation` (rep) - View your standing with discovered factions
- `companions` - View your party members with bond levels
- `recruit <npc>` - Recruit a willing NPC to join your party
- `dismiss <name>` - Dismiss a companion from your party (requires confirmation; high-bond companions show warning)
- `companion-quest <name>` - Accept a companion's personal quest (requires TRUSTED bond level)
- `dump-state` - Export complete game state as JSON for programmatic inspection
- `sneak` (sn) - **Rogue only**: Move stealthily to avoid random encounters (costs 10 stamina). Success chance: 50% + (DEX × 2%) - (armor defense × 5%) - (15% if lit), capped 10-90%. Effect consumed on next move.
- `rest` (r) - Rest to recover health and stamina (restores 25% of max HP and 25% of max stamina, advances time by 4 hours, reduces dread, may trigger dreams; not available during combat). Use `rest --quick` or `rest -q` to skip the dream check entirely.
- `camp` (ca) - Set up camp in wilderness areas (requires Camping Supplies; heals 50% HP, reduces dread by 30-40, advances time 8 hours; campfire cooks raw meat and may attract friendly visitors)
- `forage` (fg) - Search for herbs and berries (forest/wilderness only; PER-based success chance; 1-hour cooldown)
- `hunt` (hu) - Hunt game for meat and pelts (forest/wilderness only; DEX/PER-based success chance; 2-hour cooldown)
- `track` (tr) - **Ranger only**: Detect enemies in adjacent locations (costs 10 stamina; success rate: 50% + 3% per PER point)
- `gather` (ga) - Gather resources in wilderness areas (forest/wilderness yields wood and fiber; cave/dungeon yields iron ore and stone; PER-based success chance; 1-hour cooldown)
- `recipes` - View all available crafting recipes with their ingredients
- `craft <recipe>` (cr) - Craft an item from gathered resources (e.g., `craft torch`, `craft iron sword`)
- `events` - View active world events and their status
- `resolve [event]` - Attempt to resolve an active world event (without args: lists events with requirements)
- `save` - Save complete game state including world, location, and theme (not available during combat)
- `help` (h) - Display the full command reference
- `quit` - Exit to main menu

### World Events
The world is alive with timed events that progress with in-game time:

- **Caravans**: Trading caravans pass through locations, providing a temporary shop with exotic items (use `shop` command to access)
- **Plagues**: Disease outbreaks spread through affected areas, creating urgency
- **Invasions**: Hostile forces threaten locations, requiring player intervention

Events have limited duration and consequences if not resolved. Use the `events` command to view active events and their time remaining. When entering a location affected by an event, you'll receive a warning. Events persist across save/load.

**Resolving Events**: Use the `resolve <event>` command to attempt to resolve active events:

| Event Type | Resolution Method | Requirements | Rewards |
|------------|-------------------|--------------|---------|
| Plague | `resolve <event>` | Cure item in inventory, at affected location | 50 XP, 30 gold |
| Invasion | `resolve <event>` | At affected location | Combat encounter → 75 XP, 50 gold on victory |
| Caravan | Use `shop` to browse, `buy` to purchase | At affected location | Access exotic items (spices, elixirs, maps) |

**Cure Items**: Cure items (Antidote, Cure Vial, Purification Elixir) can be found as loot drops from defeated enemies (15% chance when consumables drop) or purchased from merchants.

### Random Travel Encounters
When moving between locations, you have a 15% chance to trigger a random encounter:
- **Hostile Encounters** (60%): Wandering enemies ambush you, immediately starting combat
- **Merchant Encounters** (25%): A traveling merchant appears with 2-3 items for sale (use `talk` to shop)
- **Wanderer Encounters** (15%): A mysterious traveler offers lore and atmosphere (use `talk` to converse)

Merchants and wanderers are added to your current location and can be interacted with normally.

**Safe Zones**: Towns, villages, and other safe locations (marked as `is_safe_zone`) are protected from random encounters, allowing you to shop and rest without interruption.

**Rogue Sneak**: Rogues can use the `sneak` command before moving to attempt to avoid random encounters. Success depends on DEX, armor weight, and whether carrying a light source.

### Combat System
Combat encounters occur randomly as you explore. You may face multiple enemies at once (1-2 enemies at lower levels, up to 3 at level 4+). Enemies display ASCII art when combat begins.

**Distance-Based Difficulty**: Enemy difficulty scales based on how far you've traveled from the starting location (0,0). The further you explore, the stronger the enemies:
- Near spawn (0-3 tiles): Easy encounters for new players
- Mid-range (4-7 tiles): Moderate difficulty
- Far reaches (8-12 tiles): Challenging encounters
- Deep wilderness (13+ tiles): Dangerous, high-risk high-reward

Enemy stats (HP, attack, defense) and XP rewards all scale with distance, encouraging strategic exploration and progression.

**Boss Fights**: Occasionally, you'll encounter powerful boss enemies with enhanced stats (2x health, attack, and defense) and 4x XP rewards. Bosses are guaranteed to drop legendary loot with enhanced stats upon defeat. Boss types vary by location category (Lich Lords in dungeons, Ancient Guardians in ruins, Cave Troll Kings in caves, etc.).

**Telegraphed Attacks**: Boss enemies have powerful special attacks that are telegraphed one turn in advance. When you see a warning like "The Stone Sentinel raises its massive fist high above its head...", prepare for a devastating strike next turn. Special attacks deal 1.5x-2x damage and may inflict status effects (stun, poison, freeze). Use `defend` (50% reduction) or `block` (75% reduction) to mitigate incoming damage from these powerful attacks.

**Critical Hits & Dodge**: Combat includes critical hit and dodge mechanics:
- **Player Critical Hits**: Base 5% chance + 1% per DEX (physical) or INT (magic) + 0.5% per LCK from 10, capped at 20%. Crits deal 1.5x damage.
- **Player Dodge**: Base 5% chance + 0.5% per DEX, capped at 15%. Successful dodge negates all damage from an attack.
- **Enemy Critical Hits**: Flat 5% chance for enemies, dealing 1.5x damage.

**Loot & Gold**: Your Luck stat affects combat rewards:
- **Loot Drop Rate**: Base 50% chance, modified by ±2% per LCK point from 10
- **Loot Quality**: Weapon/armor bonuses gain +1 per 5 LCK above 10
- **Gold Rewards**: Modified by ±5% per LCK point from 10

**Weapon Proficiencies**: Using weapons builds proficiency with that weapon type, granting damage bonuses:
- **Weapon Types**: Sword, Axe, Dagger, Mace, Bow, Staff
- **Proficiency Levels**: Novice → Apprentice → Journeyman → Expert → Master
- **XP Per Attack**: 1 XP gained per attack with an equipped weapon
- **Damage Bonuses**: Novice +0%, Apprentice +5%, Journeyman +10%, Expert +15%, Master +20%
- Use `proficiency` command to view your progress with each weapon type

**Status Effects**: Some enemies can inflict status effects during combat:
- **Poison**: Certain creatures (spiders, snakes, serpents, vipers) have a chance to poison you on attack. Poison deals damage each turn and wears off after a set duration.
- **Burn**: Fire-based enemies (fire elementals, dragons, flame creatures) can inflict burn, dealing damage over time for 2 turns.
- **Bleed**: Slashing enemies (wolves, bears, lions, claw/fang-based creatures) can cause bleeding wounds, dealing 3 damage per turn for 4 turns.
- **Stun**: Heavy-hitting enemies (trolls, golems, giants, hammer-wielders) can stun you, causing you to skip your next action.
- **Freeze**: Ice-themed enemies (yetis, frost creatures) can freeze you or themselves, reducing attack damage by 50% while frozen.

Status effects are cleared when combat ends.

**Combat Commands:**
- `attack [target]` (a) - Attack an enemy (damage based on your strength vs enemy defense). Specify a target name when facing multiple enemies, or attacks the first living enemy.
- `defend` (d) - Take a defensive stance, reducing incoming damage by 50% from all enemies
- `block` (bl) - Take a blocking stance for stronger defense (costs 5 stamina, reduces incoming damage by 75%)
- `parry` (pa) - Attempt to parry and counter-attack (costs 8 stamina, 40% + DEX×2% success capped at 70%; success negates damage and counters for 50% of your attack power; failure takes full damage)
- `stance [style]` (st) - View or change your fighting stance. Available stances:
  - **Balanced** (default): +5% critical hit chance
  - **Aggressive**: +20% damage dealt, -10% defense
  - **Defensive**: -10% damage dealt, +20% defense
  - **Berserker**: Damage scales with missing HP (up to +50% at low health)
- `flee` (f) - Attempt to escape (chance based on dexterity)
- `cast [target]` (c) - Cast a magic attack at an enemy (costs 10 mana, damage based on intelligence). Targeting works like `attack`.
- `fireball [target]` (fb) - **Mage only**: Hurl a fireball at an enemy (costs 20 mana). Deals INT × 2.5 damage (ignores defense), 25% chance to inflict Burn (5 damage/turn for 2 turns). Deals 1.5x damage to ICE enemies (yetis, frost creatures), 0.5x to FIRE enemies (dragons, fire elementals). Targeting works like `attack`.
- `ice_bolt [target]` (ib) - **Mage only**: Launch an ice bolt at an enemy (costs 15 mana). Deals INT × 2.0 damage (ignores defense), 30% chance to inflict Freeze (50% attack reduction for 2 turns). Deals 1.5x damage to FIRE enemies, 0.5x to ICE enemies. Targeting works like `attack`.
- `heal` (hl) - **Mage only**: Cast a healing spell on yourself (costs 25 mana). Restores INT × 2 HP (capped at max health).
- `bash [target]` (ba) - **Warrior only**: Shield bash an enemy (costs 15 stamina). Deals 0.75x STR-based damage but stuns the target for 1 turn. Targeting works like `attack`.
- `sneak` (sn) - **Rogue only**: Enter stealth mode for 1 turn (costs 10 stamina). Next attack deals 1.5x backstab damage. Higher DEX increases dodge chance while stealthed (DEX × 5%, capped at 75%). Stealth breaks if you take damage.
- `hide` (hd) - Become hidden for 1 turn (costs 10 stamina). While hidden, enemies skip attacking you. The effect expires after the enemy turn.
- `bless` (bs) - **Cleric only**: Bless your party (costs 20 mana). Grants "Blessed" status effect (+25% attack damage) for 3 turns to player and all companions.
- `smite [target]` (sm) - **Cleric only**: Channel holy energy at an enemy (costs 15 mana). Deals INT × 2.5 damage (ignores defense), or INT × 5.0 damage against undead. 30% chance to stun undead for 1 turn. Targeting works like `attack`.
- `use <item>` (u) - Use a consumable item (e.g., health potion) - counts as your turn
- `status` (s, stats) - View combat status (HP of you and all enemies, action history, pending combos)
- `help` (h) - Display the full command reference
- `quit` - Exit to main menu (no save during combat - combat progress will be lost)

**Combo System**: Chain specific action sequences to unlock powerful combo attacks:
- **Frenzy** (Attack → Attack → Attack): Triple hit dealing ~1.5x total damage
- **Revenge** (Defend → Defend → Attack): Counter-attack dealing damage equal to damage taken while defending
- **Arcane Burst** (Cast → Cast → Cast): Empowered spell dealing 2x magic damage (costs 25 mana total)

The combat status shows your last actions (e.g., "Last actions: [Attack] → [Defend]"). When a combo pattern is complete, you'll see "COMBO AVAILABLE: Frenzy! (Type 'frenzy' to use)" - type the combo name to trigger it. Fleeing clears your action history.

**Targeting:** When facing multiple enemies, you can target specific enemies by name (e.g., `attack goblin` or `cast orc`). Partial, case-insensitive matching is supported. If no target is specified, attacks hit the first living enemy.

**Ranger Wilderness Bonus:** Rangers receive +15% attack damage when fighting in forest or wilderness locations. This bonus is applied automatically during combat.

**Companion Combat Bonus:** Companions in your party provide passive attack damage bonuses based on their bond level:
- STRANGER (0-24 points): No bonus
- ACQUAINTANCE (25-49 points): +3% attack damage
- TRUSTED (50-74 points): +5% attack damage
- DEVOTED (75-100 points): +10% attack damage

Multiple companions stack their bonuses additively. The bonus appears in combat status when greater than 0%.

**Companion Personal Quests:** Companions with high bond levels may have personal quests you can undertake:
- Use `companion-quest <name>` to accept a companion's personal quest (requires TRUSTED or DEVOTED bond)
- Complete the quest objectives as normal
- Turn in the quest with `complete <quest>` to earn standard rewards plus a +15 bond bonus

**Companion Reactions:** Companions react to your combat choices based on their personality:
- **Warrior** companions approve of killing enemies (+3 bond) but disapprove of fleeing (-3 bond)
- **Pacifist** companions disapprove of killing enemies (-3 bond) but approve of fleeing (+3 bond)
- **Pragmatic** companions remain neutral to all combat choices (no bond change)

Companion reactions appear as flavor text after combat resolution.

**Combat Flow:**
1. You attack, defend, or cast
2. All living enemies attack (unless you fled successfully)
3. Combat continues until all enemies are defeated, you are defeated, or you successfully flee

**Victory**: Gain XP and gold, potentially level up, and may receive loot drops
**Defeat**: Game over (can restore health for testing)
**Flee**: Escape without gaining XP, gold, or loot

**Faction Reputation:** Defeating certain enemies affects your standing with factions:
- **Bandit-type enemies** (bandits, thieves, ruffians, outlaws): -5 reputation with Thieves Guild, +3 with Town Guard
- **Guard-type enemies** (guards, soldiers, knights, captains): -5 reputation with Town Guard, +3 with Thieves Guild
- Reputation changes are shown after combat victory

### Inventory & Equipment

Defeated enemies have a chance to drop loot. Items include:
- **Weapons**: Increase attack damage when equipped
- **Armor**: Reduce incoming damage when equipped
- **Consumables**: Health potions that restore HP, mana potions that restore mana, stamina potions that restore stamina
- **Misc Items**: Flavor items like gold coins and monster parts

Your inventory has a capacity of 20 items. Use `inventory` to view your items, `equip <item>` to equip weapons/armor, `unequip weapon|armor` to remove equipment, and `use <item>` for consumables. Equipped items apply their bonuses automatically during combat.

### NPC Shops

Merchants can be found throughout the world. Interact with them to buy and sell items:

1. Use `look` to see NPCs in your location
2. Use `shop` to view available items and prices (auto-detects merchant in location)
3. Use `buy <item>` to purchase items (requires sufficient gold)
4. Use `sell <item>` to sell items from your inventory for gold
5. Optionally use `talk <npc>` to chat with a merchant before shopping

**Earning Gold**: Defeat enemies in combat to earn gold (5-15 × enemy level per victory).

**Charisma Price Modifier**: Your Charisma stat affects shop prices. Higher CHA reduces buy prices and increases sell prices (±1% per point from 10).

**Merchant Guild Reputation**: Your standing with the Merchant Guild faction affects shop prices:
- **HOSTILE** (1-19): Merchants refuse to trade with you
- **UNFRIENDLY** (20-39): +15% buy prices, -15% sell prices
- **NEUTRAL** (40-59): Standard prices (no modifier)
- **FRIENDLY** (60-79): -10% buy prices, +10% sell prices
- **HONORED** (80-100): -20% buy prices, +20% sell prices

Faction modifiers stack multiplicatively with CHA modifiers.

### Social Skills

Use social skills to influence NPCs during conversations:

1. **Persuade**: Use `persuade` while talking to an NPC
   - Success chance: 30% + (CHA × 3%), capped at 90%
   - On success: Grants 20% discount at merchant shops
   - NPCs can only be persuaded once per session

2. **Intimidate**: Use `intimidate` while talking to an NPC
   - Success chance: 20% + (CHA × 2%) + (kills × 5%), capped at 85%
   - NPC willpower reduces your chance (1-10 scale)
   - On success: Same effect as persuasion (20% discount)

3. **Bribe**: Use `bribe <amount>` while talking to an NPC
   - Required amount: 50 - (CHA × 2) gold, minimum 10 gold
   - Not all NPCs are bribeable
   - On success: Gold is deducted, same effect as persuasion

4. **Haggle**: Use `haggle` while at a shop to negotiate prices
   - Success chance: 25% + (CHA × 2%) + 15% if persuaded, capped at 85%
   - On success: 15% bonus on your next buy or sell transaction
   - On critical success (roll ≤ 10% of success chance): 25% bonus
   - On critical failure (roll ≥ 95): Merchant refuses to haggle for 3 turns
   - Bonus is consumed after one transaction (buy or sell)

### NPC Quests

Quest-giver NPCs can be found throughout the world. Interact with them to receive quests:

1. Use `look` to see NPCs in your location
2. Use `talk <npc>` to interact with a quest-giver and see available quests
3. Use `accept <quest>` to accept a quest (partial matching supported)
4. Use `quests` to view your quest journal (shows active, ready to turn in, and completed quests)

**Quest Progress**: Quests automatically track your progress:
- **Kill quests**: Progress updates when you defeat matching enemies in combat
- **Collect quests**: Progress updates when you acquire matching items (from combat loot or shop purchases)
- **Drop quests**: Progress updates when you defeat a specific enemy AND it drops a specific item (e.g., "Collect 3 Wolf Pelts from Wolves")
- **Explore quests**: Progress updates when you visit matching locations
- **Talk quests**: Progress updates when you talk to matching NPCs
- **Use quests**: Progress updates when you use matching consumable items (e.g., "Use a Health Potion")

You'll see progress messages after each relevant action.

**Turning In Quests**: When quest objectives are complete, you must return to the quest giver:
1. Travel back to the NPC who gave you the quest
2. Use `talk <npc>` to interact with them (shows quests ready to turn in)
3. Use `complete <quest>` to claim your rewards

**Quest Rewards**: Rewards are granted when you turn in a quest:
- **Gold**: Added directly to your gold total
- **XP**: Grants experience points (may trigger level-ups)
- **Items**: Quest reward items are added to your inventory
- **Faction Reputation**: Some quests are affiliated with factions and grant reputation bonuses (or penalties to rival factions) on completion

**Faction-Affiliated Quests**: Some quests require a minimum reputation with a faction before they can be accepted. If your standing is too low, the NPC will refuse to give you the quest until you improve your reputation.

**Quest Chains**: Some quests are part of multi-part story chains that must be completed in order:
- Use `quest <name>` to view chain information (e.g., "Chain: goblin_war (Part 2)")
- Quests with prerequisites cannot be accepted until required quests are completed
- The game will show which prerequisite quests you still need to complete

**Note**: You must talk to an NPC before accepting or completing their quests. Quest names are matched case-insensitively.

### Save System

The game supports automatic and manual saving:

**Autosave**
- Game automatically saves after key events:
  - Moving to a new location
  - Winning combat
  - Successfully fleeing from combat
- Uses a single autosave slot per character (`autosave_{name}.json`)
- Silent operation - never interrupts gameplay

**Manual Saves** (Full Game State)
- Use the `save` command during gameplay
- Saves complete game progress including:
  - Character stats and progress
  - Entire world structure and locations
  - Current location where you left off
  - Theme setting for consistent AI generation
- Resume exactly where you left off with full world intact

**Character-Only Saves** (Legacy)
- Older save format containing only character data
- Fully supported for backward compatibility
- Loading these saves starts a new adventure with the saved character
- Original saves work without any modification needed

### AI World Generation (Optional)

Enable dynamic world generation with AI using OpenAI, Anthropic, or Ollama (local):

**Option 1: OpenAI**
1. Get an API key from [platform.openai.com](https://platform.openai.com/)
2. Create a `.env` file:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

**Option 2: Anthropic**
1. Get an API key from [console.anthropic.com](https://console.anthropic.com/)
2. Create a `.env` file:
   ```bash
   ANTHROPIC_API_KEY=your-api-key-here
   ```

**Option 3: Ollama (Local - Free, No API Key)**
1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model: `ollama pull llama3.2`
3. Start the server: `ollama serve`
4. Create a `.env` file:
   ```bash
   AI_PROVIDER=ollama
   ```

**Multiple providers configured?** Anthropic is used by default. Set `AI_PROVIDER=openai` or `AI_PROVIDER=ollama` to override.

3. Select a theme when creating a new character (fantasy, sci-fi, cyberpunk, etc.)

**Strict Mode (Default)**: If AI generation fails, you'll be prompted with options to retry, use the default world, or return to the main menu. To enable silent fallback (no prompts), set `CLI_RPG_REQUIRE_AI=false` in your `.env` file.

See [docs/AI_FEATURES.md](docs/AI_FEATURES.md) for detailed AI configuration.

### Disabling Colors

Colors are enabled by default for terminals that support ANSI escape codes. To disable colorized output:

```bash
CLI_RPG_NO_COLOR=true cli-rpg
```

Or add to your `.env` file:
```bash
CLI_RPG_NO_COLOR=true
```

### Procedural Terrain (WFC Mode)

Wave Function Collapse terrain generation is **enabled by default**, providing coherent, infinite world terrain.

To disable WFC and use the fixed world instead:

```bash
cli-rpg --no-wfc
```

**Features:**
- Generates coherent terrain using Wave Function Collapse algorithm
- Terrain types: plains, forest, mountain, water, desert, swamp, tundra, volcanic, ruins
- Terrain affects location theming (forests generate forest locations, etc.)
- Water terrain is impassable - find another route
- Terrain persists across save/load
- Works with all other game modes and flags (interactive, non-interactive, JSON)

### Non-Interactive Mode

For automated testing and AI agent playtesting, use the `--non-interactive` flag to read commands from stdin:

```bash
# Single command
echo "look" | cli-rpg --non-interactive

# Multiple commands
echo -e "look\nstatus\ninventory" | cli-rpg --non-interactive

# From file
cli-rpg --non-interactive < commands.txt

# Reproducible runs with fixed seed
cli-rpg --non-interactive --seed 42 < commands.txt

# With delay between commands (500ms)
cli-rpg --non-interactive --delay 500 < commands.txt

# Skip character creation and use default "Agent" character
cli-rpg --non-interactive --skip-character-creation < commands.txt
```

**Features:**
- Reads commands from stdin line-by-line
- Exits with code 0 when stdin is exhausted (EOF)
- ANSI colors automatically disabled for machine-readable output
- Runs without AI service for deterministic behavior
- `--seed <int>` option for reproducible random outcomes (combat, loot, etc.)
- `--delay <ms>` option for pacing between commands (0-60000ms, default 0)

**Character Creation:**
- By default, reads character creation inputs from stdin (name, class, stat method, stats, confirmation)
- Use `--skip-character-creation` to use a default character ("Agent") with balanced stats (10/10/10/10)
- Manual stats: provide name, class (1-5), "1", str, dex, int, cha, "yes" (one per line)
- Random stats: provide name, class (1-5), "2", "yes" (one per line)
- Invalid inputs return error messages and exit with code 1

### Gameplay Logging

For comprehensive session logging, use the `--log-file` option to record all gameplay activity:

```bash
# Log session to file
cli-rpg --non-interactive --log-file session.log < commands.txt

# Combined with JSON mode (log file separate from stdout)
cli-rpg --json --log-file transcript.log < commands.txt

# With delay for observable pacing (useful for demos/recordings)
cli-rpg --json --delay 200 < commands.txt
```

**Log format** (JSON Lines, one entry per line):
```json
{"timestamp": "2025-01-15T12:00:00.000000+00:00", "type": "session_start", "character": "Agent", "location": "Town Square", "theme": "fantasy", "seed": 12345}
{"timestamp": "2025-01-15T12:00:01.000000+00:00", "type": "command", "input": "look"}
{"timestamp": "2025-01-15T12:00:01.100000+00:00", "type": "response", "text": "=== Town Square ===\n..."}
{"timestamp": "2025-01-15T12:00:01.100000+00:00", "type": "state", "location": "Town Square", "health": 100, "max_health": 100, "gold": 50, "level": 1}
{"timestamp": "2025-01-15T12:00:02.000000+00:00", "type": "session_end", "reason": "eof"}
```

**Entry types:**
- `session_start` - Session initialization with character, location, theme, and seed
- `command` - Player input commands
- `response` - Game output text
- `state` - Game state snapshots (location, health, gold, level)
- `session_end` - Session termination with reason (eof/quit/death)

### JSON Output Mode

For programmatic consumption and AI agent integration, use the `--json` flag to output structured JSON Lines:

```bash
echo -e "look\ngo north\nstatus" | cli-rpg --json
```

**Output format** (one JSON object per line):
```json
{"type": "state", "location": "Town Square", "health": 150, "max_health": 150, "gold": 0, "level": 1}
{"type": "narrative", "text": "=== Town Square ===\nA bustling town square..."}
{"type": "actions", "exits": ["north", "east"], "npcs": ["Town Merchant"], "commands": ["look", "go", ...]}
```

**Message types:**
- `session_info` - Session initialization with seed and theme (first message)
- `state` - Current game state (location, health, gold, level)
- `narrative` - Human-readable text (descriptions, action results)
- `actions` - Available exits, NPCs, and valid commands
- `error` - Machine-readable error code + human message
- `combat` - Combat state (enemy name, enemy health, player health)

**Error codes** for programmatic handling:
- `INVALID_DIRECTION` - Moving in invalid direction
- `NOT_IN_SHOP` - Shop command when not at shop
- `ITEM_NOT_FOUND` - Item not in inventory
- `UNKNOWN_COMMAND` - Unrecognized command
- `NOT_IN_COMBAT` - Combat command outside combat
- `IN_CONVERSATION` - Movement blocked by conversation
- `NO_NPC` - Talk command with no NPCs
- `INVENTORY_FULL` - Inventory capacity reached
- `INSUFFICIENT_GOLD` - Can't afford purchase

**Features:**
- Implies non-interactive mode (reads from stdin)
- ANSI colors automatically disabled
- Each line is a valid JSON object
- Suitable for AI agents, testing frameworks, and automation tools

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run specific test suites:
```bash
# AI-related unit and integration tests
pytest tests/test_ai_*.py -v

# Dynamic world expansion E2E tests
pytest tests/test_e2e_world_expansion.py -v

# All tests with coverage
pytest --cov=src/cli_rpg
```

### Project Structure
```
src/cli_rpg/
├── main.py              # Game entry point and main loop
├── game_state.py        # Game state management
├── combat.py            # Combat system
├── character_creation.py # Character creation flow
├── world.py             # Default world generation
├── world_grid.py        # Grid-based world coordinate system
├── ai_world.py          # AI-powered world generation
├── ai_service.py        # AI service integration
├── ai_config.py         # AI configuration management
├── location_art.py      # Fallback ASCII art for locations
├── npc_art.py           # Fallback ASCII art for NPCs
├── autosave.py          # Automatic game saving
├── dreams.py            # Dream sequences triggered on rest
├── companion_banter.py  # Context-aware companion travel comments
├── companion_reactions.py # Companion reactions to player combat choices
├── companion_quests.py  # Companion personal quest system
├── models/              # Data models
│   ├── character.py
│   ├── location.py
│   ├── enemy.py
│   ├── item.py
│   ├── inventory.py
│   ├── npc.py
│   ├── quest.py
│   ├── shop.py
│   ├── status_effect.py
│   └── companion.py
└── persistence.py       # Save/load system (character and full game state)
```

## Documentation

- [AI Features Guide](docs/AI_FEATURES.md) - Detailed AI world generation documentation
- [AI Specification](docs/ai_location_generation_spec.md) - Technical specification for AI features

## License

MIT
