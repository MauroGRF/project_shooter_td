from direct.showbase.ShowBase import ShowBase
from panda3d.core import Point3, Vec3, Plane


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

    def _bind_key(self, key, event_names):
        """Bind press/release for key state, including Panda3D modifier-prefixed
        variants (e.g. while Shift is held, 'w' arrives as 'shift-w')."""
        for name in event_names:
            self.game.accept(name, self._set_key, [key, True])
            self.game.accept(f"{name}-up", self._set_key, [key, False])

    def _bind_action(self, event_names, action):
        for name in event_names:
            self.game.accept(name, self._on_action, [action])

    def _setup_keybindings(self):
        self._bind_key("w", ["w", "shift-w"])
        self._bind_key("s", ["s", "shift-s"])
        self._bind_key("a", ["a", "shift-a"])
        self._bind_key("d", ["d", "shift-d"])

        self._bind_key("arrow_up", ["arrow_up", "shift-arrow_up"])
        self._bind_key("arrow_down", ["arrow_down", "shift-arrow_down"])
        self._bind_key("arrow_left", ["arrow_left", "shift-arrow_left"])
        self._bind_key("arrow_right", ["arrow_right", "shift-arrow_right"])

        self._bind_action(["enter", "shift-enter"], "enter_pressed")
        self._bind_action(["escape", "shift-escape"], "escape_pressed")
        self._bind_action(["p", "shift-p"], "pause_pressed")

        self._bind_key("space", ["space", "shift-space"])

        # mouse input
        self.game.accept("mouse1", self._on_mouse1)

    def _is_shift_down(self):
        try:
            return bool(self.game.getShift())
        except Exception:
            return False

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
        if self.game.state_machine.current_name != "gameplay":
            return
        if not self.player or not self.player.alive:
            return

        dx, dy = self.get_movement()
        sprint_intent = self._is_shift_down()
        self.player.request_move(dx, dy, sprint_intent, dt)

        # aiming (keyboard preferred only if no mouse), mouse preferred otherwise
        aim_dx, aim_dy = self.get_aim()
        try:
            if self.game.mouseWatcherNode.hasMouse():
                mpos = self.game.mouseWatcherNode.getMouse()
                near = Point3()
                far = Point3()
                self.game.cam.node().getLens().extrude(mpos, near, far)
                from_point = self.game.render.getRelativePoint(self.game.cam, near)
                to_point = self.game.render.getRelativePoint(self.game.cam, far)
                plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
                intersect = Point3()
                if plane.intersectsLine(intersect, from_point, to_point):
                    world_x, world_y = intersect.getX(), intersect.getY()
                    px, py, pz = self.player.get_position()
                    vx = world_x - px
                    vy = world_y - py
                    dist = (vx * vx + vy * vy) ** 0.5
                    if dist > 0.001:
                        vx /= dist
                        vy /= dist
                        self.player.aim(vx, vy)
            else:
                if aim_dx != 0 or aim_dy != 0:
                    self.player.aim(aim_dx, aim_dy)
        except Exception:
            pass

        if self.keys["space"]:
            gameplay = self.game.state_machine.get_state("gameplay")
            level = gameplay.level if gameplay else None
            self.player.shoot(level)

    def _on_mouse1(self):
        if self.game.state_machine.current_name != "gameplay":
            return
        if not self.player or not self.player.alive:
            return
        gameplay = self.game.state_machine.get_state("gameplay")
        level = gameplay.level if gameplay else None
        self.player.shoot(level)