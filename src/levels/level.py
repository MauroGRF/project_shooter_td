from src.entities.tile import Tile
from src.entities.player import Player
from src.entities.enemies import Dog, Enemy
from src.entities.collectables import create_collectable
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
        self.barriers = []
        self.entities = []
        self.projectiles = []
        self.melee_hitboxes = []
        self.player = None

        self.physics = Physics(game)
        self.collision = CollisionSystem(game)
        self.animation = AnimationSystem(game)
        self.camera = CameraSystem(game)

        self.root = self.game.render.attachNewNode("level_root")
        self.game.event_bus.subscribe("clear_barriers", self._on_clear_barriers)
        self.game.event_bus.subscribe("interact_pressed", self._on_interact_pressed)

    def build(self):
        self._build_tiles()
        self._build_player()
        self._build_enemies()
        self._build_collectables()
        self._setup_camera()

    # Tile types that mark entity spawns. Kept for back-compat; the
    # builder below lays a floor base under every non-wall cell anyway.
    SPAWN_TILE_TYPES = ("spawn_player", "spawn_enemy", "spawn_dog")

    # Element tiles sit ON TOP of the floor base (solid, walkable False).
    ELEMENT_TILE_TYPES = ("door", "barrier", "chest")

    def _build_tiles(self):
        for row in self.data["tiles"]:
            for tile_data in row:
                t = tile_data["type"]
                gx, gy = tile_data["grid_x"], tile_data["grid_y"]
                if t == "wall":
                    tile = Tile(self.game, tile_data, self.tile_size)
                    tile.node.reparentTo(self.root)
                    self.tiles.append(tile)
                    continue
                # Base terrain: floor under everything that is not a wall,
                # whether or not an element spawns on top. No more holes.
                floor = Tile(
                    self.game,
                    {"type": "floor", "grid_x": gx, "grid_y": gy,
                     "walkable": True, "damage": 0},
                    self.tile_size,
                )
                floor.node.reparentTo(self.root)
                self.tiles.append(floor)
                if t in self.ELEMENT_TILE_TYPES:
                    tile = Tile(self.game, tile_data, self.tile_size)
                    tile.node.reparentTo(self.root)
                    self.tiles.append(tile)
                    if t == "barrier":
                        self.barriers.append(tile)

    def _build_collectables(self):
        meta = self.data.get("meta") or {}
        for spawn in self.data.get("collectable_spawns") or []:
            params = dict(spawn.get("params") or {})
            if spawn["type"] == "next_level":
                payload = dict(params.get("payload") or {})
                payload.setdefault("level", meta.get("next_level"))
                params["payload"] = payload
            collectable = create_collectable(
                spawn["type"],
                self.game,
                (spawn["grid_x"], spawn["grid_y"]),
                self.tile_size,
                **params,
            )
            collectable.node.reparentTo(self.root)
            self.entities.append(collectable)

    def _on_clear_barriers(self, *args):
        # The floor base already exists under every barrier, so clearing
        # only removes the element tile. No hole left behind.
        for tile in self.barriers:
            if tile in self.tiles:
                self.tiles.remove(tile)
            tile.destroy()
        self.barriers.clear()

    def _on_interact_pressed(self, *args):
        """Open the closest adjacent chest (chebyshev ≤ 1) and drop loot.

        Single chest per press: only the first adjacent closed chest is
        opened. Re-pressing E with no chest nearby is a no-op.
        """
        if not self.player or not self.player.alive:
            return
        px = self.player.grid_x
        py = self.player.grid_y
        for tile in self.tiles:
            if tile.entity_type != "chest" or tile.opened:
                continue
            if max(abs(tile.grid_x - px), abs(tile.grid_y - py)) <= 1:
                tile.open()
                self._drop_chest_loot()
                return

    def _drop_chest_loot(self):
        from src.entities.collectables.chest_loot import roll_chest_loot

        kind, value = roll_chest_loot()
        if kind == "coins":
            self.player.add_coin(value)
        elif kind == "score":
            self.player.add_score(value)
        elif kind == "refill":
            self.player.reload_weapon()
        elif kind == "heal":
            self.player.heal(value)

    def _build_player(self):
        spawn = self.data["player_spawn"]
        if spawn is None:
            raise ValueError("Level data has no player_spawn (missing 'P' tile)")

        # Visual owned by Player (class attrs win, else config default).
        self.player = Player(
            self.game,
            grid_pos=spawn,
            tile_size=self.tile_size,
        )
        self.player.node.reparentTo(self.root)
        self.entities.append(self.player)
        self.game.input_manager.bind_player(self.player)

    def _build_enemies(self):
        # Visuals owned by Enemy/Dog (class attrs win, else config default).
        for spawn in self.data["enemy_spawns"]:
            enemy = Enemy(
                self.game,
                grid_pos=spawn,
                tile_size=self.tile_size,
            )
            enemy.node.reparentTo(self.root)
            self.entities.append(enemy)

        for spawn in self.data["dog_spawns"]:
            dog = Dog(
                self.game,
                grid_pos=spawn,
                tile_size=self.tile_size,
            )
            dog.node.reparentTo(self.root)
            self.entities.append(dog)

    def _setup_camera(self):
        width = self.data["width"] * self.tile_size
        height = self.data["height"] * self.tile_size
        center_x = width / 2.0
        center_y = height / 2.0
        self.camera.setup(center_x, center_y)
        # Bounds clamp keeps the panned look-at inside the map.
        self.camera.set_level_bounds(self.data["width"], self.data["height"], self.tile_size)

    def update(self, dt):
        self.physics.update(dt, self.entities + self.projectiles, self.tiles)
        self.collision.update(dt, self.entities, self.projectiles, self.tiles, self.melee_hitboxes)
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
                # player death changes state (destroys this level): stop iterating
                if self.game.state_machine.current_name != "gameplay":
                    break

        for hb in self.melee_hitboxes[:]:
            hb.update(dt)
            if not hb.alive:
                self.remove_melee_hitbox(hb)

    def add_projectile(self, projectile):
        projectile.node.reparentTo(self.root)
        self.projectiles.append(projectile)

    def add_melee_hitbox(self, hitbox):
        hitbox.node.reparentTo(self.root)
        self.melee_hitboxes.append(hitbox)

    def remove_melee_hitbox(self, hitbox):
        if hitbox in self.melee_hitboxes:
            self.melee_hitboxes.remove(hitbox)
            hitbox.destroy()

    def remove_projectile(self, projectile):
        if projectile in self.projectiles:
            self.projectiles.remove(projectile)
            projectile.destroy()

    def remove_entity(self, entity):
        if entity == self.player:
            entity.destroy()
            self.player = None
            self.game.state_machine.change_state("menu")
            return
        if entity in self.entities:
            self.entities.remove(entity)
            entity.destroy()

    def destroy(self):
        self.game.event_bus.unsubscribe("clear_barriers", self._on_clear_barriers)
        self.game.event_bus.unsubscribe("interact_pressed", self._on_interact_pressed)
        for entity in self.entities:
            entity.destroy()
        for projectile in self.projectiles:
            projectile.destroy()
        for hb in self.melee_hitboxes:
            hb.destroy()
        for tile in self.tiles:
            tile.destroy()
        self.entities.clear()
        self.projectiles.clear()
        self.melee_hitboxes.clear()
        self.tiles.clear()
        self.root.removeNode()
