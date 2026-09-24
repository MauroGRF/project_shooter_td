"""Custom event bus on top of Panda3D's Messenger.

The naive approach — call ``base.accept(event, callback)`` once per
subscriber — silently breaks when more than one subscriber wants the
same event. Panda3D's Messenger keys handlers by ``(event_name,
accepting_object)`` and *replaces* the previous handler when a new one
is registered under the same key. All our entities (Player, Enemy,
Collectables...) subscribe via the same ``ShowBase`` instance, so each
accept overwrites the last: only the final subscriber's callback ever
fires, which is why pickups, contact damage and exit detection
silently broke whenever more than one entity was in play.

Fix: one accept per event name (the first subscription installs a
single dispatcher); the dispatcher fans out to an internal list of
callbacks. Subsequent subscribes just append, unsubscribes shrink the
list, and the event is ignored only when the list goes empty again.

Public API stays the same (subscribe / unsubscribe / emit / clear).
"""

from direct.showbase.ShowBase import ShowBase

from src.core.warn_once import warn_once


class EventBus:
    _instance = None

    def __init__(self, base: ShowBase):
        self._base = base
        # event_name -> list[callback] (preserves subscribe order).
        self._handlers = {}
        # event_name -> dispatcher installed on the messenger (one per event).
        self._dispatchers = {}
        EventBus._instance = self

    @classmethod
    def get_instance(cls):
        return cls._instance

    def subscribe(self, event_name, callback):
        """Register callback for event_name. Multiple subscribers stack.

        Idempotent on the same callback (a duplicate subscribe does not
        add a second entry). Returns the callback as a token.
        """
        handlers = self._handlers.setdefault(event_name, [])
        if callback in handlers:
            return callback
        handlers.append(callback)
        if event_name not in self._dispatchers:
            self._install_dispatcher(event_name)
        return callback

    def _install_dispatcher(self, event_name):
        """Install a single messenger accept that fans out to all handlers.

        The dispatcher is captured by closure so messenger.send routes
        through us instead of going directly to a per-object callback
        (which would clobber siblings on the same accepting object).
        """
        handlers_list = self._handlers[event_name]

        def dispatcher(*args):
            # Iterate over a snapshot so handlers can safely unsubscribe
            # themselves during dispatch.
            for cb in list(handlers_list):
                try:
                    cb(*args)
                except Exception as exc:
                    warn_once(
                        f"eventbus.dispatch.{event_name}.{getattr(cb, '__qualname__', repr(cb))}",
                        f"[EventBus] handler {cb!r} for {event_name!r} raised: {exc!r}",
                    )

        self._dispatchers[event_name] = dispatcher
        self._base.accept(event_name, dispatcher)

    def unsubscribe(self, event_name, callback):
        """Remove a single callback. Ignores the event on the messenger
        once the handler list for it goes empty so we stop receiving it.
        """
        handlers = self._handlers.get(event_name)
        if not handlers:
            return
        if callback not in handlers:
            return
        handlers.remove(callback)
        if not handlers:
            self._handlers.pop(event_name, None)
            self._dispatchers.pop(event_name, None)
            self._base.ignore(event_name)

    def emit(self, event_name, *args):
        if args:
            self._base.messenger.send(event_name, list(args))
        else:
            self._base.messenger.send(event_name)

    def clear(self):
        for event_name in list(self._dispatchers.keys()):
            self._base.ignore(event_name)
        self._handlers.clear()
        self._dispatchers.clear()