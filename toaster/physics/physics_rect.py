STATIC = 0
KINEMATIC = 1
DYNAMIC = 2


class PhysicsRect:
    _id = 0

    def __init__(self, collision_mode=0, collision_layer=0, phys_rect=None):
        self.collision_mode = collision_mode
        self.collision_layer = collision_layer
        self.phys_rect = phys_rect

        self.rect_id = PhysicsRect._id
        PhysicsRect._id += 1

    @property
    def static(self):
        return self.collision_mode == STATIC

    @property
    def kinematic(self):
        return self.collision_mode == KINEMATIC

    @property
    def dynamic(self):
        return self.collision_mode == DYNAMIC

    @property
    def rect(self): return self.phys_rect

    def __hash__(self):
        return self.rect_id

    def __eq__(self, other):
        return self.rect_id == other.rect_id
