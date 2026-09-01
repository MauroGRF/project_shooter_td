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

        pos = self.node.getPos()
        new_x = pos.getX() + dx * self.speed * dt
        new_y = pos.getY() + dy * self.speed * dt

        if tiles:
            if self._is_walkable(new_x, pos.getY(), tiles):
                self.node.setX(new_x)
            if self._is_walkable(self.node.getX(), new_y, tiles):
                self.node.setY(new_y)
        else:
            self.node.setPos(new_x, new_y, pos.getZ())

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
