from panda3d.core import CardMaker, Vec4
from src.entities.character import Character


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

    def _add_marker(self):
        cm = CardMaker("enemy_marker")
        cm.setFrame(-0.3, 0.3, -0.3, 0.3)
        marker = self.node.attachNewNode(cm.generate())
        marker.setZ(0.6)
        marker.setP(-90)
        marker.setColor(Vec4(0.9, 0.1, 0.1, 0.8))

    def update(self, dt):
        Character.update(self, dt)
        self._update_ai(dt)

    def _update_ai(self, dt):
        if self.game.state_machine.current_name != "gameplay":
            return

        gameplay = self.game.state_machine.get_state("gameplay")
        if not gameplay or not gameplay.level or not gameplay.level.player:
            return

        player = gameplay.level.player
        player_pos = player.get_position()
        my_pos = self.get_position()

        dx = player_pos[0] - my_pos[0]
        dy = player_pos[1] - my_pos[1]
        dist = (dx**2 + dy**2) ** 0.5

        if dist > self.aggro_range:
            return

        if dist > 0:
            nx = dx / dist
            ny = dy / dist

            if dist > self.attack_range:
                self.move(nx, ny, dt, gameplay.level.tiles)
            else:
                self.shoot(gameplay.level)

            self.aim(nx, ny)
