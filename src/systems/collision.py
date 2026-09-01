class CollisionSystem:
    def __init__(self, game):
        self.game = game
        self._contact_pairs = set()
        self._id_to_entity = {}

    def update(self, entities, projectiles, tiles):
        self._check_projectile_entity_collisions(projectiles, entities)
        self._check_entity_tile_collisions(entities, tiles)
        self._check_entity_entity_collisions(entities + projectiles)

    def _check_projectile_entity_collisions(self, projectiles, entities):
        for projectile in projectiles[:]:
            if not projectile.alive:
                continue

            proj_pos = projectile.node.getPos()
            hit_range = 0.8

            for entity in entities:
                if not entity.alive:
                    continue
                if entity == projectile.owner:
                    continue

                ent_pos = entity.node.getPos()
                dx = proj_pos.getX() - ent_pos.getX()
                dy = proj_pos.getY() - ent_pos.getY()
                dist = (dx**2 + dy**2) ** 0.5

                if dist < hit_range:
                    entity.take_damage(projectile.damage)
                    projectile.alive = False
                    self.game.event_bus.emit(
                        "projectile_hit",
                        projectile,
                        entity,
                    )
                    break

    def _check_entity_tile_collisions(self, entities, tiles):
        for entity in entities:
            if not entity.alive:
                continue
            if not hasattr(entity, "tile_size"):
                continue

            pos = entity.node.getPos()
            tile_size = entity.tile_size

            for tile in tiles:
                if tile.walkable:
                    continue

                tx = tile.node.getX()
                ty = tile.node.getY()
                half = tile_size * 0.5

                dx = pos.getX() - tx
                dy = pos.getY() - ty
                abs_dx = abs(dx)
                abs_dy = abs(dy)

                if abs_dx < half and abs_dy < half:
                    if abs_dx > abs_dy:
                        push = half - abs_dx + 0.01
                        if dx > 0:
                            entity.node.setX(entity.node.getX() + push)
                        else:
                            entity.node.setX(entity.node.getX() - push)
                    else:
                        push = half - abs_dy + 0.01
                        if dy > 0:
                            entity.node.setY(entity.node.getY() + push)
                        else:
                            entity.node.setY(entity.node.getY() - push)

    def _check_entity_entity_collisions(self, entities):
        alive = [e for e in entities if e.alive and e.node]
        current_pairs = set()
        self._id_to_entity.clear()

        for i in range(len(alive)):
            e1 = alive[i]
            id1 = id(e1)
            self._id_to_entity[id1] = e1
            r1 = getattr(e1, "tile_size", 0.5) * 0.5

            for j in range(i + 1, len(alive)):
                e2 = alive[j]
                id2 = id(e2)
                self._id_to_entity[id2] = e2
                r2 = getattr(e2, "tile_size", 0.5) * 0.5

                pos1 = e1.node.getPos()
                pos2 = e2.node.getPos()
                dx = pos1.getX() - pos2.getX()
                dy = pos1.getY() - pos2.getY()
                dist = (dx**2 + dy**2) ** 0.5

                if dist < r1 + r2:
                    pair = (min(id1, id2), max(id1, id2))
                    current_pairs.add(pair)

        entered = current_pairs - self._contact_pairs
        exited = self._contact_pairs - current_pairs

        for pair in entered:
            e1 = self._id_to_entity.get(pair[0])
            e2 = self._id_to_entity.get(pair[1])
            if e1 and e2:
                self.game.event_bus.emit("entity_enter", e1, e2)

        for pair in exited:
            e1 = self._id_to_entity.get(pair[0])
            e2 = self._id_to_entity.get(pair[1])
            if e1 and e2:
                self.game.event_bus.emit("entity_exit", e1, e2)

        self._contact_pairs = current_pairs
