import os
from panda3d.core import CardMaker, Vec4, Texture
from src.core.warn_once import warn_once
from src.entities.entity_base import EntityBase
from src.entities.model_loader import load_entity_model, resolve_visual


TILE_COLORS = {
    "wall": (0.55, 0.45, 0.35, 1.0),
    "floor": (0.3, 0.35, 0.25, 1.0),
    "door": (0.7, 0.6, 0.25, 1.0),
    "door_open": (0.35, 0.55, 0.35, 1.0),
    "chest": (0.9, 0.75, 0.15, 1.0),
    "chest_open": (0.55, 0.5, 0.3, 1.0),
    "barrier": (0.2, 0.2, 0.25, 1.0),
}

TILE_TEXTURES = {
    "wall": "wall.png",
    "floor": "floor.png",
    "door": "door.png",
    "chest": "chest.png",
}


class TileTextureCache:
    _instance = None

    def __init__(self):
        self._cache = {}
        self._textures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets",
            "textures",
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_texture(self, tile_type, game):
        if tile_type in self._cache:
            return self._cache[tile_type]

        tex = self._load_texture(tile_type, game)
        self._cache[tile_type] = tex
        return tex

    def _load_texture(self, tile_type, game):
        filename = TILE_TEXTURES.get(tile_type)
        if not filename:
            return None

        filepath = os.path.join(self._textures_dir, filename)
        if not os.path.exists(filepath):
            return None

        tex = game.loader.loadTexture(filepath)
        if tex:
            tex.setMagfilter(Texture.FTNearest)
            tex.setMinfilter(Texture.FTNearest)
        return tex

    def clear(self):
        self._cache.clear()


class Tile(EntityBase):
    """Static map cell with split floor/wall visuals.

    - wall: scaled unit box (assets/models/tile_box.glb) with its BASE
      at z=0 rising to wall_height.
    - floor/door/chest: flat CardMaker card lying in the XY plane at
      z=floor_card_z (avoids z-fighting between adjacent tiles).

    CardMaker generates cards in the XZ plane (normal -Y, vertical),
    so the floor card needs setP(-90) to lie flat with normal +Z.
    This was verified empirically on Panda3D 1.10.16: without the
    pitch the card stands vertical (tightBounds Y extent ~0).
    """

    def __init__(self, game, tile_data, tile_size=1.0):
        EntityBase.__init__(self, game, tile_data["type"])

        self.walkable = tile_data["walkable"]
        self.damage = tile_data["damage"]
        self.grid_x = tile_data["grid_x"]
        self.grid_y = tile_data["grid_y"]
        self.tile_size = tile_size
        self.texture = None
        # Door/chest state: opened gates consume a key on entry; chests are
        # opened by the player's interact action.
        self.opened = False
        self._visual_box = None

        old_node = self.node
        self.node = self._create_visual()
        if old_node is not None:
            # Drop the bare placeholder NodePath created by EntityBase so
            # it is not left orphaned.
            try:
                old_node.removeNode()
            except Exception as exc:
                warn_once(
                    "tile.placeholder.remove",
                    f"[Tile] removeNode placeholder failed: {exc!r}",
                )
        world_x = self.grid_x * tile_size
        world_y = self.grid_y * tile_size
        self.node.setPos(world_x, world_y, 0)

    def _tile_cfg(self, key):
        # Single source of truth: config owns these values, no Python
        # defaults duplicating them. Missing keys fail fast.
        settings = getattr(self.game, "settings", None)
        getter = getattr(settings, "get", None)
        value = None
        if getter is not None:
            try:
                value = getter("game." + key, None)
            except Exception as exc:
                raise ValueError(
                    "[visual] tile config 'game.%s' lookup failed: %r"
                    % (key, exc)
                ) from exc
        if value is None:
            raise ValueError(
                "[visual] no value for tile config 'game.%s': "
                "Tile declares no class visual, so the config default is required."
                % key
            )
        return value

    def _create_visual(self):
        vis = self.game.render.attachNewNode("tile_vis")
        s = self.tile_size
        color = TILE_COLORS.get(self.entity_type, (0.4, 0.4, 0.4, 1.0))

        cache = TileTextureCache.get_instance()
        self.texture = cache.get_texture(self.entity_type, self.game)

        if self.entity_type in ("wall", "barrier", "door", "chest"):
            return self._create_wall_visual(vis, s, color)

        return self._create_floor_visual(vis, s, color)

    def _create_wall_visual(self, vis, s, color):
        # Tile declares no class visual: model comes from the config
        # default (game.tile_model) via the shared resolver.
        model_path = resolve_visual(self.entity_type, type(self), self.game)[0]
        box, _, _ = load_entity_model(self.game, model_path)
        box.reparentTo(vis)

        wall_h = self._tile_cfg("wall_height")
        box.setScale(s, s, wall_h)
        box.setPos(0, 0, wall_h / 2.0)

        if self.texture:
            box.setTexture(self.texture)
        else:
            box.setColor(Vec4(color[0], color[1], color[2], 1))

        self._visual_box = box
        return vis

    def _create_floor_visual(self, vis, s, color):
        card_z = self._tile_cfg("floor_card_z")
        maker = CardMaker("tile_floor")
        maker.setFrame(-s / 2.0, s / 2.0, -s / 2.0, s / 2.0)
        card = vis.attachNewNode(maker.generate())
        # CardMaker cards are born vertical (XZ plane, normal -Y);
        # pitch -90 lays the card flat with normal +Z.
        card.setP(-90)
        card.setPos(0, 0, card_z)

        if self.texture:
            card.setTexture(self.texture)
        else:
            card.setColor(Vec4(color[0], color[1], color[2], 1))

        return vis

    def open(self):
        """Mark this gate opened and swap its visual. Idempotent.

        Used by both doors (key consumed by Character._is_walkable) and
        chests (opened by Level via the interact action). Recolor + lower
        the box so the gate reads as "open hatch".
        """
        if self.opened:
            return
        self.opened = True
        self.walkable = True
        if self._visual_box is None:
            return
        color_key = "door_open" if self.entity_type == "door" else "chest_open"
        color = TILE_COLORS.get(color_key, TILE_COLORS.get(self.entity_type, (0.4, 0.4, 0.4, 1.0)))
        try:
            self._visual_box.setColor(Vec4(color[0], color[1], color[2], 1))
            # Halve height and drop to floor so the opened gate reads
            # as an open hatch instead of a wall.
            wall_h = self._tile_cfg("wall_height") * 0.5
            self._visual_box.setScale(self.tile_size, self.tile_size, wall_h)
            self._visual_box.setPos(0, 0, wall_h / 2.0)
        except Exception as exc:
            warn_once(
                f"tile.open.{self.entity_type}",
                f"[Tile] open() recolor failed: {exc!r}",
            )

    def destroy(self):
        EntityBase.destroy(self)
