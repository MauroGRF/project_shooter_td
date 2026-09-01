from src.states.state_base import StateBase
from src.levels.level_manager import LevelManager


class LoadingState(StateBase):
    def enter(self, **kwargs):
        self.level_file = kwargs.get("level_file", "level_01.lvl")
        self._load_level()

    def _load_level(self):
        level_manager = LevelManager(self.game)
        level_data = level_manager.load(self.level_file)

        from src.states.gameplay_state import GameplayState
        gameplay = self.game.state_machine.get_state("gameplay")
        gameplay.level_data = level_data
        self.game.state_machine.change_state("gameplay")

    def exit(self):
        pass
