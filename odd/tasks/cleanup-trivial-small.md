# Feature: cleanup-trivial-small

## Objective
Fix the trivial and small architecture findings from the architecture review, in one pass. No tests required (user decision). No medium/large items.

## Why
Architecture review found 14 issues; user approved fixing trivial + small (7 items) now, deferring medium/large.

## Scope (authorized)
In scope:
- T1 README architecture section refresh (stale config/model/module docs)
- T2 Remove redundant `sys.path.insert` from `main.py`
- T3 Move `diagnostic_window_check.py` → `scripts/`
- T4 Named constants for projectile hit_range / push epsilon in `collision.py`
- T5 `Projectile.__init__` accepts optional `damage`/`speed`; callers pass weapon stats
- T6 Narrow silent `except Exception` with warn-once (no behavior change intended)
- T7 EventBus singleton consistency: register in `__init__`, remove `_set_instance`

Out of scope: tests, medium items (settings mirror, EventBus unification, Player split, dependency inversions), large items (collision unification, service locator removal), O(n²) broad-phase.

## Constraints
- Branch: `chore/cleanup-trivial-small` (from main)
- TDD: off (user: "la de los test no me molesta")
- RDD: off (global)
- Conventional commits; no AI attribution
- User chose single commit for prior WIP + this pass together

## Checklist
- [x] T1 README architecture refresh
- [x] T2 main.py sys.path hack removed
- [x] T3 diagnostic moved to scripts/
- [x] T4 collision constants named
- [x] T5 Projectile damage/speed via constructor
- [x] T6 except Exception warn-once (targeted sites)
- [x] T7 EventBus singleton consistency
- [x] Verify: compileall + targeted import/assert checks — VERIFY_OK
- [x] Work-unit commit: single commit (user: "Todo en un solo commit")

## Progress
- [x] complete — 2026-09-23

## Route
- All tasks: inline (parent writer). Explore/delegate failed earlier (provider free-tier); full review context already loaded in parent; changes are mechanical post-review.

## Verification commands
- `.venv/bin/python -m compileall -q src main.py scripts` — pass
- `.venv/bin/python` assert script: EventBus no `_set_instance`, Projectile signature, constants 0.8/0.01, warn_once once-only, README free of `settings.json`/`panda-model` — pass

## Commit decision
- User selected "Todo en un solo commit": prior uncommitted tree + this pass staged together on `chore/cleanup-trivial-small`.
