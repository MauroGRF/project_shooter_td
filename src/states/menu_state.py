from panda3d.core import TextNode, CardMaker, NodePath, Vec4
from src.states.state_base import StateBase


class MenuState(StateBase):
    def enter(self, **kwargs):
        self._elements = []

        bg = CardMaker("menu_bg")
        bg.setFrame(-2, 2, -1.2, 1.2)
        bg_node = self.game.aspect2d.attachNewNode(bg.generate())
        bg_node.setColor(Vec4(0.05, 0.05, 0.1, 1.0))
        bg_node.setZ(-0.1)
        self._elements.append(bg_node)

        self.title = self._make_text("TD SHOOTER", 0, 0.6, 0.18, Vec4(1, 1, 1, 1))
        self.start_text = self._make_text("Presiona ENTER para Jugar", 0, 0.1, 0.08, Vec4(1, 1, 0.3, 1))
        self.controls_text = self._make_text(
            "WASD: Mover | Flechas: Apuntar | P: Pausa",
            0, -0.3, 0.05, Vec4(0.7, 0.7, 0.7, 1),
        )

        self.game.event_bus.subscribe("enter_pressed", self._on_start)
        self.game.event_bus.subscribe("escape_pressed", self._on_exit)

    def _make_text(self, text, x, y, scale, color):
        tn = TextNode("menu_text")
        tn.setText(text)
        tn.setAlign(TextNode.ACenter)
        tn.setTextColor(color)
        tn.setShadow(0.04, 0.04)
        tn.setShadowColor(Vec4(0, 0, 0, 1))
        node_path = self.game.aspect2d.attachNewNode(tn.generate())
        node_path.setScale(scale)
        node_path.setPos(x, 0, y)
        self._elements.append(node_path)
        return node_path

    def exit(self):
        for elem in self._elements:
            elem.removeNode()
        self._elements.clear()
        self.game.event_bus.unsubscribe("enter_pressed", self._on_start)
        self.game.event_bus.unsubscribe("escape_pressed", self._on_exit)

    def _on_start(self, *args):
        self.game.state_machine.change_state("loading", level_file="level_01.lvl")

    def _on_exit(self, *args):
        self.game.userExit()
