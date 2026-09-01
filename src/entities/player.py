from panda3d.core import CardMaker, Vec4
from src.entities.character import Character


class Player(Character):
    def __init__(self, game, model_name=None, grid_pos=(0, 0), tile_size=1.0):
        super().__init__(game, "player", model_name, grid_pos, tile_size)

        self.life = game.settings.get("game.player_life", 100)
        self.max_life = self.life
        self.speed = game.settings.get("game.player_speed", 5.0)

        self._add_marker()

    def _add_marker(self):
        cm = CardMaker("player_marker")
        cm.setFrame(-0.3, 0.3, -0.3, 0.3)
        marker = self.node.attachNewNode(cm.generate())
        marker.setZ(0.6)
        marker.setP(-90)
        marker.setColor(Vec4(0.1, 0.8, 0.2, 0.8))

    def update(self, dt):
        super().update(dt)

    def die(self):
        super().die()
        self.game.event_bus.emit("player_died")
