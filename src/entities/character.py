from panda3d.core import Vec4
import math
from src.entities.entity_base import EntityBase
from src.entities.model_loader import resolve_visual
from src.systems.physics import WALK_RADIUS_FACTOR, is_position_walkable
from src.core.warn_once import warn_once


class Character(EntityBase):
    # Collision box half-extents (hx, hy) in world units, measured from
    # the visual's tight bounds (node origin == box center). Subclasses
    # override with their own visual size. None = legacy square
    # (tile_size * WALK_RADIUS_FACTOR).
    COLLISION_HALF_EXTENTS = None

    def __init__(self, game, entity_type="character", model_name=None, grid_pos=(0, 0), tile_size=1.0,
                 model_scale=None, model_rotation=None, model_offset=None):
        # Single source of truth: class attrs win, else config default.
        # Explicit params are per-slot overrides (default None = no override).
        resolved = resolve_visual(entity_type, type(self), game)
        if model_name is None:
            model_name = resolved[0]
        if model_scale is None:
            model_scale = resolved[1]
        if model_rotation is None:
            model_rotation = resolved[2]
        if model_offset is None:
            model_offset = resolved[3]
        super().__init__(game, entity_type, model_name,
                         model_scale=model_scale, model_offset=model_offset,
                         model_rotation=model_rotation)

        self.tile_size = tile_size
        self.grid_x = grid_pos[0]
        self.grid_y = grid_pos[1]
        self._walkable_half_extents = self.get_collision_half_extents()

        self.aim_dx = 0
        self.aim_dy = 1
        self.shoot_cooldown = 0.0
        self.shoot_rate = 0.25
        # Base heading correction (model_rotation H) preserved across aim().
        # setH() keeps P/R, so only H needs re-adding here.
        try:
            self._base_h = float(model_rotation[0]) if isinstance(model_rotation, (list, tuple)) else float(model_rotation)
        except (TypeError, ValueError):
            self._base_h = 0.0

        world_x = self.grid_x * tile_size
        world_y = self.grid_y * tile_size
        self.node.setPos(world_x, world_y, 0.0)

        # Scale comes from the resolved visual (class wins, else config
        # default) and was already applied by EntityBase. No magic
        # fallback here: each class/config owns its scale.

        # Re-apply offset additively: setPos above reset the absolute
        # offset EntityBase applied before spawn positioning.
        if self._model_offset is not None:
            try:
                if isinstance(self._model_offset, (list, tuple)):
                    self.node.setPos(
                        self.node.getX() + float(self._model_offset[0]),
                        self.node.getY() + float(self._model_offset[1]),
                        self.node.getZ() + float(self._model_offset[2]),
                    )
                else:
                    self.node.setZ(self.node.getZ() + float(self._model_offset))
            except Exception as exc:
                warn_once(
                    f"character.offset.{self.entity_type}",
                    f"[Character] bad model_offset on {self.entity_type}: {exc!r}",
                )

    def move(self, dx, dy, dt, tiles=None):
        if not self.alive:
            return
        # old move preserved: interpret dx,dy as direction and move by speed*dt
        pos = self.node.getPos()
        speed = self.get_move_speed()
        disp_x = dx * speed * dt
        disp_y = dy * speed * dt
        self.move_by(disp_x, disp_y, tiles)

    def get_move_speed(self):
        factor = getattr(self, 'move_speed_factor', 1.0)
        return self.speed * factor

    def move_by(self, disp_x, disp_y, tiles=None):
        """Move the entity by world displacement (units). Handles substeps and sliding.

        disp_x, disp_y: world-space displacement in X/Y to apply for this update.
        """
        if not self.alive:
            return
        pos = self.node.getPos()

        # split movement into substeps to avoid tunneling and improve collision sliding
        max_step = max(self.tile_size * 0.25, 0.05)
        steps = 1
        max_disp = max(abs(disp_x), abs(disp_y))
        if max_disp > max_step:
            steps = int((max_disp // max_step) + 1)

        step_x = disp_x / steps
        step_y = disp_y / steps

        for i in range(steps):
            cur_x = self.node.getX()
            cur_y = self.node.getY()
            nx = cur_x + step_x
            ny = cur_y + step_y
            if tiles:
                moved_x = False
                moved_y = False
                if self._is_walkable(nx, cur_y, tiles):
                    self.node.setX(nx)
                    moved_x = True
                if self._is_walkable(self.node.getX(), ny, tiles):
                    self.node.setY(ny)
                    moved_y = True
                # sliding: if blocked on both axes, try smaller step towards target
                if not moved_x and not moved_y:
                    nx2 = cur_x + step_x * 0.5
                    ny2 = cur_y + step_y * 0.5
                    if self._is_walkable(nx2, cur_y, tiles):
                        self.node.setX(nx2)
                    if self._is_walkable(self.node.getX(), ny2, tiles):
                        self.node.setY(ny2)
            else:
                self.node.setPos(nx, ny, pos.getZ())

        self.grid_x = int(round(self.node.getX() / self.tile_size))
        self.grid_y = int(round(self.node.getY() / self.tile_size))

    def get_collision_half_extents(self):
        """Return this entity's (hx, hy) collision half-extents."""
        if self.COLLISION_HALF_EXTENTS is not None:
            return (
                float(self.COLLISION_HALF_EXTENTS[0]),
                float(self.COLLISION_HALF_EXTENTS[1]),
            )
        legacy = self.tile_size * WALK_RADIUS_FACTOR
        return (legacy, legacy)

    def _is_walkable(self, x, y, tiles):
        return is_position_walkable(
            x, y, tiles, half_extents=self._walkable_half_extents
        )

    def aim(self, dx, dy):
        if dx != 0 or dy != 0:
            self.aim_dx = dx
            self.aim_dy = dy
            angle = math.degrees(math.atan2(dx, -dy))
            self.node.setH(angle + self._base_h)

    def shoot(self, level):
        if not self.alive or self.shoot_cooldown > 0:
            return
        if not level:
            return

        from src.entities.projectile import Projectile
        direction = (self.aim_dx, self.aim_dy)

        if self.entity_type == "player":
            color = Vec4(0.0, 1.0, 0.5, 1.0)
        else:
            color = Vec4(1.0, 0.3, 0.0, 1.0)

        projectile = Projectile(
            self.game,
            owner=self,
            position=self.get_position(),
            direction=direction,
            color=color,
        )
        level.add_projectile(projectile)
        self.shoot_cooldown = self.shoot_rate

    def update(self, dt):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
