# Single shared walkability box (fraction of tile_size).
# Character, Collision and Physics all use per-entity collision boxes so
# solid tiles block movement identically everywhere.
from src.core.warn_once import warn_once

WALK_RADIUS_FACTOR = 0.5  # legacy fallback: square half-extent for entities with no box.


def get_collision_half_extents(entity):
    """Return the (hx, hy) collision half-extents for an entity.

    Prefers entity.get_collision_half_extents(), then the
    COLLISION_HALF_EXTENTS class attr. Falls back to the legacy square
    (tile_size * WALK_RADIUS_FACTOR) so entities without a box keep the
    old behavior.
    """
    getter = getattr(entity, "get_collision_half_extents", None)
    if callable(getter):
        try:
            half_extents = getter()
            if half_extents is not None:
                return (float(half_extents[0]), float(half_extents[1]))
        except Exception as exc:
            warn_once(
                f"physics.extents.{type(entity).__name__}",
                f"[Physics] get_collision_half_extents failed on "
                f"{type(entity).__name__}: {exc!r} (using legacy box)",
            )
    half_extents = getattr(entity, "COLLISION_HALF_EXTENTS", None)
    if half_extents is not None:
        return (float(half_extents[0]), float(half_extents[1]))
    tile_size = getattr(entity, "tile_size", 1.0)
    legacy = tile_size * WALK_RADIUS_FACTOR
    return (legacy, legacy)


def is_position_walkable(x, y, tiles, radius=None, half_extents=None):
    """Shared solid-tile test used by Character and Physics.

    Box-based: (x, y) is the center of a (hx, hy) box; a solid tile
    centered on (tx, ty) with half size ts/2 blocks it when both boxes
    overlap on X and Y. The legacy radius path (square comparison) is
    kept unchanged for callers that pass radius without a box.
    """
    if half_extents is None and radius is None:
        return True
    if half_extents is None:
        for tile in tiles:
            if not tile.walkable:
                tx = tile.node.getX()
                ty = tile.node.getY()
                if abs(x - tx) < radius and abs(y - ty) < radius:
                    return False
        return True
    hx, hy = half_extents
    for tile in tiles:
        if not tile.walkable:
            tx = tile.node.getX()
            ty = tile.node.getY()
            th = getattr(tile, "tile_size", 1.0) * 0.5
            if abs(x - tx) < th + hx and abs(y - ty) < th + hy:
                return False
    return True


class Physics:
    def __init__(self, game):
        self.game = game
        self.gravity = game.settings.get("game.gravity", -20.0)

    def update(self, dt, entities, tiles=None):
        # NOTE: EntityBase always defines a `velocity` list, but nothing in
        # the game sets it (Character moves its node directly). This path is
        # currently inert for zero velocities and is kept for future use.
        for entity in entities:
            if not entity.alive:
                continue
            if hasattr(entity, "velocity") and entity.velocity:
                if entity.velocity[0] == 0 and entity.velocity[1] == 0 and entity.velocity[2] == 0:
                    continue
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
        return is_position_walkable(
            x, y, tiles, half_extents=get_collision_half_extents(entity)
        )

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
