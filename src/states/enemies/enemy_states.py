"""Concrete AI states for enemies.

States transition by name via Enemy.set_state_by_name(), so they do not
reference each other and can live in a single module without imports
between them. The set of available states is chosen per enemy.
"""
from src.states.enemies.enemy_state import EnemyState


class IdleState(EnemyState):
    """Player out of aggro range: do nothing."""

    def update(self, dt):
        context = self._player_context()
        if not context:
            return

        dist = context[2]
        if dist <= self.enemy.aggro_range:
            if dist <= self.enemy.attack_range:
                self.enemy.set_state_by_name("attack")
            else:
                self.enemy.set_state_by_name("chase")


class ChaseState(EnemyState):
    """Player inside aggro range but outside attack range: move toward it."""

    def update(self, dt):
        context = self._player_context()
        if not context:
            return

        nx, ny, dist, level = context
        if dist > self.enemy.aggro_range:
            self.enemy.set_state_by_name("idle")
            return

        if dist <= self.enemy.attack_range:
            self.enemy.set_state_by_name("attack")
            return

        self.enemy.move(nx, ny, dt, level.tiles)
        self.enemy.aim(nx, ny)


class ShootState(EnemyState):
    """Player inside attack range: shoot and keep aiming."""

    def update(self, dt):
        context = self._player_context()
        if not context:
            return

        nx, ny, dist, level = context
        if dist > self.enemy.attack_range:
            self.enemy.set_state_by_name("chase")
            return

        self.enemy.shoot(level)
        self.enemy.aim(nx, ny)


class MeleeAttackState(EnemyState):
    """Player inside attack range: bite on a cooldown timer.

    Damage comes from state logic (distance via _player_context), not from
    the contact system: entity_enter fires once per contact episode, which
    would let a permanently-attached dog bite only once. The FSM owns the
    decision to bite; the contact tracking stays available for other uses.
    """

    def enter(self):
        self._cooldown = 0.0

    def update(self, dt):
        context = self._player_context()
        if not context:
            return

        nx, ny, dist, level = context
        if dist > self.enemy.attack_range:
            self.enemy.set_state_by_name("chase")
            return

        self.enemy.aim(nx, ny)

        self._cooldown -= dt
        if self._cooldown > 0:
            return

        self._cooldown = self.enemy.attack_cooldown
        level.player.take_damage(self.enemy.melee_damage)
