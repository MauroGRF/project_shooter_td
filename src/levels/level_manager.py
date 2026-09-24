import os


TILE_CHARS = {
    "S": "floor",
    "W": "wall",
    "D": "door",
    "P": "spawn_player",
    "E": "spawn_enemy",
    "F": "spawn_dog",
    "C": "chest",
    "B": "barrier",
}

COLLECTABLE_CHARS = {
    "o": "coin",
    "m": "score",
    "g": "weapon",
    "x": "exit",
    "K": "key",
    "t": "trigger",
    "n": "next_level",
}

TILE_LEGEND = {
    "floor": {"walkable": True, "damage": 0},
    "wall": {"walkable": False, "damage": 0},
    "door": {"walkable": False, "damage": 0},
    "chest": {"walkable": False, "damage": 0},
    "barrier": {"walkable": False, "damage": 0},
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

        meta = {}
        raw_lines = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    body = stripped[1:].strip()
                    if ":" in body:
                        key, _, value = body.partition(":")
                        key = key.strip()
                        value = value.strip()
                        if key and value and " " not in key:
                            meta[key] = value
                    continue
                raw_lines.append(stripped)

        grid = [line.split() for line in raw_lines]
        return self._parse_grid(grid, meta)

    def _parse_grid(self, grid, meta=None):
        meta = meta or {}
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
        collectable_spawns = []

        for row_idx, row in enumerate(grid):
            tile_row = []
            for col_idx, cell in enumerate(row):
                if cell in COLLECTABLE_CHARS:
                    spawn = {
                        "type": COLLECTABLE_CHARS[cell],
                        "grid_x": col_idx,
                        "grid_y": row_idx,
                    }
                    if spawn["type"] == "next_level":
                        spawn["params"] = {
                            "event_name": "change_level",
                            "payload": {"level": meta.get("next_level")},
                        }
                    collectable_spawns.append(spawn)
                    tile_type = "floor"
                elif cell not in TILE_CHARS:
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
            "collectable_spawns": collectable_spawns,
            "meta": meta,
        }
