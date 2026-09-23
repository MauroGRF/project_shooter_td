# TD Shooter

Top-down 3D shooter construido con Python y Panda3D. Arquitectura modular basada en maquina de estados, sistema de entidades y pipeline de recursos con archivos de texto.

---

## Ejecucion

```bash
# Instalar dependencias
uv sync

# Ejecutar el juego
uv run main.py

# O directamente con el venv
.venv\Scripts\python.exe main.py
```

**Requisitos:** Python 3.10+, panda3d 1.10+

---

## Controles

| Accion | Tecla | Descripcion |
|--------|-------|-------------|
| Mover | W A S D | Desplazamiento libre en el plano XY |
| Apuntar | Flechas / ratón | Dirección de vista (ratón tiene prioridad si hay mouse) |
| Sprint | Shift | Correr (gasta stamina) |
| Dash | Z | Desplazamiento rápido (cooldown + stamina) |
| Parry | Ctrl | Bloqueo/reflejo (carga por near-dodge) |
| Armas | 0 1 2 3 | melee, pistol, rifle, shotgun |
| Munición | L | Alterna limited / infinite |
| Efecto test | M | Aplica efecto de velocidad (debug) |
| Disparar | Espacio / clic izq. | Ataque del arma seleccionada |
| Pausa | P | Interrumpe el juego, muestra menu de pausa |
| Iniciar / salir | Enter / Escape | Menú: iniciar · gameplay: menú · pausa: menú |

---

## Arquitectura del proyecto

### Diagrama de dependencias

```
main.py
  └── GameManager (ShowBase)
        ├── Settings           ← config/{window,player,weapons,enemies,camera,audio,game}.json
        ├── EventBus           ← wrapper de messenger
        ├── InputManager       ← teclado + ratón (WASD, armas, dash, parry)
        ├── AudioManager       ← musica y efectos
        ├── Window             ← propiedades de ventana
        └── StateMachine
              ├── MenuState       → titulo, controles, iniciar
              ├── LoadingState    → carga nivel via LevelManager
              ├── GameplayState   → nivel activo, HUD, update loop
              └── PauseState      → menu de pausa
```

### Flujo de ejecucion

```
1. main.py instancia GameManager()
2. GameManager inicializa ShowBase, Settings, EventBus, Window, InputManager
3. StateMachine arranca en MenuState
4. Usuario presiona ENTER → LoadingState
5. LoadingState consulta LevelManager para parsear el archivo .lvl
6. LevelManager retorna un diccionario con la grilla de tiles y spawns
7. LoadingState pasa los datos a GameplayState → Level construye el mapa
8. GameplayState ejecuta el loop principal (physics, collision, input, render)
9. Pausa (P) → PauseState (override sobre GameplayState)
10. Muerte del jugador → transicion a MenuState
```

---

## Modulos

### `src/game/` — Motor principal

| Archivo | Responsabilidad |
|---------|-----------------|
| `game_manager.py` | Clase principal que hereda de `ShowBase`. Crea e inicializa todos los sistemas. Ejecuta el game loop via `task_mgr` y delega el `update(dt)` al estado activo. |
| `window.py` | Lee la configuración de ventana desde `config/window.json` y aplica titulo, resolucion, fullscreen y color de fondo usando `WindowProperties`. |

**GameManager** es un singleton accesible desde cualquier modulo via `GameManager.get_instance()`. Cada sistema recibe una referencia al game en su constructor.

### `src/core/` — Infraestructura base

| Archivo | Responsabilidad |
|---------|-----------------|
| `settings.py` | Singleton que carga los 7 archivos de dominio bajo `config/`. Falla al boot si falta archivo o key requerida. Acceso por property (`settings.player`) o dotted (`get("game.tile_size")`) con espejo legacy `game.*`. |
| `event_bus.py` | Wrapper del `messenger` de Panda3D. Provee `subscribe(event, callback)`, `unsubscribe(event, callback)` y `emit(event, *args)`. Desacopla los modulos entre si. Se registra como singleton en `__init__`. |
| `warn_once.py` | Helper `warn_once(key, msg)` para surfear excepciones tragadas sin spam por frame. |

**EventBus** es el corazon del desacoplamiento. Los sistemas emiten eventos (`entity_died`, `projectile_fired`, `state_changed`) y los componentes se suscriben sin conocer al emisor.

### `src/states/` — Maquina de estados

| Archivo | Responsabilidad |
|---------|-----------------|
| `state_base.py` | Clase abstracta con metodos `enter()`, `exit()`, `update(dt)`, `handle_input(action)`. |
| `state_machine.py` | Registra estados por nombre, gestiona transiciones con `change_state(name)`. Emite evento `state_changed`. |
| `menu_state.py` | Muestra titulo, controles y opciones con `TextNode` sobre `aspect2d`. |
| `loading_state.py` | Recibe un nombre de archivo `.lvl`, consulta `LevelManager`, y transiciona a `gameplay` con los datos parseados. |
| `gameplay_state.py` | Instancia `Level` y `HUD`. Delega el `update(dt)` al nivel y al HUD. |
| `pause_state.py` | Muestra opciones de pausa. Al reanudar, retoma `gameplay` sin recargar. |

**Patron:** cada estado es una instancia de `StateBase` que se registra una sola vez en la maquina. Las transiciones llaman `exit()` del estado actual y `enter()` del nuevo.

### `src/levels/` — Gestion de niveles

| Archivo | Responsabilidad |
|---------|-----------------|
| `level_manager.py` | Lee archivos `.lvl` (matriz ASCII), parsea cada caracter a un tipo de tile, y retorna un diccionario con `width`, `height`, `tiles[][]`, `player_spawn`, `enemy_spawns[]` y `dog_spawns[]`. |
| `level.py` | Recibe los datos del nivel, instancia tiles, personajes y enemigos. Crea Physics/Collision/Animation/Camera por nivel. Ejecuta el update en orden y gestiona lifecycle de entidades, proyectiles y melee hitboxes. |

**Formato `.lvl`:** cada linea es una fila de tiles separados por espacios. Lineas que empiezan con `#` son comentarios.

```
# level_01.lvl
W W W W W W W W W W
W S S S S S S S S W
W S P S S S S S S W
W S S S S E S S S W
W S S S S S S S S W
W W W W W W W W W W
```

| Caracter | Tipo | Caminable | Descripcion |
|----------|------|-----------|-------------|
| `W` | wall | No | Pared solida, bloquea movimiento y proyectiles |
| `S` | floor | Si | Suelo base del mapa |
| `P` | spawn_player | Si | Posicion inicial del jugador (no genera tile) |
| `E` | spawn_enemy | Si | Posicion de enemigos (no genera tile) |
| `F` | spawn_dog | Si | Posicion de dogs (no genera tile) |
| `D` | door | Si | Puerta (transicion entre areas) |
| `C` | chest | No | Cofre interactuable |
| `B` | barrier | No | Barrera solida; se elimina con el evento `clear_barriers` |
| `o` | coin | Si | Collectable: +1 moneda al contacto |
| `m` | score | Si | Collectable: +monedas y +puntaje |
| `g` | weapon | Si | Collectable: recarga arma (o la cambia en modo select) |
| `x` | exit | Si | Collectable: termina el nivel |
| `t` | trigger | Si | Collectable: dispara `clear_barriers` |
| `n` | next_level | Si | Collectable: dispara `change_level` hacia `# next_level: file.lvl` |

**Metadatos por comentario** (lineas `# clave: valor`):
- `# next_level: level_02.lvl` — destino del collectable `n`

**Logica de colision por tiles:**
- `LevelManager` calcula la posicion world-space de cada tile: `(grid_x * tile_size, grid_y * tile_size)`
- `tile_size` esta definido en `config/game.json` (default: 1.0 unidad)

### `src/entities/` — Entidades del juego

| Archivo | Responsabilidad |
|---------|-----------------|
| `entity_base.py` | Clase base: nodo3D, vida, daño, muerte, tipo, contacts, anims, swap/destroy de modelo. |
| `model_loader.py` | Carga glTF/GLB/egg/bam + `resolve_visual()` (fuente única de verdad: class MODEL > config default). |
| `character.py` | Hereda de `EntityBase`. Movimiento con colisión AABB por caja, aim, shoot base. |
| `player/player.py` | Stamina, sprint, dash, parry, 4 armas, melee trail, status effects. |
| `enemies/enemy.py` | Enemy (ranged) y Dog (melee). AI data-driven vía dict de states. |
| `tile.py` | Tile estático: wall/barrier = box `tile_box.glb`; floor/door/chest = card plana con textura `TileTextureCache`. |
| `projectile.py` | Proyectil con speed/damage opcionales por constructor (default = config). |
| `melee_hitbox.py` | Hitbox temporal del swing melee. |
| `collectables/` | `Collectable` + subclases (score, weapon, exit, event). Al tocar al player: +moneda y efecto extra. |

**Jerarquía de entidades:**
```
EntityBase
  ├── Character
  │     ├── Player
  │     └── Enemy → Dog
  ├── Collectable
  │     ├── ScoreBonus
  │     ├── WeaponPickup
  │     ├── LevelExit
  │     └── EventTrigger
  ├── Tile
  ├── Projectile
  └── MeleeHitbox
```

**EntityBase (campos clave):**
```
node, life/max_life, alive, speed, velocity, entity_type
COLLISION_HALF_EXTENTS (subclases miden su visual)
```

### `src/systems/` — Sistemas del juego

| Archivo | Responsabilidad |
|---------|-----------------|
| `input_manager.py` | Captura teclado/ratón. WASD, flechas, Shift sprint, Z dash, Ctrl parry, 0-3 armas, L ammo, mouse aim. Expone `get_movement()` / `get_aim()` y llama `request_*` del player. |
| `physics.py` | Walkability AABB compartida (`is_position_walkable`) + path de velocity (inerte hoy). |
| `collision.py` | Proyectil↔entity (`PROJECTILE_HIT_RANGE`), entity↔tile push, entity↔entity contacts + contact damage, melee hitboxes. |
| `camera.py` | Sistema de camara isometrica. Configuracion estática por nivel o follow de entidad. |
| `audio_manager.py` | Carga y reproduce musica de fondo y efectos de sonido. |
| `animation_system.py` | Animaciones frame-based (scale, color, pos_offset), loop o one-shot. |
| `status_effects.py` | Buffs temporales (speed multiplier, etc.) sobre el player. |

**InputManager — flujo del input:**
```
1. Tecla → accept(...) → _set_key / _on_action / request_*
2. update(dt) consulta keys + mouse y llama player.request_move/aim/shoot
3. Acciones de estado (enter/escape/pause) emiten por EventBus
```

**Collision — AABB por caja:**
```
1. entity↔tile: half-extents del entity vs half tile; push en eje de menor penetración
2. proyectil↔entity: distancia < PROJECTILE_HIT_RANGE (+ dodge window para parry)
3. entity↔entity: pares por distancia → entity_enter/exit + contact damage
```

**CameraSystem — modos de operacion:**
```
1. setup(center_x, center_y): posiciona camara sobre el centro del nivel
2. follow(entity): la camara sigue a una entidad en cada frame
3. unfollow(): detiene el seguimiento
4. update(dt): actualiza posicion si hay target activo
```
- La camara se instancia por nivel (cada Level crea su CameraSystem)
- Configuracion desde `config/camera.json`: `camera.height`, `camera.fov`

### `src/ui/` — Interfaces de usuario

| Archivo | Responsabilidad |
|---------|-----------------|
| `hud.py` | HP, stamina, dash, parry, arma, score, ammo, effects como `OnscreenText`. Lee el player vía GameplayState cada frame. |
| `menu_ui.py` | Componentes de menu con `DirectGui` (botones, frames). Util para menus interactivos con mouse. |

---

## Configuracion (`config/*.json`)

Un archivo por dominio; cada uno envuelve sus keys bajo una sección top-level con el nombre del dominio. `Settings` valida required keys al boot y falla con mensaje claro si falta algo.

| Archivo | Seccion | Contenido clave |
|---------|---------|-----------------|
| `window.json` | `window` | title, width, height, fullscreen, backgroundColor |
| `player.json` | `player` | speed, life, stamina, dash, parry, melee, model |
| `weapons.json` | `weapons` | armas `0`–`3` (type, damage, fire_rate, pellets, spread…) |
| `enemies.json` | `enemies` | enemy/dog stats + model scale/rotation/offset |
| `camera.json` | `camera` | height, angle, near, far, fov |
| `audio.json` | `audio` | music_volume, sfx_volume |
| `game.json` | `game` | tile_size, gravity, projectile_*, tile_model, wall_height… |

Acceso:

```python
settings.player["player_speed"]   # preferred: domain property
settings.get("game.tile_size")    # dotted (legacy mirror for player/enemies keys)
settings["camera.height"]         # __getitem__ → get()
```

---

## Sistema de eventos

El `EventBus` permite desacoplar completamente los modulos. Ejemplo de flujo:

```
InputManager                    EventBus                      GameplayState
     │                              │                              │
     │  accept("p", callback)       │                              │
     │─────────────────────────────>│                              │
     │                              │  emit("pause_pressed")       │
     │                              │─────────────────────────────>│
     │                              │                              │
     │                              │  state_machine.change_state  │
     │                              │         ("pause")            │
```

**Eventos del sistema:**
| Evento | Emisor | Descripcion |
|--------|--------|-------------|
| `enter_pressed` | InputManager | Tecla Enter presionada |
| `escape_pressed` | InputManager | Tecla Escape presionada |
| `pause_pressed` | InputManager | Tecla P presionada |
| `state_changed` | StateMachine | Transicion de estado completada |
| `entity_died` | EntityBase | Una entidad perdio toda su vida |
| `player_died` | Player | El jugador murio |
| `entity_enter` / `entity_exit` | CollisionSystem | Par de entidades entro/salio de contacto |
| `projectile_hit` | CollisionSystem | Proyectil impacto una entidad |
| `projectile_reflected` | CollisionSystem | Proyectil rebotado por parry |
| `melee_hitbox` hit | CollisionSystem | Hitbox melee impacto |

---

## Camara isometrica

El juego utiliza una vista cenital-isometrica:

```python
# Posicion: centrada sobre el nivel, elevada en Z
camera.setPos(center_x, center_y - cam_height, cam_height)
camera.lookAt(center_x, center_y, 0)
```

- **Eje X:** izquierda/derecha en pantalla
- **Eje Y:** profundidad (hacia/desde la camara)
- **Eje Z:** altura vertical
- **Heading (H):** rotacion del personaje en el plano XY

---

## Modelos y assets

| Entidad | Modelo / visual | Fuente |
|---------|-----------------|--------|
| Player | `models/smiley` | clase `Player.MODEL` |
| Enemy / Dog | `assets/models/enemy_fixed.gltf` | clase (`scale` 0.13) |
| Wall tile | `assets/models/tile_box.glb` | config `game.tile_model` |
| Floor/door/chest | CardMaker plana + textura | `TileTextureCache` (`assets/textures/*.png`) |
| Proyectil | CardMaker cuadrado | código en `Projectile` |
| Marker player/enemy | CardMaker sobre la entidad | código |

`resolve_visual(entity_type, cls, game)` es la única puerta: gana la clase si declara `MODEL*`; si no, el default del config; si no hay ninguno, `ValueError` (fail-fast).

---

## Proximos pasos

- [x] Sistema de disparo funcional con cooldown (4 armas + melee)
- [ ] Animaciones de movimiento y disparo
- [x] Sistema de audio (musica y SFX)
- [x] Enemigos con patrones de IA variados (FSM idle/chase/attack + Dog melee)
- [ ] multiples niveles con transiciones
- [ ] Sistema de vida/muerte con respawn
- [ ] UI con DirectGui para menus interactivos
- [ ] Pickups y items (cofres, power-ups)
- [ ] Minimap
- [ ] Optimizacion de render (instancing, culling)
