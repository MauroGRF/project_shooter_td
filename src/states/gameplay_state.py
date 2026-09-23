from src.states.state_base import StateBase
from src.levels.level import Level
from src.ui.hud import HUD


class GameplayState(StateBase):
    def __init__(self, game):
        StateBase.__init__(self, game)
        self.level = None
        self.hud = None
        self.level_data = None
        self._preserve_for_pause = False

    def enter(self, **kwargs):
        level_data = kwargs.get("level_data", None)
        # Resume from pause: level was preserved, just re-show HUD.
        if self.level is not None and level_data is None:
            if self.hud:
                self.hud.show()
            self.game.event_bus.subscribe("pause_pressed", self._on_pause)
            return

        if level_data is None:
            level_data = self.level_data
        if level_data is None:
            return
        self.level_data = level_data

        self.level = Level(self.game, level_data)
        self.level.build()

        self.hud = HUD(self.game)
        self.hud.show()

        self.game.event_bus.subscribe("pause_pressed", self._on_pause)

    def exit(self):
        if self._preserve_for_pause:
            # Pausing: keep level/HUD alive, only hide HUD and drop the
            # pause subscription (PauseState registers its own).
            self._preserve_for_pause = False
            if self.hud:
                self.hud.hide()
            self.game.event_bus.unsubscribe("pause_pressed", self._on_pause)
            return
        self.teardown()

    def teardown(self):
        """Fully destroy level and HUD (menu/exit path, never pause)."""
        self._preserve_for_pause = False
        if self.level:
            self.level.destroy()
            self.level = None
        if self.hud:
            self.hud.destroy()
            self.hud = None
        self.game.event_bus.unsubscribe("pause_pressed", self._on_pause)

    def update(self, dt):
        if self.level:
            self.level.update(dt)
        if self.hud:
            self.hud.update(dt)

    def _on_pause(self):
        self._preserve_for_pause = True
        self.game.state_machine.change_state("pause")
