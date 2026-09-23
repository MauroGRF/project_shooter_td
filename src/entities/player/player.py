import math

from panda3d.core import CardMaker, Vec4
from src.entities.character import Character
from src.systems.status_effects import StatusEffect, StatusEffectSystem


class Player(Character):
    # Single source of truth for the player visual: the class wins over
    # config. SCALE 0.4 formalizes the old magic fallback in Character.
    MODEL = "models/smiley"
    MODEL_SCALE = 0.4
    MODEL_ROTATION = None
    MODEL_OFFSET = None
    # Tight bounds of models/smiley at scale 0.4: 0.80 x 0.80.
    COLLISION_HALF_EXTENTS = (0.4, 0.4)

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

        # dash
        self.dash_cd = game.settings.get("game.dash_cooldown", 2.5)
        self.dash_duration = game.settings.get("game.dash_duration", 0.18)
        self.dash_speed = game.settings.get("game.dash_speed", 18.0)
        self.dash_stamina_cost = game.settings.get("game.dash_stamina_cost", 25.0)
        self.dash_cooldown_timer = 0.0
        self.dash_timer = 0.0
        self.is_dashing = False
        self.dash_dir_x = 0.0
        self.dash_dir_y = 0.0

        # parry
        self.parries = 0
        self.max_parries = game.settings.get("game.max_parries", 3)
        self.parry_duration = game.settings.get("game.parry_duration", 1.0)
        self.parry_timer = 0.0
        self.is_parrying = False
        self._evade_timer = 0.0
        self._evaded = set()

        # weapons (key 0 = melee default, 1 = pistol, 2 = rifle, 3 = shotgun)
        self.weapons = game.settings.get("game.weapons", {})
        self.selected_weapon = "0"
        self.ammo_mode = "limited"
        self.weapon_ammo = {}
        for key, weapon in self.weapons.items():
            if weapon.get("type") != "melee":
                self.weapon_ammo[key] = weapon.get("ammo", 999)
        self.melee_state = None
        self._melee_hit_ids = set()
        self.melee_cd = game.settings.get("game.melee_cooldown", 1.5)
        self.melee_cooldown_timer = 0.0

        # status effects (speed multiplier etc.)
        self.status_effects = StatusEffectSystem(game)

        self._add_marker()

    def _add_marker(self, marker_height=None):
        if marker_height is None:
            marker_height = self.game.settings.get("game.marker_height", 0.6)
        cm = CardMaker("player_marker")
        cm.setFrame(-0.3, 0.3, -0.3, 0.3)
        marker = self.node.attachNewNode(cm.generate())
        marker.setZ(marker_height)
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
        if self.is_dashing:
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
        target_speed = self.get_effective_speed() * self.move_speed_factor if intent else 0.0
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

    def request_dash(self):
        if not self.alive or self.is_dashing or self.dash_cooldown_timer > 0.0:
            return
        if self.stamina < self.dash_stamina_cost:
            return
        # dash toward the current movement direction; fallback to aim direction
        dx, dy = self._vx, self._vy
        length = math.hypot(dx, dy)
        if length < 1e-3:
            dx, dy = self.aim_dx, self.aim_dy
            length = math.hypot(dx, dy)
            if length < 1e-3:
                return
        self.dash_dir_x = dx / length
        self.dash_dir_y = dy / length
        self.stamina -= self.dash_stamina_cost
        self.is_dashing = True
        self.dash_timer = self.dash_duration
        self.dash_cooldown_timer = self.dash_cd

    def request_parry(self):
        if not self.alive or self.is_parrying or self.parries <= 0:
            return
        self.parries -= 1
        self.is_parrying = True
        self.parry_timer = self.parry_duration

    def gain_parry(self):
        if not self.alive:
            return
        self.parries = min(self.max_parries, self.parries + 1)

    def select_weapon(self, key):
        if key in self.weapons:
            self.selected_weapon = key

    def toggle_ammo_mode(self):
        if self.ammo_mode == "limited":
            self.ammo_mode = "infinite"
        else:
            self.ammo_mode = "limited"
            self._refill_ammo()

    def _refill_ammo(self):
        for key, weapon in self.weapons.items():
            if weapon.get("type") != "melee":
                self.weapon_ammo[key] = weapon.get("ammo", 999)

    def get_effective_speed(self):
        return self.speed * self.status_effects.get_modifier("speed_multiplier")

    def get_move_speed(self):
        return self.get_effective_speed() * getattr(self, "move_speed_factor", 1.0)

    def apply_status(self, effect_name):
        if not self.alive:
            return
        config = self.game.settings.get("game.player_effects", {}).get(effect_name)
        if not config:
            return
        duration = config.get("duration", 5.0)
        modifiers = {k: v for k, v in config.items() if k != "duration"}
        self.status_effects.add_effect(StatusEffect(effect_name, duration, modifiers))

    def shoot(self, level):
        if not self.alive or self.shoot_cooldown > 0.0:
            return
        if not level:
            return

        weapon = self.weapons.get(self.selected_weapon, {})
        if not weapon:
            return

        is_melee = weapon.get("type") == "melee"
        if is_melee and self.melee_cooldown_timer > 0.0:
            return

        # out of ammo in limited mode: cannot fire
        if (
            not is_melee
            and self.ammo_mode == "limited"
            and self.weapon_ammo.get(self.selected_weapon, 0) <= 0
        ):
            return

        self.shoot_cooldown = weapon.get("fire_rate", 0.25)
        if is_melee:
            self.melee_cooldown_timer = self.melee_cd
            self._start_melee(weapon, level)
        else:
            if self.ammo_mode == "limited":
                self.weapon_ammo[self.selected_weapon] -= 1
            self._fire_ranged(weapon, level)

    def _fire_ranged(self, weapon, level):
        from src.entities.projectile import Projectile

        damage = weapon.get("damage", 10)
        speed = weapon.get("projectile_speed", 15.0)
        pellets = weapon.get("pellets", 1)
        spread = weapon.get("spread", 0.0)
        color = Vec4(0.0, 1.0, 0.5, 1.0)

        offsets = []
        if pellets <= 1:
            offsets = [0.0]
        else:
            for i in range(pellets):
                offsets.append((i / (pellets - 1)) - 0.5)

        for off in offsets:
            off_rad = math.radians(off * spread)
            c = math.cos(off_rad)
            s = math.sin(off_rad)
            dx = self.aim_dx * c - self.aim_dy * s
            dy = self.aim_dx * s + self.aim_dy * c

            projectile = Projectile(
                self.game,
                owner=self,
                position=self.get_position(),
                direction=(dx, dy),
                color=color,
                damage=damage,
                speed=speed,
            )
            level.add_projectile(projectile)

    def _start_melee(self, weapon, level):
        # a swing spawns hitboxes at the player's current position as they
        # move/turn, so the trail covers the area around the player
        self._melee_hit_ids = set()
        self.melee_state = {
            "level": level,
            "timer": weapon.get("fire_rate", 0.35),
            "spawn_timer": 0.0,
            "interval": weapon.get("spawn_interval", 0.07),
            "max": weapon.get("hitboxes", 3),
            "spawned": 0,
            "damage": weapon.get("damage", 25),
            "radius": weapon.get("hitbox_radius", 0.65),
            "lifetime": weapon.get("hitbox_lifetime", 0.25),
            "blocked": False,
            "boxes": [],
        }

    def _spawn_melee_hitbox(self, melee_state):
        from src.entities.melee_hitbox import MeleeHitbox

        # spawn just in front of the player, following the CURRENT aim
        # direction so turning the camera swings the hitbox around you
        length = math.hypot(self.aim_dx, self.aim_dy)
        if length < 1e-3:
            ax, ay = 0.0, 1.0
        else:
            ax, ay = self.aim_dx / length, self.aim_dy / length
        front = melee_state["radius"] * 0.9
        px, py, pz = self.get_position()

        hb = MeleeHitbox(
            self.game,
            owner=self,
            position=(px + ax * front, py + ay * front, pz),
            damage=melee_state["damage"],
            radius=melee_state["radius"],
            lifetime=melee_state["lifetime"],
        )
        melee_state["level"].add_melee_hitbox(hb)
        melee_state["boxes"].append(hb)
        melee_state["spawned"] += 1

    def on_melee_hit(self, hitbox):
        """One hitbox connected: stop the rest of the trail."""
        if self.melee_state is None:
            return
        self.melee_state["blocked"] = True
        for hb in self.melee_state["boxes"]:
            if hb is not hitbox:
                hb.active = False

    def take_damage(self, amount):
        if self.is_parrying:
            return
        super().take_damage(amount)

    def update(self, dt):
        super().update(dt)
        # parry window
        if self.is_parrying:
            self.parry_timer -= dt
            if self.parry_timer <= 0.0:
                self.is_parrying = False
        # dodge-detection grace after a dash
        if self.is_dashing:
            self._evade_timer = 0.2
        elif self._evade_timer > 0.0:
            self._evade_timer = max(0.0, self._evade_timer - dt)
        # dash: override movement with a burst toward the dash direction
        if self.is_dashing:
            self.dash_timer -= dt
            self.move_by(
                self.dash_dir_x * self.dash_speed * dt,
                self.dash_dir_y * self.dash_speed * dt,
                self._get_tiles(),
            )
            if self.dash_timer <= 0.0:
                self.is_dashing = False
        if self.dash_cooldown_timer > 0.0:
            self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - dt)
        if self.melee_cooldown_timer > 0.0:
            self.melee_cooldown_timer = max(0.0, self.melee_cooldown_timer - dt)
        # handle stamina depletion / recovery
        if self.is_sprinting and self.is_moving:
            self.stamina = max(0.0, self.stamina - self.stamina_depletion_rate * dt)
            if self.stamina <= self.min_sprint_stamina:
                # empty stamina to avoid stuttering on/off at the boundary
                self.stamina = 0.0
                self.is_sprinting = False
        elif self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_recovery_rate * dt)

        # status effects tick
        self.status_effects.update(dt)

        # melee swing: spawn the trail over time so hitboxes follow the player path
        if self.melee_state is not None:
            ms = self.melee_state
            ms["timer"] -= dt
            if ms["timer"] <= 0.0:
                self.melee_state = None
            elif not ms["blocked"] and ms["spawned"] < ms["max"]:
                ms["spawn_timer"] -= dt
                if ms["spawn_timer"] <= 0.0:
                    ms["spawn_timer"] = ms["interval"]
                    self._spawn_melee_hitbox(ms)

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
        self.is_dashing = False
        self.is_parrying = False
        self.move_speed_factor = 1.0

    def die(self):
        super().die()
        self.game.event_bus.emit("player_died")