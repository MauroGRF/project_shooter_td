"""Warn-once helper: surface swallowed exceptions without per-frame spam."""

_logged = set()


def warn_once(key, message):
    """Print ``message`` at most once per ``key`` for the process lifetime."""
    if key in _logged:
        return
    _logged.add(key)
    print(f"[warn] {message}", flush=True)
