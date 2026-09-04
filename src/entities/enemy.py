from panda3d.core import CardMaker, Vec4
from src.entities.character import Character
from src.states.enemies.enemy_states import IdleState


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

        self.state = IdleState(self)
        self.state.enter()

    def set_state(self, state):
        """Transition the enemy AI to a new state (exit current, enter new)."""
        self.state.exit()
        self.state = state
        state.enter()
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
