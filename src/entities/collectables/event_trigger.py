from src.entities.collectables.collectable import Collectable


class EventTrigger(Collectable):
    COLOR = (1.0, 0.5, 0.1, 1.0)

    def __init__(self, game, entity_type="trigger", grid_pos=(0, 0),
                 tile_size=1.0, event_name="collectable_event", payload=None,
                 **params):
        Collectable.__init__(self, game, entity_type, grid_pos, tile_size, **params)
        self.event_name = event_name
        self.payload = payload

    def on_collect(self, player):
        self.game.event_bus.emit(self.event_name, self.payload)
