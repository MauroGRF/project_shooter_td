# Entities — Documentación

Sistema de entidades del juego. jerarquía de herencia:

```
EntityBase
  ├── Character
  │     ├── Player
  │     └── Enemy
  ├── Tile
  └── Projectile
```

---

## EntityBase

Clase base abstracta para todas las entidades del juego.

**Archivo:** `entity_base.py`

### Propiedades

| Propiedad | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `game` | GameManager | — | Referencia al motor principal |
| `entity_type` | str | `"generic"` | Identificador del tipo de entidad |
| `life` | int | 100 | Puntos de vida actuales |
| `max_life` | int | 100 | Puntos de vida máximos |
| `alive` | bool | True | Si está viva |
| `speed` | float | 0.0 | Velocidad de movimiento |
| `velocity` | list | [0,0,0] | Vector de velocidad (x, y, z) |
| `node` | NodePath | — | Nodo 3D en la escena de Panda3D |
| `child_nodes` | dict | {} | Nodos hijos (brazos, armas, etc.) |
| `joints` | dict | {} | Joints expuestos del esqueleto |
| `_contacts` | set | {} | IDs de entidades en contacto |
| `_contacts_enabled` | bool | True | Si detecta contactos |
| `_anims` | dict | {} | Animaciones registradas |

### Métodos de vida

```python
entity.take_damage(10)    # Reduce vida, llama a die() si llega a 0
entity.heal(20)           # Restaura vida (no excede max_life)
entity.die()              # Marca como muerta, emite "entity_died"
entity.is_dead()          # Retorna True si life <= 0
```

### Métodos de posición

```python
entity.set_position(x, y, z)    # Posición absoluta
entity.get_position()            # Retorna (x, y, z) tuple
```

### Sistema de contactos

Detecta cuando esta entidad entra o sale de contacto con otra.

```python
# Habilitar/deshabilitar
entity.set_contacts_enabled(True)
entity.set_contacts_enabled(False)
entity.contacts_enabled()        # Retorna bool

# Sobreescribir en subclases
def on_contact_enter(self, other):
    """Se llama al tocar otra entidad"""
    pass

def on_contact_exit(self, other):
    """Se llama al separarse de otra entidad"""
    pass

# Consultar contacto específico
entity.is_contacting(other_entity)  # Retorna bool
```

**Eventos del sistema:**
- `entity_enter` — emitido por CollisionSystem al detectar contacto
- `entity_exit` — emitido por CollisionSystem al detectar separación

### Sistema de animaciones (híbrido)

Soporta 3 capas: model swapping, node manipulation y joint manipulation.

```python
# Registrar animación
entity.register_anim("walk", [
    {"scale": 0.3, "color": (1, 1, 1, 1)},
    {"scale": 0.35, "color": (1, 1, 0.8, 1)},
], frame_rate=8, loop=True)

# Reproducir
entity.play_anim("walk")         # Loop infinito
entity.play_anim_once("hit")     # Una vez

# Detener
entity.stop_anim("walk")
entity.stop_all_anims()
```

**Tipos de frame soportados:**

| Key | Tipo | Ejemplo | Descripción |
|-----|------|---------|-------------|
| `hpr` | tuple (h,p,r) | `{"hpr": (45, 0, 0)}` | Rotación completa |
| `h` | float | `{"h": 45}` | Heading (izq/der) |
| `p` | float | `{"p": 15}` | Pitch (arriba/abajo) |
| `r` | float | `{"r": 10}` | Roll (inclinación) |
| `scale` | float o tuple | `{"scale": 0.5}` | Escala (uniforme o XYZ) |
| `color` | tuple (r,g,b,a) | `{"color": (1,0,0,1)}` | Color RGBA |
| `pos` | tuple (x,y,z) | `{"pos": (0,0,1)}` | Posición absoluta |
| `pos_offset` | tuple (x,y,z) | `{"pos_offset": (0,0,0.5)}` | Offset relativo |
| `target` | str | `{"target": "arm"}` | Nodo hijo donde aplicar |
| `joint` | str | `{"joint": "arm"}` | Nombre del joint |
| `joint_hpr` | tuple | `{"joint_hpr": (45,0,0)}` | Rotación del joint |
| `joint_pos` | tuple | `{"joint_pos": (0,0,1)}` | Posición del joint |
| `model` | str | `{"model": "models/walk.egg"}` | Swap de modelo |

### Nodos hijos (brazos, armas, escudos)

```python
# Crear nodo hijo con modelo
player.add_child_node("arm", "models/arm.egg")

# Crear nodo hijo vacío
player.add_child_node("weapon_slot")

# Eliminar nodo hijo
player.remove_child_node("arm")

# Acceder al nodo hijo
arm = player.child_nodes["arm"]
```

### Joint manipulation (esqueleto)

```python
# Exponer un joint del modelo (requiere modelo con esqueleto)
joint = player.expose_joint("arm_joint")

# Los joints se almacenan en entity.joints
player.joints["arm_joint"].setH(45)
```

### Model swapping

```python
# Cambiar modelo completo
player.swap_model("models/walk.egg")
```

### Métodos a sobreescribir en subclases

```python
def update(self, dt):
    """Se llama cada frame"""
    pass

def die(self):
    """Se llama al morir"""
    pass

def on_contact_enter(self, other):
    """Al tocar otra entidad"""
    pass

def on_contact_exit(self, other):
    """Al separarse de otra entidad"""
    pass
```

### Ciclo de vida

```
1. __init__()    → Crea nodo, se suscribe a eventos
2. update(dt)    → Se llama cada frame desde Level
3. on_contact_*  → Se llaman por CollisionSystem
4. die()         → Se llama si life <= 0
5. destroy()     → Limpia nodo, se desuscribe de eventos
```

---

## Character

Subclase de EntityBase para personajes con movimiento y apuntar.

**Archivo:** `character.py`
**Hereda de:** EntityBase

### Propiedades adicionales

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `tile_size` | float | Tamaño del tile para colisiones |
| `grid_x` | int | Posición X en la grilla |
| `grid_y` | int | Posición Y en la grilla |
| `aim_dx` | float | Dirección de apuntado X |
| `aim_dy` | float | Dirección de apuntado Y |
| `shoot_cooldown` | float | Cooldown actual del disparo |
| `shoot_rate` | float | Tiempo entre disparos (segundos) |

### Métodos

```python
# Movimiento con colisión a tiles
character.move(dx, dy, dt, tiles=None)
# dx, dy: dirección normalizada
# dt: delta time
# tiles: lista de tiles para colisión (None = sin colisión)
# El movimiento se aplica por eje independiente (permite deslizarse langs de paredes)

# Apuntar (cambia orientación visual)
character.aim(dx, dy)
# Usa atan2(dx, -dy) para orientación isométrica

# Disparar (stub, sobreescribir en subclases)
character.shoot()
```

### Colisión con tiles

```python
character._is_walkable(x, y, tiles)
# Retorna True si la posición (x, y) es caminable
# Verifica contra tiles no-walkable con radio tile_size * 0.5
```

---

## Player

Subclase de Character para el jugador controlado por humano.

**Archivo:** `player.py`
**Hereda de:** Character

### Propiedades

| Propiedad | Valor | Fuente |
|-----------|-------|--------|
| `entity_type` | `"player"` | Hardcoded |
| `life` | 100 | `settings.json → game.player_life` |
| `speed` | 5.0 | `settings.json → game.player_speed` |

### Métodos

```python
player.update(dt)    # Llama a Character.update()
player.die()         # Emite "player_died" además de "entity_died"
```

### Eventos

| Evento | Descripción |
|--------|-------------|
| `player_died` | Emitido cuando el jugador muere |

---

## Enemy

Subclase de Character para enemigos con AI básica.

**Archivo:** `enemy.py`
**Hereda de:** Character

### Propiedades

| Propiedad | Valor | Fuente |
|-----------|-------|--------|
| `entity_type` | `"enemy"` | Hardcoded |
| `life` | 30 | `settings.json → game.enemy_life` |
| `speed` | 2.5 | `settings.json → game.enemy_speed` |
| `attack_range` | tile_size * 3 | Calculado |
| `aggro_range` | tile_size * 6 | Calculado |

### AI

```python
enemy._update_ai(dt)
```

**Comportamiento:**
1. Si está fuera de `aggro_range` → no hace nada (idle)
2. Si está dentro de `aggro_range` pero fuera de `attack_range` → se mueve hacia el jugador
3. Si está dentro de `attack_range` → apunta al jugador (no ataca aún, shoot está deshabilitado)

**Flujo:**
```
aggro_range (6 tiles) → detecta jugador
  └── attack_range (3 tiles) → se acerca
       └── distância < attack_range → apunta (futuro: ataca)
```

### Subclases futuras

```python
class ShooterEnemy(Enemy):
    """Enemigo que dispara"""
    pass

class MeleeEnemy(Enemy):
    """Enemigo cuerpo a cuerpo"""
    pass
```

---

## Tile

Entidad estática del mapa. Genera geometría visual con CardMaker.

**Archivo:** `tile.py`
**Hereda de:** EntityBase

### Propiedades

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `walkable` | bool | Si se puede caminar sobre él |
| `damage` | int | Daño al pisar (0 = ninguno) |
| `grid_x` | int | Posición X en la grilla |
| `grid_y` | int | Posición Y en la grilla |
| `tile_size` | float | Tamaño de la celda |

### Geometría visual

| Tipo | Caras | Color | Textura |
|------|-------|-------|---------|
| `floor` | 1 (plano horizontal) | Verde oscuro | `floor.png` |
| `wall` | 5 (top + 4 lados) | Marrón | `wall.png` |
| `door` | 1 | Amarillo | `door.png` |
| `chest` | 1 | Dorado | `chest.png` |

### TileTextureCache

Singleton que gestiona la carga y cache de texturas.

```python
cache = TileTextureCache.get_instance()
tex = cache.get_texture("wall", game)  # Retorna Texture o None
cache.clear()  # Limpia el cache
```

**Ubicación de texturas:** `assets/textures/` (relativo a la raíz del proyecto)

### Colores

```python
TILE_COLORS = {
    "wall": (0.55, 0.45, 0.35, 1.0),
    "floor": (0.3, 0.35, 0.25, 1.0),
    "door": (0.7, 0.6, 0.25, 1.0),
    "chest": (0.9, 0.75, 0.15, 1.0),
}
```

### Sistema de texturas

Los tiles soportan texturas PNG. El sistema usa un cache (`TileTextureCache`) que carga cada textura una sola vez.

**Texturas esperadas en `assets/textures/`:**
```
assets/textures/
  ├── wall.png
  ├── floor.png
  ├── door.png
  └── chest.png
```

**Configuración de texturas (en `tile.py`):**
```python
TILE_TEXTURES = {
    "wall": "wall.png",
    "floor": "floor.png",
    "door": "door.png",
    "chest": "chest.png",
}
```

**Comportamiento:**
1. Si la textura existe en `assets/textures/` → se aplica al tile
2. Si no existe → usa color sólido de `TILE_COLORS` (fallback)
3. Las texturas se cachean (no se recargan por cada tile)

**Filtrado de textura:**
```python
tex.setMagfilter(Texture.FTNearest)  # Pixel art (nítido, sin suavizar)
tex.setMagfilter(Texture.FTLinear)   # Suavizado (bordes suaves)
```

**Para agregar texturas:**
1. Coloca las imágenes `.png` en `assets/textures/`
2. Los nombres deben coincidir con `TILE_TEXTURES`
3. El juego funciona sin texturas (usa colores sólidos)

---

## Projectile

Entidad proyectil con velocidad, daño y lifetime.

**Archivo:** `projectile.py`
**Hereda de:** EntityBase

### Propiedades

| Propiedad | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `owner` | EntityBase | — | Entidad que disparó |
| `speed` | float | 15.0 | Velocidad de movimiento |
| `damage` | int | 10 | Daño al impactar |
| `lifetime` | float | 3.0 | Tiempo de vida (segundos) |
| `age` | float | 0.0 | Tiempo transcurrido |
| `direction` | Vec3 | — | Vector de dirección normalizado |

### Métodos

```python
projectile.update(dt)        # Mueve el proyectil en su dirección
projectile.should_destroy()  # True si age >= lifetime o !alive
projectile.destroy()         # Elimina el nodo
```

### Comportamiento

1. Se genera en la posición del owner + offset en dirección del disparo
2. Se mueve cada frame en `direction * speed * dt`
3. Después de `lifetime` segundos, se marca como muerto
4. CollisionSystem lo destruye al impactar una entidad (excepto el owner)

### Visual

Cuadrado amarillo (CardMaker) orientado con `setP(-90)` para vista cenital.

---

## Ejemplo completo: crear una entidad animada

```python
from src.entities.player import Player

# Crear jugador
player = Player(game, model_name="models/smiley", grid_pos=(2, 2))

# Crear brazo como nodo hijo
player.add_child_node("arm")

# Registrar animación de walk
player.register_anim("walk", [
    {"target": "arm", "hpr": (0, 0, 0)},
    {"target": "arm", "hpr": (15, 0, 0)},
    {"target": "arm", "hpr": (0, 0, 0)},
    {"target": "arm", "hpr": (-15, 0, 0)},
    {"target": "arm", "hpr": (0, 0, 0)},
], frame_rate=8, loop=True)

# Registrar animación de hit
player.register_anim("hit", [
    {"color": (1, 0.5, 0.5, 1)},
    {"color": (1, 0.3, 0.3, 1)},
    {"color": (1, 1, 1, 1)},
], frame_rate=12, loop=False)

# Detectar contacto
def on_touch(self, other):
    if other.entity_type == "enemy":
        self.take_damage(1)
        self.play_anim_once("hit")

player.on_contact_enter = lambda other: on_touch(player, other)

# Iniciar walk
player.play_anim("walk")
```
