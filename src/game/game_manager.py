from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4
from src.core.settings import Settings
from src.core.event_bus import EventBus
from src.game.window import Window
from src.states.state_machine import StateMachine
from src.systems.input_manager import InputManager
from src.systems.audio_manager import AudioManager


class GameManager(ShowBase):
    _instance = None

    def __init__(self):
        ShowBase.__init__(self)
        GameManager._instance = self

        self.settings = Settings.get_instance()
        self.event_bus = EventBus(self)

        self.window_config = Window(self)

        self.input_manager = InputManager(self)
        self.audio_manager = AudioManager(self)

        self._setup_lights()

        self.state_machine = StateMachine(self)

        self.task_mgr.add(self._update, "game_update")

    def _setup_lights(self):
        """Ambient + key directional so boxes/cards shade instead of flat."""
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.55, 0.55, 0.55, 1.0))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        key = DirectionalLight("key")
        key.setColor(Vec4(0.85, 0.85, 0.85, 1.0))
        key_np = self.render.attachNewNode(key)
        key_np.setHpr(-45.0, -60.0, 0.0)
        self.render.setLight(key_np)

    @classmethod
    def get_instance(cls):
        return cls._instance

    def _update(self, task):
        dt = self.clock.getDt()
        self.input_manager.update(dt)
        if self.state_machine.current_state:
            self.state_machine.current_state.update(dt)
        return task.cont

    def run(self):
        self.state_machine.change_state("menu")
        ShowBase.run(self)
