from toaster.entity.component import Component


class Transform(Component):
    def __init__(
        self, 
        position: tuple[float, float] | list[float] = (0, 0), 
        scale: tuple[float, float] | list[float] = (1, 1), 
        rotation: float = 0
    ) -> None:
        super().__init__("transform")
        self.position: list[float] = list(position).copy()
        self.scale: list[float] = list(scale).copy()
        self.rotation: float = rotation
