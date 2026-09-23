from src.entities.collectables.collectable import Collectable
from src.entities.collectables.event_trigger import EventTrigger
from src.entities.collectables.level_exit import LevelExit
from src.entities.collectables.score_bonus import ScoreBonus
from src.entities.collectables.weapon_pickup import WeaponPickup

COLLECTABLE_TYPES = {
    "coin": (Collectable, {}),
    "score": (ScoreBonus, {"points": 100}),
    "weapon": (WeaponPickup, {"mode": "reload"}),
    "exit": (LevelExit, {}),
    "trigger": (EventTrigger, {"event_name": "clear_barriers"}),
    "next_level": (EventTrigger, {"event_name": "change_level"}),
}


def create_collectable(type_name, game, grid_pos, tile_size=1.0, **overrides):
    cls, defaults = COLLECTABLE_TYPES[type_name]
    params = {**defaults, **overrides}
    return cls(
        game,
        entity_type=type_name,
        grid_pos=grid_pos,
        tile_size=tile_size,
        **params,
    )
