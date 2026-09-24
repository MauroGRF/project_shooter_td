from src.entities.collectables.collectable import Collectable


class LevelExit(Collectable):
    COLOR = (0.9, 0.3, 0.9, 1.0)

    def __init__(self, game, entity_type="exit", grid_pos=(0, 0),
                 tile_size=1.0, next_level=None, **params):
        Collectable.__init__(self, game, entity_type, grid_pos, tile_size, **params)
        self.next_level = next_level

    def on_collect(self, player):
        self.game.event_bus.emit("level_complete", self.next_level)
