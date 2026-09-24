# Feature: collectables

## Objective
Add a `Collectable` class hierarchy. On pickup (contact with player) every collectable increases a coin counter. Subclasses add extra effects: score, weapon change/reload, level end, and events (level change, barrier removal).

## Why
User request: gameplay pickups framework with inheritance from one base class.

## Scope (authorized)
- T1 `Collectable` base + `ScoreBonus`, `WeaponPickup`, `LevelExit`, `EventTrigger` in `src/entities/collectables/`
- T2 Player `coins`/`score` + `add_coin`/`add_score`/`reload_weapon`; HUD coins + wired score
- T3 LevelManager: new .lvl chars + `collectable_spawns` + `next_level` comment parse
- T4 Level: build collectables + barrier tiles; handle `clear_barriers` event
- T5 GameplayState: `level_complete` / `change_level` handlers
- T6 Demo placements in `assets/levels/level_01.lvl` + README legend update
- T7 Verify compile + import checks

Out of scope: inventory UI, trading/shop, save/persist coins, animation polish.

## Decisions (locked)
- Placement: chars in .lvl (user choice)
- New chars: `o` coin, `m` score, `g` weapon, `x` exit, `t` trigger(clear_barriers), `n` next_level trigger, `B` barrier tile
- Every collectable gives +1 coin in base `_collect`; subclass `on_collect(player)` adds effect
- Collectables skip projectile hits via `collectable = True` flag
- `next_level` target comes from `# next_level: file.lvl` comment header

## Constraints
- Branch: `feat/collectables`
- TDD: off (user earlier: tests not wanted)
- RDD: off (global)
- Conventional commits, work-unit commit, no AI attribution
- ~450 authored lines forecast — above 400 heuristic; one coherent feature, explained overage, single PR-size unit

## Checklist
- [x] T1 Collectable hierarchy
- [x] T2 Player + HUD coins/score
- [x] T3 LevelManager chars/spawns
- [x] T4 Level wiring + barriers
- [x] T5 GameplayState events
- [x] T6 Level demo + README
- [x] T7 Verify + work-unit commit

## Verification
- `.venv/bin/python -m compileall -q src`
- import + factory smoke check
