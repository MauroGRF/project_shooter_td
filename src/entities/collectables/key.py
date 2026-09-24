from src.entities.collectables.collectable import Collectable


class Key(Collectable):
    """Pickup that grants one key to the player (used to open doors).

    Same contact-and-collect flow as a coin; the extra effect is
    `player.add_key(1)` instead of score/weapon/exit.
    """

    COLOR = (1.0, 0.85, 0.2, 1.0)

    def on_collect(self, player):
        player.add_key(1)