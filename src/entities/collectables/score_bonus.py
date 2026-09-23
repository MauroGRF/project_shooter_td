from src.entities.collectables.collectable import Collectable


class ScoreBonus(Collectable):
    COLOR = (0.2, 0.9, 0.3, 1.0)

    def __init__(self, game, entity_type="score", grid_pos=(0, 0),
                 tile_size=1.0, points=100, **params):
        Collectable.__init__(self, game, entity_type, grid_pos, tile_size, **params)
        self.points = points

    def on_collect(self, player):
        player.add_score(self.points)
