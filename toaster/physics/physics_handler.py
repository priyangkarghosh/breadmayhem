from toaster.registry.registry_item import RegistryItem
from toaster.physics.physics_rect import PhysicsRect, STATIC
from toaster.physics.rect_tree import RectTree

COLLISION_LAYERS = ["DEFAULT", "PLAYER"]
COLLISION_MATRIX = [
    # d  p
    [1, 1],  # d
    [1, 1],  # p
]
TREE_FAT = (4, 4)


class PhysicsHandler(RegistryItem):
    def __init__(self):
        super().__init__("physics")

        self.iter_bodies = []
        self.all_rects = []
        self.rect_tree = RectTree(TREE_FAT)

    def update(self):
        for physics_rect in self.iter_bodies:
            physics_rect.step()

        self.rect_tree.update()

        #for i in range(20):
        #    for physics_rect in self.iter_bodies:
         #       physics_rect.process_collisions()

    def add_physics_rect(self, physics_rect):
        if not isinstance(physics_rect, PhysicsRect): return

        self.all_rects.append(physics_rect)
        if physics_rect.collision_mode != STATIC:
            # skip the check to make sure it is a rect_collider
            self.iter_bodies.append(physics_rect)
        self.rect_tree.insert_leaf(physics_rect)

    def get_collisions(self, physics_rect):
        if not isinstance(physics_rect, PhysicsRect): return None
        return self.rect_tree.get_overlaps(physics_rect)
