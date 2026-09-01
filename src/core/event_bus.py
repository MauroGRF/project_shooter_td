from direct.showbase.ShowBase import ShowBase


class EventBus:
    _instance = None

    def __init__(self, base: ShowBase):
        self._base = base
        self._handlers = {}

    @classmethod
    def get_instance(cls):
        return cls._instance

    def _set_instance(self, base: ShowBase):
        EventBus._instance = self

    def subscribe(self, event_name, callback):
        token = self._base.accept(event_name, callback)
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append((callback, token))
        return token

    def unsubscribe(self, event_name, callback):
        if event_name in self._handlers:
            self._handlers[event_name] = [
                (cb, tok) for cb, tok in self._handlers[event_name] if cb != callback
            ]
            self._base.ignore(event_name)

    def emit(self, event_name, *args):
        if args:
            self._base.messenger.send(event_name, list(args))
        else:
            self._base.messenger.send(event_name)

    def clear(self):
        for event_name, handlers in self._handlers.items():
            for _, token in handlers:
                self._base.ignore(event_name, token)
        self._handlers.clear()
