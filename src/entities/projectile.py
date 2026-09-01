import math
from panda3d.core import Vec3, CardMaker, Vec4
from src.entities.entity_base import EntityBase


class Projectile(EntityBase):
    def __init__(self, game, owner, position, direction, color=None):
        EntityBase.__init__(self, game, "projectile")

        self.owner = owner
        self.speed = game.settings.get("game.projectile_speed", 15.0)
        self.damage = game.settings.get("game.projectile_damage", 10)
        self.lifetime = 3.0
        self.age = 0.0

        self.direction = Vec3(direction[0], direction[1], 0.0).normalized()

        self.node.setPos(
            position[0] + self.direction.getX() * 0.5,
            position[1] + self.direction.getY() * 0.5,
            position[2] + 0.3,
        )

        cm = CardMaker("bullet")
        cm.setFrame(-0.15, 0.15, -0.15, 0.15)
        bullet = self.node.attachNewNode(cm.generate())
        if color is None:
            color = Vec4(1.0, 0.3, 0.0, 1.0)
        bullet.setColor(color)
        bullet.setP(-90)

    def update(self, dt):
        if not self.alive:
            return
        self.age += dt
        if self.age >= self.lifetime:
            self.alive = False
            return

        dx = self.direction.getX() * self.speed * dt
        dy = self.direction.getY() * self.speed * dt
        self.node.setX(self.node.getX() + dx)
        self.node.setY(self.node.getY() + dy)

    def should_destroy(self):
        return not self.alive

    def destroy(self):
        if self.node:
            self.node.removeNode()
            self.node = None
