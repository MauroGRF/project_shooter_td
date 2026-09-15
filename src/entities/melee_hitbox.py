from panda3d.core import (
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
    TransparencyAttrib,
    Vec4,
)
from src.entities.entity_base import EntityBase


class MeleeHitbox(EntityBase):
    NEUTRAL_COLOR = Vec4(1.0, 0.25, 0.25, 0.55)
    HIT_COLOR = Vec4(0.2, 1.0, 0.2, 0.9)

    def __init__(self, game, owner, position, damage, radius=0.65, lifetime=0.25):
        EntityBase.__init__(self, game, "melee_hitbox")

        self.owner = owner
        self.damage = damage
        self.radius = radius
        self.lifetime = lifetime
        self.age = 0.0
        self.hit = False
        self.active = True
        self.fade_time = 0.15
        self._base_color = self.NEUTRAL_COLOR

        # cube rests on the floor (z = half of its size)
        self.node.setPos(position[0], position[1], radius)

        cube = self._build_cube(radius * 2.0)
        cube.reparentTo(self.node)
        cube.setColor(self._base_color)
        cube.setTransparency(TransparencyAttrib.MAlpha)
        cube.setTwoSided(True)
        self.cube = cube

    def mark_hit(self):
        """Flag this hitbox as connected; it turns green to show the hit."""
        if self.hit:
            return
        self.hit = True
        self._base_color = self.HIT_COLOR
        if self.cube:
            self.cube.setColor(self._base_color)

    def _apply_alpha(self):
        if not self.cube:
            return
        remaining = self.lifetime - self.age
        if remaining < self.fade_time:
            factor = max(0.0, remaining / self.fade_time)
        else:
            factor = 1.0
        alpha = self._base_color[3] * factor
        self.cube.setColor(
            self._base_color[0],
            self._base_color[1],
            self._base_color[2],
            alpha,
        )

    @staticmethod
    def _build_cube(size):
        half = size * 0.5
        vertex_format = GeomVertexFormat.getV3()
        vdata = GeomVertexData("melee_cube", vertex_format, Geom.UHStatic)
        pos = GeomVertexWriter(vdata, "vertex")

        corners = [
            (-half, -half, -half), (half, -half, -half),
            (half, half, -half), (-half, half, -half),
            (-half, -half, half), (half, -half, half),
            (half, half, half), (-half, half, half),
        ]
        for c in corners:
            pos.addData3(c[0], c[1], c[2])

        # outward-facing triangles (two-sided anyway, so winding is cosmetic)
        faces = [
            (0, 3, 7), (0, 7, 4),  # -X
            (1, 5, 6), (1, 6, 2),  # +X
            (0, 4, 5), (0, 5, 1),  # -Y
            (3, 2, 6), (3, 6, 7),  # +Y
            (0, 1, 2), (0, 2, 3),  # -Z
            (4, 7, 6), (4, 6, 5),  # +Z
        ]
        tris = GeomTriangles(Geom.UHStatic)
        for a, b, c in faces:
            tris.addVertex(a)
            tris.addVertex(b)
            tris.addVertex(c)
            tris.closePrimitive()

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode("melee_cube_mesh")
        node.addGeom(geom)
        return NodePath(node)

    def update(self, dt):
        self.age += dt
        self._apply_alpha()
        if self.age >= self.lifetime:
            self.alive = False

    def destroy(self):
        EntityBase.destroy(self)