"""Concrete AI states for enemies.

These states transition between each other, so they live in a single module
to avoid circular imports: the state graph of an enemy is strongly connected
(any state can reach any other).
"""
from src.states.enemies.enemy_state import EnemyState


class IdleState(EnemyState):
    """No line of sight to the player (or out of aggro range): do nothing."""

    def update(self, dt):
        context = self._player_context()
        if not context:
            return

        nx, ny, dist, level = context
        if dist <= self.enemy.aggro_range:
            if dist <= self.enemy.attack_range:
                self.enemy.set_state(ShootState(self.enemy))
            else:
                self.enemy.set_state(ChaseState(self.enemy))


class ChaseState(EnemyState):
    """Player inside aggro range but outside attack range: move toward it."""

    def update(self, dt):
        context = self._player_context()
        if not context:
            return

        nx, ny, dist, level = context
        if dist > self.enemy.aggro_range:
            self.enemy.set_state(IdleState(self.enemy))
            return

        if dist <= self.enemy.attack_range:
            self.enemy.set_state(ShootState(self.enemy))
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
            self.enemy.set_state(ChaseState(self.enemy))
            return

        self.enemy.shoot(level)
        self.enemy.aim(nx, ny)
