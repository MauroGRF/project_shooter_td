from panda3d.core import CardMaker, Vec4
from src.entities.character import Character
from src.states.enemies.enemy_states import ChaseState, IdleState, MeleeAttackState, ShootState


class Enemy(Character):
    def __init__(self, game, model_name=None, grid_pos=(0, 0), tile_size=1.0):
        super().__init__(game, "enemy", model_name, grid_pos, tile_size)

        self.life = game.settings.get("game.enemy_life", 30)
        self.max_life = self.life
        self.speed = game.settings.get("game.enemy_speed", 2.5)
        self.attack_range = tile_size * 3
        self.aggro_range = tile_size * 6
        self.shoot_rate = 1.0

        self._add_marker()

        # Available AI transitions for this enemy. Variations (turret, dog)
        # change this dict; states themselves never change.
        self.states = {
            "idle": IdleState,
            "chase": ChaseState,
            "attack": ShootState,
        }
        self.state = None
        self.set_state_by_name("idle")

    def set_state(self, state):
        """Transition the enemy AI to a new state (exit current, enter new)."""
        if self.state:
            self.state.exit()
        self.state = state
        state.enter()

    def set_state_by_name(self, name):
        """Transition by state name. Missing states are a no-op."""
        state_class = self.states.get(name)
        if state_class:
            self.set_state(state_class(self))

    def _add_marker(self):
        cm = CardMaker("enemy_marker")
        cm.setFrame(-0.3, 0.3, -0.3, 0.3)
        marker = self.node.attachNewNode(cm.generate())
        marker.setZ(0.6)
        marker.setP(-90)
        marker.setColor(Vec4(0.9, 0.1, 0.1, 0.8))

    def update(self, dt):
        Character.update(self, dt)
        self.state.update(dt)


class Dog(Enemy):
    """Melee enemy variant: fast, fragile, bites instead of shooting.

    Shows the payoff of the data-driven state refactor: a new enemy is just
    a different states dict plus its own stats, no new transition logic.
    """

    def __init__(self, game, model_name=None, grid_pos=(0, 0), tile_size=1.0):
        super().__init__(game, model_name, grid_pos, tile_size)

        self.life = game.settings.get("game.dog_life", 15)
        self.max_life = self.life
        self.speed = game.settings.get("game.dog_speed", 5.0)
        self.attack_range = tile_size * game.settings.get("game.dog_attack_range", 0.8)
        self.aggro_range = tile_size * game.settings.get("game.dog_aggro_range", 6.0)
        self.melee_damage = game.settings.get("game.dog_damage", 10)
        self.attack_cooldown = game.settings.get("game.dog_attack_cooldown", 1.0)

        # Same state names as the base enemy; only the attack behavior differs.
        self.states = {
            "idle": IdleState,
            "chase": ChaseState,
            "attack": MeleeAttackState,
        }
        self.set_state_by_name("idle")
