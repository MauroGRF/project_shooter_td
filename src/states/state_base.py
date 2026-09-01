class StateBase:
    def __init__(self, game):
        self.game = game

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def update(self, dt):
        pass

    def handle_input(self, action):
        pass
