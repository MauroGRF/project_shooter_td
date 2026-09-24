from src.states.state_base import StateBase
from src.levels.level_manager import LevelManager


class LoadingState(StateBase):
    def enter(self, **kwargs):
        self.level_file = kwargs.get("level_file", "level_01.lvl")
        self._load_level()

    def _load_level(self):
        try:
            level_manager = LevelManager(self.game)
            level_data = level_manager.load(self.level_file)
            if level_data.get("player_spawn") is None:
                raise ValueError(
                    f"Level '{self.level_file}' has no player spawn (missing 'P' tile)"
                )
        except (FileNotFoundError, ValueError, KeyError, OSError) as e:
            print(f"[LoadingState] ERROR loading '{self.level_file}': {e}. Returning to menu.")
            self.game.state_machine.change_state("menu", error=str(e))
            return

        from src.states.gameplay_state import GameplayState
        gameplay = self.game.state_machine.get_state("gameplay")
        gameplay.level_data = level_data
        self.game.state_machine.change_state("gameplay")

    def exit(self):
        pass
