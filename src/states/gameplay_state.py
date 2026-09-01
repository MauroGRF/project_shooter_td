from src.states.state_base import StateBase
from src.levels.level import Level
from src.ui.hud import HUD


class GameplayState(StateBase):
    def __init__(self, game):
        StateBase.__init__(self, game)
        self.level = None
        self.hud = None
        self.level_data = None

    def enter(self, **kwargs):
        level_data = kwargs.get("level_data", self.level_data)
        if level_data is None:
            return

        self.level = Level(self.game, level_data)
        self.level.build()

        self.hud = HUD(self.game)
        self.hud.show()

        self.game.event_bus.subscribe("pause_pressed", self._on_pause)

    def exit(self):
        if self.level:
            self.level.destroy()
            self.level = None
        if self.hud:
            self.hud.hide()
            self.hud = None
        self.game.event_bus.unsubscribe("pause_pressed", self._on_pause)

    def update(self, dt):
        if self.level:
            self.level.update(dt)
        if self.hud:
            self.hud.update(dt)

    def _on_pause(self):
        self.game.state_machine.change_state("pause")
