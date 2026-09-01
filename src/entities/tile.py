import os
from panda3d.core import Vec4, Texture
from src.entities.entity_base import EntityBase


TILE_COLORS = {
    "wall": (0.55, 0.45, 0.35, 1.0),
    "floor": (0.3, 0.35, 0.25, 1.0),
    "door": (0.7, 0.6, 0.25, 1.0),
    "chest": (0.9, 0.75, 0.15, 1.0),
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
    def __init__(self, game, tile_data, tile_size=1.0):
        EntityBase.__init__(self, game, tile_data["type"])

        self.walkable = tile_data["walkable"]
        self.damage = tile_data["damage"]
        self.grid_x = tile_data["grid_x"]
        self.grid_y = tile_data["grid_y"]
        self.tile_size = tile_size
        self.texture = None

        self.node = self._create_visual()
        world_x = self.grid_x * tile_size
        world_y = self.grid_y * tile_size
        self.node.setPos(world_x, world_y, 0)

    def _create_visual(self):
        from panda3d.core import CardMaker

        vis = self.game.render.attachNewNode("tile_vis")
        s = self.tile_size
        color = TILE_COLORS.get(self.entity_type, (0.4, 0.4, 0.4, 1.0))

        cache = TileTextureCache.get_instance()
        self.texture = cache.get_texture(self.entity_type, self.game)

        floor_card = self._make_card("floor_card", vis, s, color, floor=True)

        if self.entity_type == "wall":
            wall_h = s
            self._make_card("wall_top", vis, s, color, z=wall_h, floor=True, shade=0.9)
            self._make_card("wall_front", vis, s, color, y=-s / 2, shade=1.0)
            self._make_card("wall_back", vis, s, color, y=s / 2, h=180, shade=0.95)
            self._make_card("wall_left", vis, s, color, x=-s / 2, h=90, shade=0.85)
            self._make_card("wall_right", vis, s, color, x=s / 2, h=-90, shade=0.85)

        return vis

    def _make_card(self, name, parent, s, color, x=0, y=0, z=0, h=0, floor=False, shade=1.0):
        from panda3d.core import CardMaker

        cm = CardMaker(name)
        cm.setFrame(-s / 2, s / 2, -s / 2, s / 2)
        card = parent.attachNewNode(cm.generate())

        card.setPos(x, y, z)
        if floor:
            card.setP(-90)
            card.setZ(card.getZ() - 0.05)
        if h != 0:
            card.setH(h)

        if self.texture:
            card.setTexture(self.texture)
        else:
            card.setColor(Vec4(color[0] * shade, color[1] * shade, color[2] * shade, 1))

        return card

    def destroy(self):
        if self.node:
            self.node.removeNode()
            self.node = None
