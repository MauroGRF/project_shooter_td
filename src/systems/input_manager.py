from direct.showbase.ShowBase import ShowBase


class InputManager:
    def __init__(self, game: ShowBase):
        self.game = game
        self.player = None

        self.keys = {
            "w": False, "s": False, "a": False, "d": False,
            "arrow_up": False, "arrow_down": False,
            "arrow_left": False, "arrow_right": False,
            "space": False,
        }

        self._setup_keybindings()

    def _setup_keybindings(self):
        self.game.accept("w", self._set_key, ["w", True])
        self.game.accept("w-up", self._set_key, ["w", False])
        self.game.accept("s", self._set_key, ["s", True])
        self.game.accept("s-up", self._set_key, ["s", False])
        self.game.accept("a", self._set_key, ["a", True])
        self.game.accept("a-up", self._set_key, ["a", False])
        self.game.accept("d", self._set_key, ["d", True])
        self.game.accept("d-up", self._set_key, ["d", False])

        self.game.accept("arrow_up", self._set_key, ["arrow_up", True])
        self.game.accept("arrow_up-up", self._set_key, ["arrow_up", False])
        self.game.accept("arrow_down", self._set_key, ["arrow_down", True])
        self.game.accept("arrow_down-up", self._set_key, ["arrow_down", False])
        self.game.accept("arrow_left", self._set_key, ["arrow_left", True])
        self.game.accept("arrow_left-up", self._set_key, ["arrow_left", False])
        self.game.accept("arrow_right", self._set_key, ["arrow_right", True])
        self.game.accept("arrow_right-up", self._set_key, ["arrow_right", False])

        self.game.accept("enter", self._on_action, ["enter_pressed"])
        self.game.accept("escape", self._on_action, ["escape_pressed"])
        self.game.accept("p", self._on_action, ["pause_pressed"])

        self.game.accept("space", self._set_key, ["space", True])
        self.game.accept("space-up", self._set_key, ["space", False])

    def _set_key(self, key, value):
        self.keys[key] = value

    def _on_action(self, event_name):
        self.game.event_bus.emit(event_name)

    def bind_player(self, player):
        self.player = player

    def get_movement(self):
        dx = 0.0
        dy = 0.0
        if self.keys["w"]:
            dy += 1.0
        if self.keys["s"]:
            dy -= 1.0
        if self.keys["a"]:
            dx -= 1.0
        if self.keys["d"]:
            dx += 1.0
        return (dx, dy)

    def get_aim(self):
        dx = 0.0
        dy = 0.0
        if self.keys["arrow_up"]:
            dy += 1.0
        if self.keys["arrow_down"]:
            dy -= 1.0
        if self.keys["arrow_left"]:
            dx -= 1.0
        if self.keys["arrow_right"]:
            dx += 1.0
        return (dx, dy)

    def update(self, dt):
        if not self.player:
            return

        dx, dy = self.get_movement()
        if dx != 0 or dy != 0:
            length = (dx**2 + dy**2) ** 0.5
            dx /= length
            dy /= length
            gameplay = self.game.state_machine.get_state("gameplay")
            tiles = gameplay.level.tiles if gameplay and gameplay.level else []
            self.player.move(dx, dy, dt, tiles)

        aim_dx, aim_dy = self.get_aim()
        if aim_dx != 0 or aim_dy != 0:
            self.player.aim(aim_dx, aim_dy)

        if self.keys["space"]:
            gameplay = self.game.state_machine.get_state("gameplay")
            level = gameplay.level if gameplay else None
            self.player.shoot(level)
