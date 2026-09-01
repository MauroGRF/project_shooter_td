from panda3d.core import Vec3, Vec4


class AnimationSystem:
    def __init__(self, game):
        self.game = game
        self._animations = []

    def register(self, entity, animation_name, frames, frame_rate=12.0, loop=False):
        anim_data = {
            "entity": entity,
            "name": animation_name,
            "frames": frames,
            "frame_rate": frame_rate,
            "loop": loop,
            "current_frame": 0,
            "timer": 0.0,
            "playing": False,
            "finished": False,
        }
        self._animations.append(anim_data)
        return anim_data

    def play(self, anim_data):
        anim_data["playing"] = True
        anim_data["current_frame"] = 0
        anim_data["timer"] = 0.0
        anim_data["finished"] = False

    def play_once(self, anim_data):
        anim_data["loop"] = False
        self.play(anim_data)

    def stop(self, anim_data):
        anim_data["playing"] = False

    def update(self, dt):
        for anim in self._animations:
            if not anim["playing"]:
                continue

            anim["timer"] += dt
            frame_duration = 1.0 / anim["frame_rate"]

            if anim["timer"] >= frame_duration:
                anim["timer"] -= frame_duration
                anim["current_frame"] += 1

                if anim["current_frame"] >= len(anim["frames"]):
                    if anim["loop"]:
                        anim["current_frame"] = 0
                    else:
                        anim["current_frame"] = len(anim["frames"]) - 1
                        anim["playing"] = False
                        anim["finished"] = True

                self._apply_frame(anim)

    def _get_target_node(self, entity, target=None):
        if target is None:
            return entity.node
        if target == "root":
            return entity.node
        if hasattr(entity, "child_nodes") and target in entity.child_nodes:
            return entity.child_nodes[target]
        return entity.node

    def _apply_frame(self, anim):
        entity = anim["entity"]
        frame = anim["frames"][anim["current_frame"]]

        if not isinstance(frame, dict):
            return

        target = frame.get("target", None)
        node = self._get_target_node(entity, target)

        if "hpr" in frame:
            h, p, r = frame["hpr"]
            node.setH(h)
            node.setP(p)
            node.setR(r)

        if "h" in frame:
            node.setH(frame["h"])
        if "p" in frame:
            node.setP(frame["p"])
        if "r" in frame:
            node.setR(frame["r"])

        if "scale" in frame:
            s = frame["scale"]
            if isinstance(s, (list, tuple)):
                node.setScale(s[0], s[1], s[2])
            else:
                node.setScale(s)

        if "color" in frame:
            c = frame["color"]
            node.setColorScale(c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)

        if "pos" in frame:
            p = frame["pos"]
            node.setPos(p[0], p[1], p[2])

        if "pos_offset" in frame:
            off = frame["pos_offset"]
            cur = node.getPos()
            node.setPos(cur.getX() + off[0], cur.getY() + off[1], cur.getZ() + off[2])

        if "joint" in frame:
            joint_name = frame["joint"]
            joint_hpr = frame.get("joint_hpr", None)
            joint_pos = frame.get("joint_pos", None)
            if hasattr(entity, "joints") and joint_name in entity.joints:
                joint_node = entity.joints[joint_name]
                if joint_hpr:
                    joint_node.setH(joint_hpr[0])
                    joint_node.setP(joint_hpr[1])
                    joint_node.setR(joint_hpr[2])
                if joint_pos:
                    joint_node.setPos(joint_pos[0], joint_pos[1], joint_pos[2])

        if "model" in frame:
            model_path = frame["model"]
            if hasattr(entity, "swap_model"):
                entity.swap_model(model_path)

    def clear(self):
        self._animations.clear()

    def remove(self, anim_data):
        if anim_data in self._animations:
            self._animations.remove(anim_data)
