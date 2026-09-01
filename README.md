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
| Apuntar | Flechas | Cambia la direccion de vista del personaje |
| Pausa | P | Interrumpe el juego, muestra menu de pausa |
| Salir | Escape | Cierra el juego o vuelve al menu principal |
| Iniciar | Enter | Comienza la partida desde el menu |

---

## Arquitectura del proyecto

### Diagrama de dependencias

```
main.py
  └── GameManager (ShowBase)
        ├── Settings           ← config/settings.json
        ├── EventBus           ← wrapper de messenger
        ├── InputManager       ← teclado (WASD + flechas)
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
| `window.py` | Lee la configuracion de ventana desde `settings.json` y aplica titulo, resolucion, fullscreen y color de fondo usando `WindowProperties`. |

**GameManager** es un singleton accesible desde cualquier modulo via `GameManager.get_instance()`. Cada sistema recibe una referencia al game en su constructor.

### `src/core/` — Infraestructura base

| Archivo | Responsabilidad |
|---------|-----------------|
| `settings.py` | Singleton que carga `config/settings.json`. Soporta claves anidadas con notacion punto (`game.tile_size`). Permite leer/escribir/guardar configuraciones en runtime. |
| `event_bus.py` | Wrapper del `messenger` de Panda3D. Provee `subscribe(event, callback)`, `unsubscribe(event, callback)` y `emit(event, *args)`. Desacopla los modulos entre si. |

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
| `level_manager.py` | Lee archivos `.lvl` (matriz ASCII), parsea cada caracter a un tipo de tile, y retorna un diccionario con `width`, `height`, `tiles[][]`, `player_spawn` y `enemy_spawns[]`. |
| `level.py` | Recibe los datos del nivel, instancia tiles, personajes y enemigos. Crea un CameraSystem por nivel. Ejecuta el update de physics, collision, animation y camera. Gestiona la lifecycle de entidades y proyectiles. |

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
| `D` | door | Si | Puerta (transicion entre areas) |
| `C` | chest | No | Cofre interactuable |

**Logica de colision por tiles:**
- `LevelManager` calcula la posicion world-space de cada tile: `(grid_x * tile_size, grid_y * tile_size)`
- `tile_size` esta definido en `settings.json` (default: 1.0 unidad)

### `src/entities/` — Entidades del juego

| Archivo | Responsabilidad |
|---------|-----------------|
| `entity_base.py` | Clase base para todas las entidades. Maneja: nodo3D, vida, daño, muerte, tipo de entidad. |
| `character.py` | Hereda de `EntityBase`. Personajes (player y enemigos). Movimiento con colision a tiles, apuntar por flechas, IA basica para enemigos. |
| `tile.py` | Hereda de `EntityBase`. Tiles estaticos del mapa. Genera geometria visual con `CardMaker`: suelo plano y paredes como bloques 3D (5 caras). |
| `projectile.py` | Hereda de `EntityBase`. Proyectil con velocidad, danyo, lifetime y direccion. |

**EntityBase:**
```
- node: NodePath (nodo 3D en la escena)
- life / max_life: puntos de vida
- alive: booleano de estado
- speed: velocidad de movimiento
- entity_type: string identificador ("player", "enemy", "wall", etc.)
```

**Character (player/enemy):**
```
- move(dx, dy, dt, tiles): mueve por eje independiente (permite deslizarse langs de paredes)
- aim(dx, dy): cambia la orientacion visual con atan2(dx, -dy)
- shoot(): genera un Projectile (disabled actualmente)
- _update_ai(dt): enemigos persiguen al jugador y disparan
```

**Tile (suelo/pared):**
```
- Genera CardMaker para cada cara visible
- Paredes: 5 caras (top + front + back + left + right)
- Suelo: 1 cara orientada con setP(-90)
- Colores por tipo de tile
```

### `src/systems/` — Sistemas del juego

| Archivo | Responsabilidad |
|---------|-----------------|
| `input_manager.py` | Captura teclado. WASD para movimiento, flechas para apuntar. Proporciona `get_movement()` y `get_aim()` normalizados. |
| `physics.py` | Actualiza posiciones basado en velocity. Soporta gravedad y colision walkable con tiles. |
| `collision.py` | Deteccion de colisiones: proyectil↔entity (distance < hit_range) y entity↔tile (AABB push). |
| `camera.py` | Sistema de camara isometrica. Configuracion estatica por nivel o seguimiento dinamico de entidad. |
| `audio_manager.py` | Carga y reproduce musica de fondo y efectos de sonido. |
| `animation_system.py` | Sistema de animaciones frame-based. Registra secuencias de frames (scale, color, pos_offset) y las reproduce con loop o una vez. |

**InputManager — flujo del input:**
```
1. Tecla presionada → accept("w", _set_key, ["w", True])
2. _set_key actualiza self.keys["w"] = True
3. update(dt) consulta self.keys y genera vector de movimiento/aim
4. Se aplica al personaje via player.move() / player.aim()
```

**Collision — algoritmo AABB:**
```
1. Para cada entidad, verifica contra cada tile no-walkable
2. Calcula distancia absoluta en X e Y al centro del tile
3. Si ambas distancias son menores a half (tile_size * 0.5), hay colision
4. Aplica push en el eje de menor penetracion para expulsar al entity
```

**CameraSystem — modos de operacion:**
```
1. setup(center_x, center_y): posiciona camara sobre el centro del nivel
2. follow(entity): la camara sigue a una entidad en cada frame
3. unfollow(): detiene el seguimiento
4. update(dt): actualiza posicion si hay target activo
```
- La camara se instancia por nivel (cada Level crea su CameraSystem)
- Configuracion desde `settings.json`: `camera.height`, `camera.fov`

### `src/ui/` — Interfaces de usuario

| Archivo | Responsabilidad |
|---------|-----------------|
| `hud.py` | Muestra HP, Score y Ammo como `OnscreenText` sobre `aspect2d`. Se actualiza cada frame con los datos del jugador. |
| `menu_ui.py` | Componentes de menu con `DirectGui` (botones, frames). Util para menus interactivos con mouse. |

---

## Configuracion (`config/settings.json`)

```json
{
    "window": {
        "title": "TD Shooter",
        "width": 1280,
        "height": 720,
        "fullscreen": false,
        "BackgroundColor": [0.1, 0.1, 0.15, 1.0]
    },
    "game": {
        "tile_size": 1.0,
        "gravity": -20.0,
        "player_speed": 5.0,
        "player_life": 100,
        "projectile_speed": 15.0,
        "projectile_damage": 10,
        "enemy_speed": 2.5,
        "enemy_life": 30
    },
    "camera": {
        "height": 15.0,
        "fov": 60
    },
    "audio": {
        "music_volume": 0.7,
        "sfx_volume": 0.8
    }
}
```

Acceso desde codigo: `game.settings.get("game.player_speed")` o `game.settings["game.player_speed"]`.

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
| `projectile_fired` | Character | Se genero un proyectil |
| `projectile_hit` | CollisionSystem | Proyectil impacto una entidad |

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

## Modelos de prueba

El juego usa modelos built-in de Panda3D para testing:

| Entidad | Modelo | Descripcion |
|---------|--------|-------------|
| Player | `models/smiley` | Esfera sonriente |
| Enemy | `models/panda-model` | Panda 3D basico |
| Tiles | `CardMaker` | Geometria generada por codigo |
| Proyectil | `CardMaker` | Cuadrado amarillo |

---

## Proximos pasos

- [ ] Sistema de disparo funcional con cooldown
- [ ] Animaciones de movimiento y disparo
- [ ] Sistema de audio (musica y SFX)
- [ ] Enemigos con patrones de IA variados
- [ ] multiples niveles con transiciones
- [ ] Sistema de vida/muerte con respawn
- [ ] UI con DirectGui para menus interactivos
- [ ] Pickups y items (cofres, power-ups)
- [ ] Minimap
- [ ] Optimizacion de render (instancing, culling)
