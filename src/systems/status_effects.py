class StatusEffect:
    def __init__(self, name, duration, modifiers=None):
        self.name = name
        self.duration = duration
        self.remaining = duration
        self.modifiers = modifiers or {}

    def update(self, dt):
        self.remaining -= dt
        return self.remaining > 0


class StatusEffectSystem:
    """Holds the active status effects for the player and exposes aggregate
    modifier multipliers (applied to movement, damage, etc.)."""

    def __init__(self, game):
        self.game = game
        self.effects = []

    def add_effect(self, effect):
        # re-applying the same effect refreshes its duration instead of stacking
        for existing in self.effects:
            if existing.name == effect.name:
                existing.remaining = effect.duration
                existing.modifiers = effect.modifiers
                return
        self.effects.append(effect)

    def remove_effect(self, name):
        for effect in self.effects[:]:
            if effect.name == name:
                self.effects.remove(effect)

    def update(self, dt):
        for effect in self.effects[:]:
            if not effect.update(dt):
                self.effects.remove(effect)

    def get_modifier(self, key, default=1.0):
        total = default
        for effect in self.effects:
            total *= effect.modifiers.get(key, 1.0)
        return total

    def has_effect(self, name):
        return any(e.name == name for e in self.effects)

    def clear(self):
        self.effects.clear()