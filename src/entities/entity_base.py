from panda3d.core import NodePath


class EntityBase:
    def __init__(self, game, entity_type="generic", model_name=None):
        self.game = game
        self.entity_type = entity_type
        self.life = 100
        self.max_life = 100
        self.alive = True
        self.speed = 0.0
        self.velocity = [0.0, 0.0, 0.0]
        self._contacts = set()
        self._contacts_enabled = True
        self._anims = {}
        self._anim_system = None
        self.child_nodes = {}
        self.joints = {}
        self._model_name = model_name

        if model_name:
            self.node = self.game.loader.loadModel(model_name)
        else:
            self.node = NodePath(entity_type)

        self.node.setTag("entity_type", entity_type)
        self.game.event_bus.subscribe("entity_enter", self._on_entity_enter)
        self.game.event_bus.subscribe("entity_exit", self._on_entity_exit)

    def set_position(self, x, y, z=0.0):
        self.node.setPos(x, y, z)

    def get_position(self):
        pos = self.node.getPos()
        return (pos.getX(), pos.getY(), pos.getZ())

    def take_damage(self, amount):
        if not self.alive:
            return
        self.life -= amount
        if self.life <= 0:
            self.life = 0
            self.die()

    def heal(self, amount):
        self.life = min(self.life + amount, self.max_life)

    def die(self):
        self.alive = False
        self.game.event_bus.emit("entity_died", self)

    def is_dead(self):
        return not self.alive

    def update(self, dt):
        pass

    def on_contact_enter(self, other):
        pass

    def on_contact_exit(self, other):
        pass

    def set_contacts_enabled(self, enabled):
        self._contacts_enabled = enabled
        if not enabled:
            self._contacts.clear()

    def contacts_enabled(self):
        return self._contacts_enabled

    def _on_entity_enter(self, e1, e2):
        if not self.alive or not self._contacts_enabled:
            return
        other = None
        if e1 is self:
            other = e2
        elif e2 is self:
            other = e1
        if other and other.alive:
            self._contacts.add(id(other))
            self.on_contact_enter(other)

    def _on_entity_exit(self, e1, e2):
        if not self._contacts_enabled:
            return
        other = None
        if e1 is self:
            other = e2
        elif e2 is self:
            other = e1
        if other:
            self._contacts.discard(id(other))
            self.on_contact_exit(other)

    def is_contacting(self, other):
        return id(other) in self._contacts

    def _get_anim_system(self):
        if self._anim_system is None:
            state = self.game.state_machine.get_state("gameplay")
            if state and state.level:
                self._anim_system = state.level.animation
        return self._anim_system

    def register_anim(self, name, frames, frame_rate=12.0, loop=False):
        anim_sys = self._get_anim_system()
        if anim_sys is None:
            return None
        anim_data = anim_sys.register(self, name, frames, frame_rate, loop)
        self._anims[name] = anim_data
        return anim_data

    def play_anim(self, name):
        anim_data = self._anims.get(name)
        if anim_data:
            anim_sys = self._get_anim_system()
            if anim_sys:
                anim_sys.play(anim_data)

    def play_anim_once(self, name):
        anim_data = self._anims.get(name)
        if anim_data:
            anim_sys = self._get_anim_system()
            if anim_sys:
                anim_sys.play_once(anim_data)

    def stop_anim(self, name):
        anim_data = self._anims.get(name)
        if anim_data:
            anim_sys = self._get_anim_system()
            if anim_sys:
                anim_sys.stop(anim_data)

    def stop_all_anims(self):
        anim_sys = self._get_anim_system()
        if anim_sys:
            for anim_data in self._anims.values():
                anim_sys.stop(anim_data)

    def add_child_node(self, name, model_path=None):
        child = self.node.attachNewNode(name)
        if model_path:
            model = self.game.loader.loadModel(model_path)
            model.reparentTo(child)
        self.child_nodes[name] = child
        return child

    def remove_child_node(self, name):
        if name in self.child_nodes:
            self.child_nodes[name].removeNode()
            del self.child_nodes[name]

    def expose_joint(self, joint_name):
        if not self.node.isEmpty() and hasattr(self.node, 'exposeJoint'):
            try:
                joint = self.node.exposeJoint(None, "modelRoot", joint_name)
                self.joints[joint_name] = joint
                return joint
            except Exception:
                return None
        return None

    def swap_model(self, model_path):
        if self.node and not self.node.isEmpty():
            self.node.removeNode()
        self.node = self.game.loader.loadModel(model_path)
        self.node.setTag("entity_type", self.entity_type)
        self._model_name = model_path
        for name, child in self.child_nodes.items():
            child.reparentTo(self.node)

    def destroy(self):
        self.game.event_bus.unsubscribe("entity_enter", self._on_entity_enter)
        self.game.event_bus.unsubscribe("entity_exit", self._on_entity_exit)
        for child in self.child_nodes.values():
            child.removeNode()
        self.child_nodes.clear()
        self.joints.clear()
        if self.node:
            self.node.removeNode()
            self.node = None
