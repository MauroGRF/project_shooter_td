from direct.showbase.ShowBase import ShowBase


class EventBus:
    _instance = None

    def __init__(self, base: ShowBase):
        self._base = base
        self._handlers = {}
        EventBus._instance = self

    @classmethod
    def get_instance(cls):
        return cls._instance

    def subscribe(self, event_name, callback):
        token = self._base.accept(event_name, callback)
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append((callback, token))
        return token

    def unsubscribe(self, event_name, callback):
        handlers = self._handlers.get(event_name)
        if not handlers:
            return
        remaining = [(cb, tok) for cb, tok in handlers if cb != callback]
        if len(remaining) == len(handlers):
            return
        # DirectObject.ignore(event) removes EVERY handler the game object
        # registered for the event, so drop all and re-register survivors.
        self._base.ignore(event_name)
        if remaining:
            self._handlers[event_name] = [
                (cb, self._base.accept(event_name, cb)) for cb, _ in remaining
            ]
        else:
            self._handlers.pop(event_name, None)

    def emit(self, event_name, *args):
        if args:
            self._base.messenger.send(event_name, list(args))
        else:
            self._base.messenger.send(event_name)

    def clear(self):
        for event_name in list(self._handlers.keys()):
            self._base.ignore(event_name)
        self._handlers.clear()
