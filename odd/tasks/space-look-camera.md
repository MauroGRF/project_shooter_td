# Feature: dual-mode camera (player mode + space-held camera mode)

## Objective
- **Player mode** (default): WASD walks the player, mouse aims, click izquierdo dispara. Camera is at the original wide view over the map centre (height=15, looking at the centre). The camera does not follow the player.
- **Camera mode** (space held): the player is frozen. WASD slides the camera in the world XY plane; the mouse rotates the camera (FPS mouselook: mouse X = yaw, mouse Y = pitch). The camera position is clamped to map + 20-unit margin so it cannot fly off to infinity, and the look-at point is clamped to the tight map bounds so the view centre never leaves the level.
- **Space released**: camera snaps back to the default wide view.

## Why
The user wants to be able to inspect the level from any angle while playing. The "space held" key switches the input from controlling the player to controlling the camera, so the player is still alive at the original position but stops moving.

## Scope (authorized)
- T1 **CameraSystem rewrite** in `src/systems/camera.py` (`_camera_pos` Vec3 + `_yaw` + `_pitch`; `setup()` positions at the original wide view; `pan()` slides XY; `rotate()` clamps to ±85° pitch; `update()` recomputes look-at; `reset()` snaps everything back to default)
- T2 **InputManager dual-mode** in `src/systems/input_manager.py` (player mode: WASD → player, mouse → aim, mouse1 → shoot; camera mode: WASD → camera.pan, mouse → camera.rotate, player frozen; space release → camera.reset())
- T3 **Settings + config** (new keys `pan_speed`, `rotate_speed`, `look_deadzone` in `camera.json` + `_DOMAINS["camera"]`)
- T4 Verify (compile + smoke + functional run)

## Decisions (locked)
- Default camera: `(center_x, center_y - height, height)` looking at `(center_x, center_y, 0)` — exact original setup. Height=15 from settings.
- Look-at distance = `height * √2 ≈ 21.2` units. At yaw=0 / pitch=45° (default), the look-at falls exactly at `(center_x, center_y, 0)`.
- T5 refinement (user request): WASD is camera-relative (W = forward on screen = view dir `(-sin yaw, cos yaw)`), NOT fixed world north. Mouse sets the ABSOLUTE orbit target `atan2(sx, sy)` around the stage with shortest-arc easing, NOT incremental FPS spin. Camera translates around the stage keeping the look-at centred.
- Camera mode: WASD pans the camera in **world-relative** XY (W = +y north, S = -y south, A = -x west, D = +x east). Camera-relative movement would couple WASD to the current yaw and is more confusing; world-relative is what level editors use.
- Camera mode: mouse rotates yaw + pitch (FPS mouselook convention — mouse right = view rotates right, mouse up = view tilts up). Pitch is clamped to ±85° to avoid pole flip.
- Camera position clamp: loose (`_camera_bounds`, 20-unit margin) so the original default (camera at `y = cy - 15`) survives but the camera cannot fly to infinity.
- Look-at clamp: tight (`_level_bounds`, no margin) so the centre of the view cannot leave the level — the user always sees the map.
- Space release = `cs.reset()` → camera snaps back to default.
- Space repurposed from "shoot" to "camera mode". Mouse1 (LMB) keeps shooting.
- Player.aim is NOT called while space held. Player position is NOT updated while space held. The player is fully frozen.

## Constraints
- Branch: `feat/collectables` (extend current; one feature stream)
- TDD: off
- RDD: off
- Conventional commits, work-unit commit per task, no AI attribution
- Forecast: ~250-300 authored lines (rewritten `camera.py` + dual-mode `input_manager.py` + `camera.json` + `settings.py`).

## Checklist
- [x] T1 CameraSystem rewrite (camera_pos + yaw + pitch + bounds clamp)
- [x] T2 InputManager dual-mode (player mode + space-held camera mode)
- [x] T3 Settings + config
- [x] T4 Verify
- [x] T5 Orbit-stage refinement (WASD camera-relative + mouse absolute yaw)
- [x] T6 Orbit persiste + sin salto inicial + sin WASD en cámara (WASD siempre al player, mouse-delta orbita, sin reset al soltar)

## Verification (T5)
- `compileall -q src` → exit 0
- Math check: `atan2` mapping Este=90°, Norte=0°; W a yaw=90° mueve -x (oeste, hacia donde mira); `orbit_towards` converge en un paso con lerp=1
- Run `main.py`: sin traceback, visuales resuelven

## Verification
- `.venv/bin/python -m compileall -q src` → exit 0
- `/tmp/test_dual_mode.py` (6 checks): default camera at (5, -10, 15); WASD in player mode moves player, camera static; WASD in camera mode moves camera, player frozen; mouse rotates yaw + pitch in camera mode; space release resets camera to default; WASD works again after reset
- Functional run: visual logs for wall/door/barrier/chest/player/enemy, no traceback

## Progress

### T1 CameraSystem rewrite
done. Rewrote `CameraSystem` with `_camera_pos` (Vec3), `_yaw`, `_pitch`. `setup()` and `reset()` snap to the default wide view. `pan(dx, dy, dt)` and `rotate(dyaw, dpitch, dt)` mutate state. `update()` applies both with bounds clamps (`_camera_bounds` loose for camera position, `_level_bounds` tight for look-at). `follow()` is a no-op kept for back-compat.

### T2 InputManager dual-mode
done. `update()` reads `space_held` once and tracks the previous frame's state. When `space_held` flips off, `_reset_camera_to_default()` is called. While held, `_update_camera_mode(dt, dx, dy)` feeds WASD to `cs.pan(...)` and the mouse vector to `cs.rotate(...)`. While not held, the original player-mode behaviour (move + aim + shoot + parry) runs.

### T3 Settings + config
done. `camera.pan_speed=14.0`, `camera.rotate_speed=2.5`, `camera.look_deadzone=0.05` in `camera.json` + `_DOMAINS["camera"]`.

## Behaviour change to call out

- Space no longer shoots — only mouse1 (LMB).
- WASD behaviour is **mode-dependent**: in player mode it walks the player; in camera mode it slides the camera. The player position is frozen while space is held.
- Default view is the original wide view (camera at `(cx, cy-15, 15)` looking at the centre) — exactly the view the user said was good.
- Space release snaps the camera back to the default view. If you re-enter camera mode immediately you start inspecting again from the wide view.