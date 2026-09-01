from direct.gui.DirectGui import DirectFrame, DirectButton
from direct.gui.OnscreenText import OnscreenText


class MenuUI:
    def __init__(self, game):
        self.game = game
        self.elements = []

    def build_main_menu(self):
        self.clear()

        frame = DirectFrame(frameColor=(0, 0, 0, 0.6), frameSize=(-0.6, 0.6, -0.5, 0.5))
        self.elements.append(frame)

        title = OnscreenText(
            text="TD SHOOTER",
            parent=frame,
            pos=(0, 0.3),
            scale=0.15,
            fg=(1, 1, 1, 1),
            align=0,
        )
        self.elements.append(title)

        start_btn = DirectButton(
            text="START",
            command=self._on_start,
            pos=(0, 0, 0),
            scale=0.1,
            frameColor=(0.3, 0.6, 0.3, 1),
            text_fg=(1, 1, 1, 1),
        )
        self.elements.append(start_btn)

        quit_btn = DirectButton(
            text="QUIT",
            command=self._on_quit,
            pos=(0, 0, -0.15),
            scale=0.1,
            frameColor=(0.6, 0.3, 0.3, 1),
            text_fg=(1, 1, 1, 1),
        )
        self.elements.append(quit_btn)

    def build_pause_menu(self):
        self.clear()

        frame = DirectFrame(frameColor=(0, 0, 0, 0.7), frameSize=(-0.5, 0.5, -0.4, 0.4))
        self.elements.append(frame)

        title = OnscreenText(
            text="PAUSED",
            parent=frame,
            pos=(0, 0.25),
            scale=0.12,
            fg=(1, 1, 1, 1),
            align=0,
        )
        self.elements.append(title)

        resume_btn = DirectButton(
            text="RESUME",
            command=self._on_resume,
            pos=(0, 0, 0.05),
            scale=0.08,
            frameColor=(0.3, 0.6, 0.3, 1),
            text_fg=(1, 1, 1, 1),
        )
        self.elements.append(resume_btn)

        menu_btn = DirectButton(
            text="MAIN MENU",
            command=self._on_menu,
            pos=(0, 0, -0.1),
            scale=0.08,
            frameColor=(0.6, 0.4, 0.2, 1),
            text_fg=(1, 1, 1, 1),
        )
        self.elements.append(menu_btn)

    def _on_start(self):
        self.game.event_bus.emit("enter_pressed")

    def _on_resume(self):
        self.game.event_bus.emit("pause_pressed")

    def _on_menu(self):
        self.game.event_bus.emit("escape_pressed")

    def _on_quit(self):
        self.game.userExit()

    def clear(self):
        for elem in self.elements:
            elem.destroy()
        self.elements.clear()
