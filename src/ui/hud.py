from direct.gui.OnscreenText import OnscreenText


class HUD:
    def __init__(self, game):
        self.game = game
        self.elements = []

        self.life_label = OnscreenText(
            text="HP: 100",
            pos=(-1.2, 0.9),
            scale=0.06,
            fg=(1, 0.2, 0.2, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.life_label)

        self.score_label = OnscreenText(
            text="SCORE: 0",
            pos=(0, 0.9),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.score_label)

        self.ammo_label = OnscreenText(
            text="AMMO: ∞",
            pos=(1.2, 0.9),
            scale=0.06,
            fg=(0.2, 0.8, 1, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.ammo_label)

    def show(self):
        for elem in self.elements:
            elem.show()

    def hide(self):
        for elem in self.elements:
            elem.hide()

    def update(self, dt):
        gameplay = self.game.state_machine.get_state("gameplay")
        if not gameplay or not gameplay.level:
            return

        player = gameplay.level.player
        if player:
            self.life_label.setText(f"HP: {int(player.life)}")

    def destroy(self):
        for elem in self.elements:
            elem.destroy()
        self.elements.clear()
