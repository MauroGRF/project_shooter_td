import math

from panda3d.core import CardMaker, Vec4
from src.entities.character import Character


class Player(Character):
    def __init__(self, game, model_name=None, grid_pos=(0, 0), tile_size=1.0):
        super().__init__(game, "player", model_name, grid_pos, tile_size)

        self.life = game.settings.get("game.player_life", 100)
        self.max_life = self.life
        self.speed = game.settings.get("game.player_speed", 5.0)

        # sprint / stamina
        self.max_stamina = game.settings.get("game.player_stamina", 100.0)
        self.stamina = self.max_stamina
        self.stamina_recovery_rate = game.settings.get("game.stamina_recovery", 15.0)
        self.stamina_depletion_rate = game.settings.get("game.stamina_depletion", 30.0)
        self.sprint_multiplier = game.settings.get("game.sprint_multiplier", 1.8)
        self.min_sprint_stamina = game.settings.get("game.min_sprint_stamina", 5.0)
        self.is_sprinting = False
        self.is_moving = False

        # movement feel (exponential smoothing rates, higher = snappier)
        self.move_response = game.settings.get("game.move_response", 14.0)
        self.move_decel = game.settings.get("game.move_decel", 20.0)
        self.sprint_response = game.settings.get("game.sprint_response", 6.0)
        # speed interpolation factor (1.0 = normal speed, sprint_multiplier = sprint)
        self.move_speed_factor = 1.0
        # current scalar speed; direction is applied instantly on every frame
        self._current_speed = 0.0
        self._vx = 0.0
        self._vy = 0.0

        self._add_marker()

    def _add_marker(self):
        cm = CardMaker("player_marker")
        cm.setFrame(-0.3, 0.3, -0.3, 0.3)
        marker = self.node.attachNewNode(cm.generate())
        marker.setZ(0.6)
        marker.setP(-90)
        marker.setColor(Vec4(0.1, 0.8, 0.2, 0.8))

    def request_move(self, input_dx, input_dy, sprint_intent, dt):
        """Apply movement for one frame.

        input_dx/input_dy: raw input direction (one axis per key, can be diagonal).
        sprint_intent: True if the player is holding the sprint key.
        dt: delta time in seconds.
        """
        intent = input_dx != 0.0 or input_dy != 0.0
        self.is_moving = intent
        if not self.alive:
            self._halt()
            return

        dir_x = input_dx
        dir_y = input_dy
        if intent:
            # normalize so diagonal movement has the same speed as cardinal
            length = math.hypot(dir_x, dir_y)
            dir_x /= length
            dir_y /= length
        else:
            dir_x = 0.0
            dir_y = 0.0

        self.is_sprinting = sprint_intent and intent and self.stamina > self.min_sprint_stamina

        # smoothly ease the speed factor between walk (1.0) and sprint
        target_factor = self.sprint_multiplier if self.is_sprinting else 1.0
        if abs(self.move_speed_factor - target_factor) > 1e-3:
            blend = 1.0 - math.exp(-self.sprint_response * dt)
            self.move_speed_factor += (target_factor - self.move_speed_factor) * blend
        else:
            self.move_speed_factor = target_factor

        # ease only the scalar speed for smooth start/stop; direction changes are instant
        target_speed = self.speed * self.move_speed_factor if intent else 0.0
        diff = target_speed - self._current_speed
        if abs(diff) < 1e-3:
            self._current_speed = target_speed
        else:
            rate = self.move_decel if diff < 0 else self.move_response
            blend = 1.0 - math.exp(-rate * dt)
            self._current_speed += diff * blend

        self._vx = dir_x * self._current_speed
        self._vy = dir_y * self._current_speed

        self.move_by(self._vx * dt, self._vy * dt, self._get_tiles())

    def update(self, dt):
        super().update(dt)
        # handle stamina depletion / recovery
        if self.is_sprinting and self.is_moving:
            self.stamina = max(0.0, self.stamina - self.stamina_depletion_rate * dt)
            if self.stamina <= self.min_sprint_stamina:
                # empty stamina to avoid stuttering on/off at the boundary
                self.stamina = 0.0
                self.is_sprinting = False
        elif self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_recovery_rate * dt)

    def _get_tiles(self):
        state = self.game.state_machine.get_state("gameplay")
        if state and state.level:
            return state.level.tiles
        return []

    def _halt(self):
        self._current_speed = 0.0
        self._vx = 0.0
        self._vy = 0.0
        self.is_sprinting = False
        self.move_speed_factor = 1.0

    def die(self):
        super().die()
        self.game.event_bus.emit("player_died")