class Physics:
    def __init__(self, game):
        self.game = game
        self.gravity = game.settings.get("game.gravity", -20.0)

    def update(self, dt, entities, tiles=None):
        for entity in entities:
            if not entity.alive:
                continue
            if hasattr(entity, "velocity") and entity.velocity:
                pos = entity.node.getPos()
                new_x = pos.getX() + entity.velocity[0] * dt
                new_y = pos.getY() + entity.velocity[1] * dt
                new_z = pos.getZ() + entity.velocity[2] * dt

                if tiles and not self._check_walkable(new_x, new_y, tiles, entity):
                    entity.velocity[0] = 0
                    entity.velocity[1] = 0
                else:
                    entity.node.setPos(new_x, new_y, new_z)

    def _check_walkable(self, x, y, tiles, entity):
        tile_size = getattr(entity, "tile_size", 2.0)
        for tile in tiles:
            if not tile.walkable:
                tx = tile.node.getX()
                ty = tile.node.getY()
                half = tile_size * 0.4
                if abs(x - tx) < half and abs(y - ty) < half:
                    return False
        return True

    def apply_gravity(self, entity, dt):
        if hasattr(entity, "velocity"):
            entity.velocity[2] += self.gravity * dt

    def apply_velocity(self, entity, dt):
        if hasattr(entity, "velocity"):
            pos = entity.node.getPos()
            new_x = pos.getX() + entity.velocity[0] * dt
            new_y = pos.getY() + entity.velocity[1] * dt
            new_z = pos.getZ() + entity.velocity[2] * dt
            entity.node.setPos(new_x, new_y, new_z)
