import json
import os


class Settings:
    """Singleton holding game configuration split by domain.

    Each domain lives in its own file under config/ (window.json,
    player.json, weapons.json, enemies.json, camera.json, audio.json,
    game.json). Every file wraps its keys under a single top-level
    section matching the domain name.

    Domain access: settings.window, settings.player, settings.weapons,
    settings.enemies, settings.camera, settings.audio, settings.game.

    Backward compatibility: get("game.<key>", default) keeps resolving
    the legacy flat game namespace (player/enemy/weapon keys are mirrored
    into the "game" section), so existing call sites are untouched.
    """

    _instance = None

    # section -> (filename, required keys). Missing file, section or key
    # fails fast with a clear message at boot.
    _DOMAINS = {
        "window": (
            "window.json",
            ("title", "width", "height", "fullscreen", "backgroundColor"),
        ),
        "player": (
            "player.json",
            (
                "player_speed",
                "player_life",
                "player_stamina",
                "min_sprint_stamina",
                "stamina_recovery",
                "stamina_depletion",
                "sprint_multiplier",
                "move_response",
                "move_decel",
                "sprint_response",
                "dash_cooldown",
                "dash_duration",
                "dash_speed",
                "dash_stamina_cost",
                "max_parries",
                "parry_duration",
                "melee_cooldown",
                "dodge_range_extra",
                "player_effects",
                "player_model",
            ),
        ),
        "weapons": ("weapons.json", ("0", "1", "2", "3")),
        "enemies": (
            "enemies.json",
            (
                "enemy_speed",
                "enemy_life",
                "enemy_contact_damage",
                "enemy_contact_interval",
                "enemy_model",
                "enemy_model_scale",
                "enemy_model_rotation",
                "enemy_model_offset",
                "dog_speed",
                "dog_life",
                "dog_damage",
                "dog_attack_cooldown",
                "dog_attack_range",
                "dog_aggro_range",
            ),
        ),
        "camera": ("camera.json", ("height", "angle", "near", "far", "fov")),
        "audio": ("audio.json", ("music_volume", "sfx_volume")),
        "game": (
            "game.json",
            ("tile_size", "gravity", "projectile_speed", "projectile_damage", "marker_height"),
        ),
    }

    # Legacy "game.<key>" mirror: rebuilt from the canonical domains so
    # old dotted keys keep working. Order matters (later wins on clash).
    _GAME_MIRROR_SECTIONS = ("game", "player", "enemies")

    def __init__(self):
        self._data = {}
        self._config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
        )
        self.load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _load_domain_file(self, section, filename):
        path = os.path.join(self._config_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"[Settings] missing required config file: {path} "
                f"(section '{section}')"
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"[Settings] invalid JSON in {path}: {exc}") from exc
        if not isinstance(content, dict) or section not in content:
            raise ValueError(
                f"[Settings] {path} must contain a top-level '{section}' object"
            )
        data = content[section]
        if not isinstance(data, dict):
            raise ValueError(
                f"[Settings] section '{section}' in {path} must be a JSON object"
            )
        return data

    def load(self):
        data = {}
        for section, (filename, required_keys) in self._DOMAINS.items():
            section_data = self._load_domain_file(section, filename)
            missing = [key for key in required_keys if key not in section_data]
            if missing:
                raise ValueError(
                    f"[Settings] {filename} (section '{section}') "
                    f"is missing required keys: {', '.join(missing)}"
                )
            data[section] = section_data
        self._data = data
        self._rebuild_game_mirror()

    def _rebuild_game_mirror(self):
        merged = {}
        for section in self._GAME_MIRROR_SECTIONS:
            merged.update(self._data.get(section, {}))
        merged["weapons"] = self._data.get("weapons", {})
        self._data["game"] = merged

    def _resolve_section(self, section):
        if section == "game":
            self._rebuild_game_mirror()
        return self._data.get(section)

    def save(self):
        os.makedirs(self._config_dir, exist_ok=True)
        # Keys mirrored into "game" from other domains must not leak back
        # into game.json; they are saved with their owning domain.
        mirrored = set(self._DOMAINS["player"][1]) | set(self._DOMAINS["enemies"][1]) | {"weapons"}
        for section, (filename, _required_keys) in self._DOMAINS.items():
            path = os.path.join(self._config_dir, filename)
            section_data = self._data.get(section, {})
            if section == "game":
                section_data = {k: v for k, v in section_data.items() if k not in mirrored}
            with open(path, "w", encoding="utf-8") as f:
                json.dump({section: section_data}, f, indent=4)
        self._rebuild_game_mirror()

    def _owner_section(self, key):
        """Map a legacy 'game.<key>' to its canonical domain section."""
        parts = key.split(".")
        if len(parts) == 2 and parts[0] == "game":
            leaf = parts[1]
            for section in ("player", "enemies"):
                if leaf in self._data.get(section, {}):
                    return section, leaf
            if leaf == "weapons":
                return "weapons", None
            return "game", leaf
        return None, None

    def get(self, key, default=None):
        keys = key.split(".")
        section = keys[0]
        value = self._resolve_section(section) if len(keys) > 1 else self._data
        if value is None:
            return default
        for k in keys[1:] if len(keys) > 1 else keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        section, leaf = self._owner_section(key)
        if section is not None:
            if leaf is None:
                self._data[section] = value
            else:
                self._data.setdefault(section, {})[leaf] = value
            self._rebuild_game_mirror()
            return
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
        self._rebuild_game_mirror()

    @property
    def window(self):
        return self._data["window"]

    @property
    def player(self):
        return self._data["player"]

    @property
    def weapons(self):
        return self._data["weapons"]

    @property
    def enemies(self):
        return self._data["enemies"]

    @property
    def camera(self):
        return self._data["camera"]

    @property
    def audio(self):
        return self._data["audio"]

    @property
    def game(self):
        self._rebuild_game_mirror()
        return self._data["game"]

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)
