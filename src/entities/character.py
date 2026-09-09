from panda3d.core import Vec4
import math
from src.entities.entity_base import EntityBase


class Character(EntityBase):
    def __init__(self, game, entity_type="character", model_name=None, grid_pos=(0, 0), tile_size=1.0):
        super().__init__(game, entity_type, model_name)

        self.tile_size = tile_size
        self.grid_x = grid_pos[0]
        self.grid_y = grid_pos[1]
        self._walkable_radius = tile_size * 0.5

        self.aim_dx = 0
        self.aim_dy = 1
        self.shoot_cooldown = 0.0
        self.shoot_rate = 0.25

        world_x = self.grid_x * tile_size
        world_y = self.grid_y * tile_size
        self.node.setPos(world_x, world_y, 0.0)

        if entity_type == "player":
            self.node.setScale(0.4)
        else:
            self.node.setScale(0.5)

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

    def _is_walkable(self, x, y, tiles):
        for tile in tiles:
            if not tile.walkable:
                tx, ty = tile.node.getX(), tile.node.getY()
                if abs(x - tx) < self._walkable_radius and abs(y - ty) < self._walkable_radius:
                    return False
        return True

    def aim(self, dx, dy):
        if dx != 0 or dy != 0:
            self.aim_dx = dx
            self.aim_dy = dy
            angle = math.degrees(math.atan2(dx, -dy))
            self.node.setH(angle)

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
