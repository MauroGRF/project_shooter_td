from panda3d.core import WindowProperties

from src.core.settings import Settings


class Window:
    DEFAULT_CONFIG = {
        "title": "TD Shooter",
        "width": 1280,
        "height": 720,
        "fullscreen": False,
        "backgroundColor": [0.1, 0.1, 0.15, 1.0],
    }
    _KNOWN_KEYS = ("title", "width", "height", "fullscreen", "backgroundColor")

    def __init__(self, base, settings=None):
        self._base = base
        self._settings = settings if settings is not None else Settings.get_instance()
        self._config = self._load_config()
        self._apply()

    def _load_config(self):
        config = dict(self.DEFAULT_CONFIG)
        if hasattr(self._settings, "window"):
            data = self._settings.window
        else:
            data = self._settings.get("window", None)
        if data is None:
            print("[Window] WARNING: no 'window' section in settings; using defaults")
            return config
        if not isinstance(data, dict):
            print("[Window] WARNING: 'window' section is not an object; using defaults")
            return config
        data = dict(data)
        # Normalize legacy capitalized key.
        if "BackgroundColor" in data and "backgroundColor" not in data:
            data["backgroundColor"] = data.pop("BackgroundColor")
        for key in self._KNOWN_KEYS:
            if key in data:
                config[key] = data[key]
        return self._validate(config)

    def _validate(self, config):
        validated = dict(self.DEFAULT_CONFIG)
        if isinstance(config.get("title"), str) and config["title"]:
            validated["title"] = config["title"]
        else:
            print("[Window] WARNING: invalid window title; using default")
        for key in ("width", "height"):
            value = config.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                print(f"[Window] WARNING: invalid window {key} {value!r}; using default")
            else:
                validated[key] = value
        value = config.get("fullscreen")
        validated["fullscreen"] = bool(value) if isinstance(value, bool) else self.DEFAULT_CONFIG["fullscreen"]
        if not isinstance(value, bool):
            print(f"[Window] WARNING: invalid window fullscreen {value!r}; using default")
        bg = config.get("backgroundColor")
        if (
            isinstance(bg, (list, tuple))
            and len(bg) == 4
            and all(isinstance(c, (int, float)) for c in bg)
        ):
            validated["backgroundColor"] = [float(c) for c in bg]
        else:
            print(f"[Window] WARNING: invalid window backgroundColor {bg!r}; using default")
        return validated

    def _apply(self):
        self._base.windowTitle = self._config["title"]

        props = WindowProperties()
        props.setTitle(self._config["title"])
        props.setSize(self._config["width"], self._config["height"])
        props.setFullscreen(self._config["fullscreen"])
        # Best-effort window hints; not all backends expose these setters.
        try:
            props.setOrigin(100, 100)
        except AttributeError:
            pass
        try:
            props.setForeground(True)
        except AttributeError:
            pass
        self._base.win.requestProperties(props)

        bg = self._config["backgroundColor"]
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
