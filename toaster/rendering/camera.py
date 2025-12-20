from toaster.entity.entity import Entity
from toaster.registry.registry_item import RegistryItem


class Camera(RegistryItem):
    # layer spacing should be relative to camera, therefore it should always be increasing (0 will be rendered first)
    def __init__(
        self, 
        central_layer: int, 
        camera_distances: list[int], 
        position: tuple[int, int] = (0, 0), 
        offset: tuple[int, int] = (0, 0), 
        origin: tuple[int, int] = (0, 0),
        smoothing: int =1
    ):
        super().__init__("camera")

        # origin and how smoothly the camera should interpolate to targets position
        self.origin = origin
        self.smoothing = smoothing

        # target possibilities
        self.target_offset = offset
        self.target_transform = None
        self.target_position = None

        # calculate the layer offset multipliers
        # **assume central layer index is always valid and distances are formatted correctly
        self.central_layer = central_layer
        central_layer_distance = camera_distances[self.central_layer]
        self.layer_multipliers = [1 - ((distance - central_layer_distance) / distance) for distance in camera_distances]
        self.num_layers = len(self.layer_multipliers)

        # set the layer offsets (increase and decrease based on displacement)
        self.layer_offsets = [list(position).copy() for i in range(self.num_layers)]

    @property
    def target(self):
        if self.target_transform:
            return (
                int(self.target_transform.position[0]) + self.target_offset[0] - self.origin[0],
                int(self.target_transform.position[1]) + self.target_offset[1] - self.origin[1]
            )
        elif self.target_position:
            return (
                self.target_position[0] + self.target_offset[0] - self.origin[0],
                self.target_position[1] + self.target_offset[1] - self.origin[1]
            )
        return None

    def set_target(self, target):
        if isinstance(target, Entity):
            self.target_transform = target.get_component("transform")
            self.target_position = None
        elif target:
            self.target_position = tuple(target)
            self.target_transform = None
        else:
            self.target_transform = None
            self.target_position = None

    def update(self):
        if (t_pos := self.target) is None: return

        position = self.layer_offsets[self.central_layer]

        # calculate the displacement of the camera
        displacement = [
            (t_pos[0] - position[0]) * min(self.smoothing * self.registry["window"].dt, 1),
            (t_pos[1] - position[1]) * min(self.smoothing * self.registry["window"].dt, 1)
        ]

        # update the offsets for each layer
        for layer, multiplier in zip(self.layer_offsets, self.layer_multipliers):
            layer[0] += displacement[0] * multiplier
            layer[1] += displacement[1] * multiplier

    def world_to_camera(self, layer, position):
        return (
            round(position[0] - self.layer_offsets[layer][0]),
            round(position[1] - self.layer_offsets[layer][1])
        )

    def camera_to_world(self, layer, position):
        return (
            round(position[0] + self.layer_offsets[layer][0]),
            round(position[1] + self.layer_offsets[layer][1])
        )