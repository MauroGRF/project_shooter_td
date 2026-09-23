import math
from panda3d.core import Vec3, CardMaker, Vec4
from src.entities.entity_base import EntityBase


class Projectile(EntityBase):
    def __init__(self, game, owner, position, direction, color=None,
                 damage=None, speed=None):
        EntityBase.__init__(self, game, "projectile")

        self.owner = owner
        # Optional per-shot overrides; fall back to shared projectile config.
        self.speed = (
            speed
            if speed is not None
            else game.settings.get("game.projectile_speed", 15.0)
        )
        self.damage = (
            damage
            if damage is not None
            else game.settings.get("game.projectile_damage", 10)
        )
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
        self.bullet_card = bullet

    def reflect(self, new_owner):
        """Bounce the projectile back; from now on it belongs to new_owner."""
        if not self.alive:
            return
        self.owner = new_owner
        self.direction = -self.direction
        self.age = 0.0
        self.node.setX(self.node.getX() + self.direction.getX() * 0.4)
        self.node.setY(self.node.getY() + self.direction.getY() * 0.4)
        if self.bullet_card:
            self.bullet_card.setColor(Vec4(0.2, 1.0, 1.0, 1.0))

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
        EntityBase.destroy(self)
