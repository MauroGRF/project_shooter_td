# Feature: door and chest interactions

## Objective
Give the two inert level elements real mechanics:
- **Door (D)**: requires a `key` collectable. Walking into a door consumes one key from the player inventory and permanently opens it (now walkable).
- **Chest (C)**: requires the new `interact` action (E key). When the player is adjacent (chebyshev ≤ 1) and presses E, the chest opens and grants a random loot drop (coins / score / weapon refill / health).
- **Bonus — fix `EventBus` multi-subscriber bug** discovered while verifying pickups: Panda3D's `DirectObject.accept` REPLACES per `(event, object)` so all entity subscriptions via the same `ShowBase` clobbered each other and only the last subscriber's callback fired. Pickups, contact damage and exit detection were silently broken whenever more than one entity was in play.

## Why
User audit of level_01.lvl: 6 collectable types work, but `D` and `C` are inert tiles with no handler. User picked `key-required` for door, `adjacent-action-key` for chest. After wiring the door/chest mechanics the user reported "coins stopped being picked up" — investigation traced it back to the pre-existing `EventBus` bug, not my new code.

## Scope (authorized)
- T1 **Key collectable + door auto-open**
- T2 **Interact action + chest with loot drop**
- T3 **EventBus dispatcher fix** (regression discovered during T1/T2 verification)
- T4 Demo placements in `assets/levels/level_01.lvl` (one key near player, one door, one chest reachable through it) + comment legend
- T5 Verify compile + functional run + pickup regression

Out of scope: door/chest animations, inventory UI panel, multiple-key doors, chest loot tiers, on-screen "Press E" hint.

## Decisions (locked)
- New collectable char: `K` → `key` (Key subclass of Collectable, +1 to player.keys)
- New collectable char: `D` already exists as a tile; this task adds the door open mechanic (no new char)
- Player keys: integer counter `keys`, method `use_key()` returning bool
- Door state: `opened: bool` on the Tile, init False. Visual swaps to "open" coloring when opened.
- Door open trigger: `Character._is_walkable` detects blocked door tile + player has key → consumes key + opens + returns walkable. No new event.
- Interact key: `e` → emits `interact_pressed` (same shape as existing `enter_pressed`/`escape_pressed`)
- Chest trigger: `Level` subscribes to `interact_pressed`. On press: find any unopened chest at chebyshev ≤ 1 from player → open it (mark opened, change visual, drop loot).
- Loot table: weighted random — 50% +5 coins, 25% +200 score, 15% refill all weapons, 10% heal 30 HP. Constants in `src/entities/collectables/chest_loot.py`.
- HUD: add `KEYS: n` label, position next to COINS.
- EventBus fix: one `accept` per event name (first subscribe installs a dispatcher); internal list of callbacks; dispatcher fans out. Public API stays `subscribe/unsubscribe/emit/clear`. Replaces the broken per-call `_base.accept(event, callback)` pattern.

## Constraints
- Branch: `feat/collectables` (extend current; door/chest are level-interaction siblings)
- TDD: off (user preference from prior feature)
- RDD: off (global)
- Conventional commits, work-unit commit per task, no AI attribution
- Forecast: ~280-380 authored lines (T1 ~120, T2 ~180, T3 ~85). Under 400 budget; one PR slice per task.

## Checklist
- [x] T1 Key + door
- [x] T2 Interact + chest
- [x] T3 EventBus dispatcher fix
- [x] T4 Level demo + legend
- [x] T5 Verify (compile + smoke + pickup regression)

## Verification
- `.venv/bin/python -m compileall -q src` → exit 0
- T1 smoke (`/tmp/test_t1.py`, 5 checks): Player keys state, use_key, Key collectable, Tile.open(), Character._is_walkable door auto-open (with and without key)
- T2 smoke (`/tmp/test_t2.py`, 8 checks): loot table weights sum 100, roll_chest_loot valid tuple, distribution within ±15pp of weights (1000 seeds), chest.open() sets opened+walkable, InputManager+interact_pressed emitted, adjacent interact opens + drops loot, far interact no-op, double-press idempotent
- Pickup regression (`/tmp/test_real_coin.py`, level_01 integration): player teleported to coin grid, collision.update fires entity_enter, coin.alive → False and player.coins → 1
- Game end-to-end run (`uv run python -u main.py`, 12s): visual logs for wall/door/barrier/chest/player/enemy, no traceback

## Progress

### T1 Key + door
done. New Key subclass of Collectable; Player.keys counter + use_key(); TILE_LEGEND["door"] walkable=False; Character._is_walkable consumes a key on closed-door overlap and calls Tile.open(); HUD KEYS label; K added to COLLECTABLE_CHARS.

### T2 Interact + chest
done. InputManager binds `e` → `interact_pressed`; Level subscribes and finds adjacent (chebyshev ≤ 1) closed chest on press, calls Tile.open() + drops weighted random loot (coins/score/refill/heal) via roll_chest_loot. Chest added to wall_visual branch for 3D look. Tile.open() fixed to set walkable=True even when no wall_visual_box (idempotent guard refactor).

### T3 EventBus dispatcher fix
done. Rewrote `src/core/event_bus.py` to install one dispatcher per event name on the messenger; internal list of callbacks fans out on emit. Public API unchanged. Verified pickup regression gone, all T1/T2 tests still pass.