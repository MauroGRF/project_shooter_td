from src.states.state_base import StateBase


class StateMachine:
    def __init__(self, game):
        self.game = game
        self.states = {}
        self.current_state = None
        self.current_name = None
        self._register_default_states()

    def _register_default_states(self):
        from src.states.menu_state import MenuState
        from src.states.gameplay_state import GameplayState
        from src.states.pause_state import PauseState
        from src.states.loading_state import LoadingState

        self.register("menu", MenuState(self.game))
        self.register("gameplay", GameplayState(self.game))
        self.register("pause", PauseState(self.game))
        self.register("loading", LoadingState(self.game))

    def register(self, name, state):
        self.states[name] = state

    def change_state(self, name, **kwargs):
        if self.current_state:
            self.current_state.exit()

        self.current_name = name
        self.current_state = self.states.get(name)

        if self.current_state:
            self.current_state.enter(**kwargs)

        self.game.event_bus.emit("state_changed", name)

    def get_state(self, name):
        return self.states.get(name)
