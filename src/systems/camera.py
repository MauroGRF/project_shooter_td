"""Dual-mode camera: static wide view in player mode, orbit-stage on space.

Player mode (default): camera at the original wide view over the map
centre (height=15, looking at the centre). WASD moves the player; the
camera does not follow.

Camera mode (space held): the player is frozen. The camera orbits
AROUND THE STAGE: the mouse direction from the screen centre sets the
absolute target yaw (mouse east -> camera east of the stage looking
west, mouse north -> camera south looking north, etc.), and WASD moves
the look-at point in camera-relative coords (W = forward on screen).
When the player releases space the camera snaps back to the default
view.
"""

import math

from panda3d.core import Vec3


class CameraSystem:
    DEFAULT_PITCH = math.radians(45.0)
    PITCH_MIN = math.radians(25.0)
    PITCH_MAX = math.radians(62.0)

    def __init__(self, game):
        self.game = game
        self._height = 15.0
        # Look-at point: starts at the map centre, WASD moves it in
        # camera-relative coords (clamped to the map).
        self._lookat_x = 0.0
        self._lookat_y = 0.0
        # Absolute orbit yaw around the look-at point (radians).
        # yaw=0 -> camera south of the look-at, looking north.
        self._yaw = 0.0
        self._pitch = self.DEFAULT_PITCH
        # Map centre that setup() anchors on. Used by reset().
        self._base_lookat_x = 0.0
        self._base_lookat_y = 0.0
        # (min_x, min_y, max_x, max_y) world-space bounds.
        self._level_bounds = None
        game.disableMouse()

    def setup(self, center_x, center_y, height=None, fov=None):
        """Position the camera at the original wide view over the centre.
        """
        if height is None:
            height = self.game.settings.get("camera.height", 15.0)
        if fov is None:
            fov = self.game.settings.get("camera.fov", 60)
        self._height = height
        self._base_lookat_x = center_x
        self._base_lookat_y = center_y
        self.reset()
        self.game.camLens.setFov(fov)

    def set_level_bounds(self, width, height, tile_size=1.0):
        # Keep the look-at point on the map so the user can never lose
        # the level from view. The camera position itself is derived
        # from the look-at + orbit offset, so it stays at a considerable
        # but bounded distance automatically.
        self._level_bounds = (
            -tile_size * 0.5,
            -tile_size * 0.5,
            width * tile_size + tile_size * 0.5,
            height * tile_size + tile_size * 0.5,
        )

    # follow is intentionally a no-op. Kept so the call from
    # Level._setup_camera does not crash if it is ever reintroduced.
    def follow(self, entity, offset=None):
        return

    def reset(self):
        """Snap the camera back to the default wide view."""
        self._lookat_x = self._base_lookat_x
        self._lookat_y = self._base_lookat_y
        self._yaw = 0.0
        self._pitch = self.DEFAULT_PITCH
        self.update(0)

    def pan(self, dx, dy, dt):
        """Slide the look-at point in CAMERA-RELATIVE coords.

        ``dx`` = strafe intent (D=+1 east on screen), ``dy`` = forward
        intent (W=+1 up on screen). Both are velocities in units/sec.
        The move does not depend on the fixed world axes: W always
        moves towards where the view is pointing. Clamped to the map.
        """
        if dt <= 0:
            return
        sin_y = math.sin(self._yaw)
        cos_y = math.cos(self._yaw)
        # View direction (look-at minus camera) projected on XY is
        # (-sin(yaw), cos(yaw)): at yaw=0 the camera is south looking
        # north, so W pushes the view north. Right on screen is that
        # vector rotated -90 deg: (cos(yaw), sin(yaw)).
        fwd_x = -sin_y
        fwd_y = cos_y
        right_x = cos_y
        right_y = sin_y
        self._lookat_x += (fwd_x * dy + right_x * dx) * dt
        self._lookat_y += (fwd_y * dy + right_y * dx) * dt
        self._clamp_lookat_point()

    def rotate(self, dyaw, dpitch, dt):
        """Back-compat incremental rotate. Kept so older callers do not
        crash; new code should use orbit_towards()."""
        if dt <= 0:
            return
        self._yaw += dyaw * dt
        self._pitch = max(
            self.PITCH_MIN,
            min(self.PITCH_MAX, self._pitch + dpitch * dt),
        )

    def orbit_towards(self, sx, sy, lerp_rate, dt):
        """Absolute orbit around the look-at point.

        The mouse vector (sx, sy) from the screen centre sets the
        TARGET yaw: mouse east -> camera east of the stage looking
        west, mouse north -> camera south looking north (default), etc.
        ``target = atan2(sx, sy)``. The current yaw eases towards the
        target on the shortest arc, so the result does not depend on
        where the camera currently is — only on where the mouse points.
        Pitch stays fixed: this is a translation around the stage.
        """
        if dt <= 0 or lerp_rate <= 0:
            return
        target = math.atan2(sx, sy)
        diff = (target - self._yaw + math.pi) % (2.0 * math.pi) - math.pi
        step = max(-1.0, min(1.0, lerp_rate * dt))
        self._yaw += diff * step

    def _clamp_lookat_point(self):
        if self._level_bounds is None:
            return
        min_x, min_y, max_x, max_y = self._level_bounds
        self._lookat_x = max(min_x, min(self._lookat_x, max_x))
        self._lookat_y = max(min_y, min(self._lookat_y, max_y))

    def update(self, dt):
        """Position the camera on its orbit around the look-at point.

        Runs unconditionally. Camera position = look-at + orbit offset;
        the view always points at the look-at, so the stage stays
        centred while the camera translates around it.
        """
        self._clamp_lookat_point()
        cos_p = math.cos(self._pitch)
        sin_p = math.sin(self._pitch)
        cos_y = math.cos(self._yaw)
        sin_y = math.sin(self._yaw)
        dist = self._height * math.sqrt(2)
        cam_x = self._lookat_x + dist * cos_p * sin_y
        cam_y = self._lookat_y - dist * cos_p * cos_y
        cam_z = dist * sin_p
        self.game.camera.setPos(cam_x, cam_y, cam_z)
        self.game.camera.lookAt(self._lookat_x, self._lookat_y, 0.0)