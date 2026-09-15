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
            "mouse1": False,
        }

        self._setup_keybindings()

    def _key_event_names(self, base):
        """All event names a key can arrive as, depending on held modifiers
        (Shift and Ctrl prefix the event name in Panda3D)."""
        return [
            base,
            f"shift-{base}",
            f"control-{base}",
            f"shift-control-{base}",
        ]

    def _bind_key(self, key, event_names):
        """Bind press/release for key state, including Panda3D modifier-prefixed
        variants (e.g. while Shift is held, 'w' arrives as 'shift-w')."""
        for name in event_names:
            self.game.accept(name, self._set_key, [key, True])
            self.game.accept(f"{name}-up", self._set_key, [key, False])

    def _bind_action(self, event_names, action):
        for name in event_names:
            self.game.accept(name, self._on_action, [action])

    def _bind_dash(self, event_names):
        for name in event_names:
            self.game.accept(name, self._on_dash)

    def _bind_weapon(self, event_names, weapon_key):
        for name in event_names:
            self.game.accept(name, self._on_weapon_select, [weapon_key])

    def _bind_ammo_toggle(self, event_names):
        for name in event_names:
            self.game.accept(name, self._on_toggle_ammo_mode)

    def _bind_effect(self, effect_name, event_names):
        for name in event_names:
            self.game.accept(name, self._on_apply_effect, [effect_name])

    def _setup_keybindings(self):
        self._bind_key("w", self._key_event_names("w"))
        self._bind_key("s", self._key_event_names("s"))
        self._bind_key("a", self._key_event_names("a"))
        self._bind_key("d", self._key_event_names("d"))

        self._bind_key("arrow_up", self._key_event_names("arrow_up"))
        self._bind_key("arrow_down", self._key_event_names("arrow_down"))
        self._bind_key("arrow_left", self._key_event_names("arrow_left"))
        self._bind_key("arrow_right", self._key_event_names("arrow_right"))

        self._bind_action(["enter", "shift-enter"], "enter_pressed")
        self._bind_action(["escape", "shift-escape"], "escape_pressed")
        self._bind_action(["p", "shift-p"], "pause_pressed")

        self._bind_key("space", self._key_event_names("space"))

        # mouse input (hold-to-fire; modifiers prefix mouse events too)
        self._bind_key("mouse1", self._key_event_names("mouse1"))

        # dash action
        self._bind_dash(["z", "shift-z", "control-z", "shift-control-z"])

        # ammo mode toggle (limited / infinite)
        self._bind_ammo_toggle(["l", "shift-l", "control-l", "shift-control-l"])

        # status effect test keys
        self._bind_effect("speed", ["m", "shift-m", "control-m", "shift-control-m"])

        # weapon selection (0 = melee, 1 = pistol, 2 = rifle, 3 = shotgun)
        for key in ["0", "1", "2", "3"]:
            self._bind_weapon(self._key_event_names(key), key)

    def _is_shift_down(self):
        try:
            return bool(self.game.getShift())
        except Exception:
            return False

    def _is_control_down(self):
        try:
            return bool(self.game.getControl())
        except Exception:
            return False

    def _set_key(self, key, value):
        self.keys[key] = value

    def _on_action(self, event_name):
        self.game.event_bus.emit(event_name)

    def _on_dash(self):
        if self.game.state_machine.current_name != "gameplay":
            return
        if not self.player or not self.player.alive:
            return
        self.player.request_dash()

    def _on_weapon_select(self, weapon_key):
        if self.game.state_machine.current_name != "gameplay":
            return
        if not self.player or not self.player.alive:
            return
        self.player.select_weapon(weapon_key)

    def _on_toggle_ammo_mode(self):
        if self.game.state_machine.current_name != "gameplay":
            return
        if not self.player or not self.player.alive:
            return
        self.player.toggle_ammo_mode()

    def _on_apply_effect(self, effect_name):
        if self.game.state_machine.current_name != "gameplay":
            return
        if not self.player or not self.player.alive:
            return
        self.player.apply_status(effect_name)

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

        # parry: edge-detect the Ctrl key (polled to avoid modifier-prefix issues)
        control_down = self._is_control_down()
        if control_down and not self._was_control_down:
            self.player.request_parry()
        self._was_control_down = control_down

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

        if self.keys["space"] or self.keys["mouse1"]:
            gameplay = self.game.state_machine.get_state("gameplay")
            level = gameplay.level if gameplay else None
            self.player.shoot(level)