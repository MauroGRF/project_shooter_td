from panda3d.core import CardMaker, Vec4

from src.entities.entity_base import EntityBase


class Collectable(EntityBase):
    """Base pickup: +1 coin on player contact, then subclass hook.

    Subclasses override on_collect(player) for extra effects (score,
    weapon, level exit, events). Collision systems skip projectile
    damage for anything with collectable = True.
    """

    collectable = True
    COLOR = (1.0, 0.9, 0.2, 1.0)

    def __init__(self, game, entity_type="collectable", grid_pos=(0, 0),
                 tile_size=1.0, **params):
        self._collected = False
        EntityBase.__init__(self, game, entity_type)
        self.tile_size = tile_size
        self.grid_x = grid_pos[0]
        self.grid_y = grid_pos[1]
        self.node.setPos(grid_pos[0] * tile_size, grid_pos[1] * tile_size, 0.0)
        self._create_visual()

    def _create_visual(self):
        cm = CardMaker("collectable")
        cm.setFrame(-0.25, 0.25, -0.25, 0.25)
        card = self.node.attachNewNode(cm.generate())
        card.setP(-90)
        card.setZ(0.3)
        card.setColor(Vec4(*self.COLOR))

    def on_contact_enter(self, other):
        if self._collected or not self.alive:
            return
        if getattr(other, "entity_type", None) != "player":
            return
        self._collected = True
        self._collect(other)

    def _collect(self, player):
        player.add_coin(1)
        self.on_collect(player)
        self.alive = False

    def on_collect(self, player):
        pass
