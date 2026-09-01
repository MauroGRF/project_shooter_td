import os
import json
from panda3d.core import WindowProperties


class Window:
    DEFAULT_CONFIG = {
        "title": "TD Shooter",
        "width": 1280,
        "height": 720,
        "fullscreen": False,
        "BackgroundColor": [0.1, 0.1, 0.15, 1.0],
    }

    def __init__(self, base):
        self._base = base
        self._config = self._load_config()
        self._apply()

    def _load_config(self):
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "settings.json",
        )
        config = dict(self.DEFAULT_CONFIG)
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "window" in data:
                    config.update(data["window"])
        return config

    def _apply(self):
        self._base.windowTitle = self._config["title"]

        props = WindowProperties()
        props.setTitle(self._config["title"])
        props.setSize(self._config["width"], self._config["height"])
        props.setFullscreen(self._config["fullscreen"])
        self._base.win.requestProperties(props)

        bg = self._config["BackgroundColor"]
        self._base.setBackgroundColor(bg[0], bg[1], bg[2], bg[3])

    @property
    def width(self):
        return self._config["width"]

    @property
    def height(self):
        return self._config["height"]

    @property
    def title(self):
        return self._config["title"]

    @property
    def fullscreen(self):
        return self._config["fullscreen"]
