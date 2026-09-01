from direct.gui.OnscreenText import OnscreenText
from src.states.state_base import StateBase


class PauseState(StateBase):
    def enter(self, **kwargs):
        self.pause_text = OnscreenText(
            text="PAUSED",
            pos=(0, 0.3),
            scale=0.15,
            fg=(1, 1, 1, 1),
            align=0,
        )
        self.resume_text = OnscreenText(
            text="Press P to Resume",
            pos=(0, 0),
            scale=0.07,
            fg=(0.8, 0.8, 0.2, 1),
            align=0,
        )
        self.menu_text = OnscreenText(
            text="Press ESC to return to Menu",
            pos=(0, -0.2),
            scale=0.06,
            fg=(0.6, 0.6, 0.6, 1),
            align=0,
        )
        self.game.event_bus.subscribe("pause_pressed", self._on_resume)
        self.game.event_bus.subscribe("escape_pressed", self._on_menu)

    def exit(self):
        self.pause_text.destroy()
        self.resume_text.destroy()
        self.menu_text.destroy()
        self.game.event_bus.unsubscribe("pause_pressed", self._on_resume)
        self.game.event_bus.unsubscribe("escape_pressed", self._on_menu)

    def _on_resume(self, *args):
        self.game.state_machine.change_state("gameplay")

    def _on_menu(self, *args):
        self.game.state_machine.change_state("menu")
