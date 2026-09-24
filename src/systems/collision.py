from src.systems.physics import get_collision_half_extents

# Combat ranges (world units). Named so tuning and tests do not hunt magic numbers.
PROJECTILE_HIT_RANGE = 0.8
# Small push so a resolved body does not re-overlap the tile next frame.
TILE_PUSH_EPSILON = 0.01


class CollisionSystem:
    def __init__(self, game):
        self.game = game
        self._contact_pairs = set()
        self._id_to_entity = {}
        self._contact_cd = {}
        self.dodge_range_extra = game.settings.get("game.dodge_range_extra", 0.9)

    def update(self, dt, entities, projectiles, tiles, melee_hitboxes=None):
        self._check_projectile_entity_collisions(projectiles, entities)
        self._check_entity_tile_collisions(entities, tiles)
        self._check_entity_entity_collisions(entities + projectiles, dt)
        if melee_hitboxes:
            self._check_melee_hitbox_collisions(melee_hitboxes, entities)

    def _check_projectile_entity_collisions(self, projectiles, entities):
        hit_range = PROJECTILE_HIT_RANGE
        dodge_range = hit_range + self.dodge_range_extra

        for projectile in projectiles[:]:
            if not projectile.alive:
                continue

            proj_pos = projectile.node.getPos()

            for entity in entities:
                if not entity.alive:
                    continue
                if entity == projectile.owner:
                    continue
                if getattr(entity, "collectable", False):
                    continue

                ent_pos = entity.node.getPos()
                dx = proj_pos.getX() - ent_pos.getX()
                dy = proj_pos.getY() - ent_pos.getY()
                dist = (dx**2 + dy**2) ** 0.5

                if entity.entity_type == "player":
                    if dist < hit_range:
                        if getattr(entity, "is_parrying", False):
                            # parry: bounce the bullet back at the enemies
                            projectile.reflect(entity)
                            self.game.event_bus.emit("projectile_reflected", projectile, entity)
                            break
                        entity.take_damage(projectile.damage)
                        projectile.alive = False
                        self.game.event_bus.emit("projectile_hit", projectile, entity)
                        break
                    if dist < dodge_range and (
                        getattr(entity, "is_dashing", False)
                        or getattr(entity, "_evade_timer", 0.0) > 0.0
                    ):
                        # a bullet came close while dodging: reward a parry charge
                        if id(projectile) not in entity._evaded:
                            entity._evaded.add(id(projectile))
                            entity.gain_parry()
                elif dist < hit_range:
                    entity.take_damage(projectile.damage)
                    projectile.alive = False
                    self.game.event_bus.emit(
                        "projectile_hit",
                        projectile,
                        entity,
                    )
                    break

    def _check_melee_hitbox_collisions(self, melee_hitboxes, entities):
        for hb in melee_hitboxes:
            if not hb.alive or not hb.active or hb.hit:
                continue
            if not hb.owner or not hb.owner.alive:
                continue

            pos = hb.node.getPos()
            for entity in entities:
                if not entity.alive:
                    continue
                if entity.entity_type != "enemy":
                    continue
                if entity is hb.owner:
                    continue
                if id(entity) in hb.owner._melee_hit_ids:
                    continue

                ent_pos = entity.node.getPos()
                dx = pos.getX() - ent_pos.getX()
                dy = pos.getY() - ent_pos.getY()
                dist = (dx**2 + dy**2) ** 0.5

                if dist < (hb.radius + getattr(entity, "tile_size", 0.5) * 0.5):
                    entity.take_damage(hb.damage)
                    hb.mark_hit()
                    hb.owner._melee_hit_ids.add(id(entity))
                    if hasattr(hb.owner, "on_melee_hit"):
                        hb.owner.on_melee_hit(hb)
                    self.game.event_bus.emit("melee_hit", hb, entity)
                    break

    def _check_entity_tile_collisions(self, entities, tiles):
        solid = [tile for tile in tiles if not tile.walkable]
        if not solid:
            return
        for entity in entities:
            if not entity.alive:
                continue
            if not hasattr(entity, "tile_size"):
                continue

            pos = entity.node.getPos()
            hx, hy = get_collision_half_extents(entity)

            for tile in solid:
                tx = tile.node.getX()
                ty = tile.node.getY()
                th = getattr(tile, "tile_size", entity.tile_size) * 0.5

                dx = pos.getX() - tx
                dy = pos.getY() - ty
                overlap_x = th + hx - abs(dx)
                overlap_y = th + hy - abs(dy)

                if overlap_x > 0 and overlap_y > 0:
                    if overlap_x < overlap_y:
                        push = overlap_x + TILE_PUSH_EPSILON
                        if dx > 0:
                            entity.node.setX(entity.node.getX() + push)
                        else:
                            entity.node.setX(entity.node.getX() - push)
                    else:
                        push = overlap_y + TILE_PUSH_EPSILON
                        if dy > 0:
                            entity.node.setY(entity.node.getY() + push)
                        else:
                            entity.node.setY(entity.node.getY() - push)

    def _check_entity_entity_collisions(self, entities, dt):
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
                    self._handle_contact_damage(e1, e2, dt)

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

    def _handle_contact_damage(self, a, b, dt):
        """Direct (melee) contact damage between player and enemies.

        If the player is parrying, the attack is reflected: the enemy takes
        the damage instead of the player.
        """
        player = None
        enemy = None
        if getattr(a, "entity_type", None) == "player":
            player, enemy = a, b
        elif getattr(b, "entity_type", None) == "player":
            player, enemy = b, a
        if player is None or getattr(enemy, "entity_type", None) != "enemy":
            return

        damage = getattr(enemy, "contact_damage", 0)
        if damage <= 0:
            return

        key = (id(player), id(enemy))
        if self._contact_cd.get(key, 0.0) > 0.0:
            self._contact_cd[key] -= dt
            return

        if getattr(player, "is_parrying", False):
            enemy.take_damage(damage)
        else:
            player.take_damage(damage)
        self._contact_cd[key] = getattr(enemy, "contact_interval", 0.6)