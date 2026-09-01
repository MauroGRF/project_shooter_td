from panda3d.core import Vec3


class CameraSystem:
    def __init__(self, game):
        self.game = game
        self.target = None
        self.offset = Vec3(0, 0, 0)
        self._follow_enabled = False

        game.disableMouse()

    def setup(self, center_x, center_y, height=None, fov=None):
        if height is None:
            height = self.game.settings.get("camera.height", 15.0)
        if fov is None:
            fov = self.game.settings.get("camera.fov", 60)

        self.game.camera.setPos(center_x, center_y - height, height)
        self.game.camera.lookAt(center_x, center_y, 0)
        self.game.camLens.setFov(fov)

    def follow(self, entity, offset=None):
        self.target = entity
        if offset:
            self.offset = Vec3(*offset)
        self._follow_enabled = True

    def unfollow(self):
        self.target = None
        self._follow_enabled = False

    def update(self, dt):
        if not self._follow_enabled or not self.target:
            return

        pos = self.target.node.getPos()
        height = self.game.settings.get("camera.height", 15.0)

        self.game.camera.setPos(
            pos.getX() + self.offset.getX(),
            pos.getY() + self.offset.getY() - height,
            height,
        )
        self.game.camera.lookAt(pos.getX(), pos.getY(), 0)
