from src.entities.collectables.collectable import Collectable


class WeaponPickup(Collectable):
    COLOR = (0.3, 0.5, 1.0, 1.0)

    def __init__(self, game, entity_type="weapon", grid_pos=(0, 0),
                 tile_size=1.0, mode="reload", weapon_key=None, **params):
        Collectable.__init__(self, game, entity_type, grid_pos, tile_size, **params)
        self.mode = mode
        self.weapon_key = weapon_key

    def on_collect(self, player):
        if self.mode == "select" and self.weapon_key:
            player.select_weapon(self.weapon_key)
        else:
            player.reload_weapon(self.weapon_key)
