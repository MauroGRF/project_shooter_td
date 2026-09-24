"""Central model loading helper with .glb/.gltf support and safe fallback.

Uses panda3d-gltf when available (registers .glb/.gltf with the loader).
Never raises: on failure returns a placeholder NodePath plus an error string.
"""

from panda3d.core import NodePath

from src.core.warn_once import warn_once

_GLTf_READY = None


def ensure_gltf_loader():
    """Import panda3d_gltf once so .glb/.gltf load via loader.loadModel.

    Returns True if glTF loading is available, False otherwise.
    Tolerates the package being absent (egg/bam models still work).

    Supports both module names: legacy ``panda3d_gltf`` (<=1.2.x, needs
    the ``patch`` import to register the loader) and new ``gltf`` (>=1.3.0,
    registered via the ``panda3d.loaders`` entry point, no import needed).
    """
    global _GLTf_READY
    if _GLTf_READY is not None:
        return _GLTf_READY
    try:
        import panda3d_gltf  # noqa: F401
        import panda3d_gltf.patch  # noqa: F401
    except ImportError:
        pass
    except Exception as exc:
        warn_once(
            "gltf.patch",
            f"[model_loader] panda3d_gltf patch import failed: {exc!r}",
        )
    # Probe again: absence of the package is fine, loader still handles egg/bam.
    try:
        import importlib.util

        _GLTf_READY = (
            importlib.util.find_spec("panda3d_gltf") is not None
            or importlib.util.find_spec("gltf") is not None
        )
    except Exception as exc:
        warn_once(
            "gltf.probe",
            f"[model_loader] glTF loader probe failed: {exc!r}",
        )
        _GLTf_READY = False
    return _GLTf_READY


# entity_type -> (domain, model_key, scale_key, rotation_key, offset_key).
# A None key means that slot has no config default (class attr or None only).
_VISUAL_CONFIG_KEYS = {
    "player": ("player", "player_model", None, None, None),
    "enemy": (
        "enemies",
        "enemy_model",
        "enemy_model_scale",
        "enemy_model_rotation",
        "enemy_model_offset",
    ),
    "dog": (
        "enemies",
        "dog_model",
        "dog_model_scale",
        "dog_model_rotation",
        "dog_model_offset",
    ),
    "tile": ("game", "tile_model", None, None, None),
    "wall": ("game", "tile_model", None, None, None),
    "barrier": ("game", "tile_model", None, None, None),
    "floor": ("game", "tile_model", None, None, None),
    "door": ("game", "tile_model", None, None, None),
    "chest": ("game", "tile_model", None, None, None),
    "projectile": ("game", "projectile_model", None, None, None),
}

# entity_type values already logged (avoid spamming one line per tile).
_LOGGED_VISUALS = set()


def resolve_visual(entity_type, cls, game=None):
    """Single source of truth for entity visuals.

    Rule: if the class declares MODEL, the class wins wholesale
    (MODEL/MODEL_SCALE/MODEL_ROTATION/MODEL_OFFSET). If it declares
    nothing (MODEL is None), the config default for the entity type is
    used. The same value never lives in two places.

    Returns (model, scale, rotation, offset, source) where source is
    "CLASS" or "CONFIG default". Scale/rotation/offset may be None
    (no transform). A missing model raises ValueError: fail fast with
    a clear message instead of a silent placeholder.
    """
    model = getattr(cls, "MODEL", None)
    if model is not None:
        result = (
            model,
            getattr(cls, "MODEL_SCALE", None),
            getattr(cls, "MODEL_ROTATION", None),
            getattr(cls, "MODEL_OFFSET", None),
            "CLASS",
        )
    else:
        domain, model_key, scale_key, rotation_key, offset_key = (
            _VISUAL_CONFIG_KEYS.get(entity_type, (None, None, None, None, None))
        )
        settings = getattr(game, "settings", None) if game is not None else None
        getter = getattr(settings, "get", None) if settings is not None else None

        def _cfg(key):
            if getter is None or key is None or domain is None:
                return None
            try:
                return getter("%s.%s" % (domain, key), None)
            except Exception as exc:
                warn_once(
                    f"visual.cfg.{domain}.{key}",
                    f"[visual] config lookup {domain}.{key} failed: {exc!r}",
                )
                return None

        if domain is None:
            resolved = (None, None, None, None)
        else:
            resolved = (_cfg(model_key), _cfg(scale_key), _cfg(rotation_key), _cfg(offset_key))
        if resolved[0] is None:
            want = "%s.%s" % (domain, model_key) if domain else "<no config domain>"
            raise ValueError(
                "[visual] no model for entity_type=%r: class %s declares no MODEL "
                "and config %r is missing. Declare %s.MODEL or add the config default."
                % (entity_type, getattr(cls, "__name__", cls), want, getattr(cls, "__name__", cls))
            )
        result = (resolved[0], resolved[1], resolved[2], resolved[3], "CONFIG default")

    if entity_type not in _LOGGED_VISUALS:
        _LOGGED_VISUALS.add(entity_type)
        print("[visual] %s -> %r from %s" % (entity_type, result[0], result[4]))
    return result


def load_entity_model(game, model_path):
    """Load a model via game.loader.loadModel with error handling.

    Supports .glb/.gltf/.egg/.bam by extension (passthrough to the loader;
    extensionless Panda3D builtin paths like "models/smiley" also work).

    Returns (node, is_actor, error) where node is always a valid NodePath
    (placeholder on failure so callers never crash), is_actor is always
    False here (Actor creation lives in EntityBase for animatable models),
    and error is None on success or a message string on failure.
    """
    ensure_gltf_loader()
    if not model_path:
        return NodePath("empty_model"), False, "empty model_path"
    try:
        node = game.loader.loadModel(model_path)
    except Exception as exc:
        return NodePath("missing_model"), False, str(exc)
    if node is None or (hasattr(node, "isEmpty") and node.isEmpty()):
        return NodePath("missing_model"), False, "loadModel returned empty for %r" % (model_path,)
    return node, False, None
