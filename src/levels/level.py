from src.entities.tile import Tile
from src.entities.player import Player
from src.entities.enemy import Enemy
from src.systems.physics import Physics
from src.systems.collision import CollisionSystem
from src.systems.animation_system import AnimationSystem
from src.systems.camera import CameraSystem


class Level:
    def __init__(self, game, level_data):
        self.game = game
        self.data = level_data
        self.tile_size = game.settings.get("game.tile_size", 1.0)

        self.tiles = []
        self.entities = []
        self.projectiles = []
        self.player = None

        self.physics = Physics(game)
        self.collision = CollisionSystem(game)
        self.animation = AnimationSystem(game)
        self.camera = CameraSystem(game)

        self.root = self.game.render.attachNewNode("level_root")

    def build(self):
        self._build_tiles()
        self._build_player()
        self._build_enemies()
        self._setup_camera()

    def _build_tiles(self):
        for row in self.data["tiles"]:
            for tile_data in row:
                if tile_data["type"] == "spawn_player":
                    continue
                tile = Tile(self.game, tile_data, self.tile_size)
                tile.node.reparentTo(self.root)
                self.tiles.append(tile)

    def _build_player(self):
        spawn = self.data["player_spawn"]
        if spawn is None:
            spawn = (0, 0)

        model_name = "models/smiley"
        self.player = Player(
            self.game,
            model_name=model_name,
            grid_pos=spawn,
            tile_size=self.tile_size,
        )
        self.player.node.reparentTo(self.root)
        self.entities.append(self.player)
        self.game.input_manager.bind_player(self.player)

    def _build_enemies(self):
        model_name = "models/panda-model"
        for spawn in self.data["enemy_spawns"]:
            enemy = Enemy(
                self.game,
                model_name=model_name,
                grid_pos=spawn,
                tile_size=self.tile_size,
            )
            enemy.node.reparentTo(self.root)
            self.entities.append(enemy)

    def _setup_camera(self):
        width = self.data["width"] * self.tile_size
        height = self.data["height"] * self.tile_size
        center_x = width / 2.0
        center_y = height / 2.0
        self.camera.setup(center_x, center_y)

    def update(self, dt):
        self.physics.update(dt, self.entities + self.projectiles, self.tiles)
        self.collision.update(self.entities, self.projectiles, self.tiles)
        self.animation.update(dt)
        self.camera.update(dt)

        for projectile in self.projectiles[:]:
            projectile.update(dt)
            if projectile.should_destroy():
                self.remove_projectile(projectile)

        for entity in self.entities[:]:
            entity.update(dt)
            if entity.is_dead():
                self.remove_entity(entity)

    def add_projectile(self, projectile):
        projectile.node.reparentTo(self.root)
        self.projectiles.append(projectile)

    def remove_projectile(self, projectile):
        if projectile in self.projectiles:
            self.projectiles.remove(projectile)
            projectile.destroy()

    def remove_entity(self, entity):
        if entity == self.player:
            self.game.state_machine.change_state("menu")
            return
        if entity in self.entities:
            self.entities.remove(entity)
            entity.destroy()

    def destroy(self):
        for entity in self.entities:
            entity.destroy()
        for projectile in self.projectiles:
            projectile.destroy()
        for tile in self.tiles:
            tile.destroy()
        self.entities.clear()
        self.projectiles.clear()
        self.tiles.clear()
        self.root.removeNode()
