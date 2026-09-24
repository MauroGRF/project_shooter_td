import os


TILE_CHARS = {
    "S": "floor",
    "W": "wall",
    "D": "door",
    "P": "spawn_player",
    "E": "spawn_enemy",
    "F": "spawn_dog",
    "C": "chest",
}

TILE_LEGEND = {
    "floor": {"walkable": True, "damage": 0},
    "wall": {"walkable": False, "damage": 0},
    "door": {"walkable": True, "damage": 0},
    "chest": {"walkable": False, "damage": 0},
    "spawn_player": {"walkable": True, "damage": 0},
    "spawn_enemy": {"walkable": True, "damage": 0},
    "spawn_dog": {"walkable": True, "damage": 0},
}


class LevelManager:
    def __init__(self, game):
        self.game = game
        self._levels_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets",
            "levels",
        )

    def load(self, filename):
        filepath = os.path.join(self._levels_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Level file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]

        grid = []
        for line in lines:
            row = line.split()
            grid.append(row)

        return self._parse_grid(grid)

    def _parse_grid(self, grid):
        if not grid or not grid[0]:
            raise ValueError("Level grid is empty")
        height = len(grid)
        width = len(grid[0])
        for row_idx, row in enumerate(grid):
            if len(row) != width:
                raise ValueError(
                    f"Irregular level grid: row {row_idx} has {len(row)} "
                    f"cells, expected {width}"
                )

        tiles = []
        player_spawn = None
        enemy_spawns = []
        dog_spawns = []

        for row_idx, row in enumerate(grid):
            tile_row = []
            for col_idx, cell in enumerate(row):
                if cell not in TILE_CHARS:
                    print(
                        f"[LevelManager] WARNING: unknown tile char "
                        f"'{cell}' at ({col_idx}, {row_idx}); using floor"
                    )
                    tile_type = "floor"
                else:
                    tile_type = TILE_CHARS[cell]

                tile_data = {
                    "type": tile_type,
                    "grid_x": col_idx,
                    "grid_y": row_idx,
                    "walkable": TILE_LEGEND.get(tile_type, TILE_LEGEND["floor"])["walkable"],
                    "damage": TILE_LEGEND.get(tile_type, TILE_LEGEND["floor"])["damage"],
                }
                tile_row.append(tile_data)

                if cell == "P":
                    player_spawn = (col_idx, row_idx)
                elif cell == "E":
                    enemy_spawns.append((col_idx, row_idx))
                elif cell == "F":
                    dog_spawns.append((col_idx, row_idx))

            tiles.append(tile_row)

        return {
            "width": width,
            "height": height,
            "tiles": tiles,
            "player_spawn": player_spawn,
            "enemy_spawns": enemy_spawns,
            "dog_spawns": dog_spawns,
        }
