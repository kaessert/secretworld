# Implementation Plan: Random Encounter Merchant/Wanderer Interactions

## Analysis Summary

The random encounter system is **already fully functional** for merchant and wanderer interactions:

1. **Merchant encounters work correctly**:
   - `spawn_wandering_merchant()` creates NPC with `is_merchant=True` and a shop with 2-3 items
   - NPC is added to `location.npcs`
   - Player can use `talk <merchant name>` to interact
   - Once talking, the shop context is set automatically (`game_state.current_shop = npc.shop`)
   - Player can use `shop`, `buy <item>`, `sell <item>` commands

2. **Wanderer encounters work correctly**:
   - `spawn_wanderer()` creates atmospheric NPC with dialogue
   - NPC is added to `location.npcs`
   - Player can use `talk <wanderer name>` to interact
   - Dialogue reduces dread by 5 (standard NPC interaction benefit)

## Conclusion: No Implementation Needed

The system is complete. The format message already tells players:
```
(Use 'talk <NPC name>' to interact)
```

And upon talking:
- Merchants: "Type 'shop' to see items, 'buy <item>' to purchase, 'sell <item>' to sell."
- Wanderers: Get atmospheric dialogue + dread reduction

**The "missing interaction" hypothesis was incorrect.** Both encounter types have meaningful interactions already implemented.

## Optional Enhancements (Not Required)

If future enhancement is desired, these could add value:

1. **Wanderer gifts**: Small chance to receive a consumable/blessing after conversation
2. **Wanderer lore hints**: Connect dialogue to actual game locations/secrets
3. **Merchant discounts**: Bond-style pricing based on conversation
4. **Encounter persistence**: Random NPCs could disappear after player leaves location

---

**Status**: No implementation required - feature is complete as designed.
