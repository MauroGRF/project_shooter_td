# Feature: camera pitch limits + lighting + tile/entity heights

## Objective
- Clamp vertical orbit to a useful band (no casi-horizontal ni cenital).
- Add ambient + directional light (hoy no hay ninguna luz en `src/`).
- Fix feet: smiley (-1..1 a escala 0.4) queda hundido 0.4 bajo el piso y las cards lo atraviesan.

## Why
User: rotación vertical se ve mal muy abajo; falta iluminación; cards a mitad de cubos atravesando jugadores.

## Scope (authorized)
- T1 `src/systems/camera.py`: PITCH_MIN 25°, PITCH_MAX 62° (default 45° intacto)
- T2 `src/game/game_manager.py`: `_setup_lights()` ambient 0.55 + directional 0.85
- T3 `src/entities/player/player.py`: MODEL_OFFSET z 0.4 (pies en z=0)
- T4 Verify compile + headless

## Decisions (locked)
- Enemy ya tiene pies en 0 (mesh 0..6 a 0.13 → 0..0.78). No se toca.
- tile_box centrado verificado (-0.5..0.5); base en 0 vía pos wall_h/2. No se toca.
- floor_card_z=0.005 ya es ras de piso. El "atravesar" era el smiley hundido, no la card alta.
- Pitch band 25°–62°: mantiene vista original 45° y evita rasante/cenital.

## Checklist
- [x] T1 Pitch clamp (25°–62°, verificado headless)
- [x] T2 Lighting (2 luces en render, verificado headless)
- [x] T3 Player feet (origen z=0.4, verificado headless)
- [x] T4 Verify (compile OK + main sin traceback)
- [x] T5 Piso bajo spawns (100/100 celdas, spawns con floor debajo)
- [x] T6 Piso tras clear_barriers (3 barreras -> floor, tiles intactos)
- [x] T7 Base piso siempre (floor bajo toda celda no-wall + elemento encima; clear solo quita elemento)

## Verification
- `compileall -q src` → OK
- Headless: pitch 25/45/62, 2 luces, player z=0.4 en (2,1)
- `main.py` 12s: visuales resuelven, sin traceback (exit 124 = timeout en menú)
