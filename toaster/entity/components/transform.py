from toaster.entity.component import Component


class Transform(Component):
    def __init__(self, position=(0, 0), scale=(1, 1), rotation=0):
        super().__init__("transform")

        self.position = list(position).copy()
        self.scale = list(scale).copy()
        self.rotation = rotation
