from typing import Optional, TYPE_CHECKING
from toaster.entity.entity import Entity
from toaster.registry.registry_item import RegistryItem
if TYPE_CHECKING: from toaster.entity.components.transform import Transform


class Camera(RegistryItem):
    def __init__(
        self,
        central_layer: int,
        camera_distances: list[int],
        position: tuple[int, int] = (0, 0),
        offset: tuple[int, int] = (0, 0),
        origin: tuple[int, int] = (0, 0),
        smoothing: float = 1.0
    ) -> None:
        super().__init__("camera")
        
        # origin and smoothing
        self.origin: tuple[int, int] = origin
        self.smoothing: float = smoothing
        
        # target configuration
        self.target_offset: tuple[int, int] = offset
        self.target_transform: Optional['Transform'] = None
        self.target_position: Optional[tuple[int, int]] = None
        
        # calculate the layer offset multipliers
        # **assume central layer index is always valid and distances are formatted correctly
        self.central_layer: int = central_layer
        central_layer_distance: int = camera_distances[self.central_layer]
        self.layer_multipliers: list[float] = [
            1 - ((distance - central_layer_distance) / distance) 
            for distance in camera_distances
        ]
        self.num_layers: int = len(self.layer_multipliers)
        
        # set the layer offsets (increase and decrease based on displacement)
        self.layer_offsets: list[list[float]] = [
            [float(position[0]), float(position[1])] 
            for _ in range(self.num_layers)
        ]
    
    @property
    def target(self) -> Optional[tuple[int, int]]:
        if self.target_transform is not None:
            return (
                int(self.target_transform.position[0]) + self.target_offset[0] - self.origin[0],
                int(self.target_transform.position[1]) + self.target_offset[1] - self.origin[1]
            )
        elif self.target_position is not None:
            return (
                self.target_position[0] + self.target_offset[0] - self.origin[0],
                self.target_position[1] + self.target_offset[1] - self.origin[1]
            )
        return None
    
    def set_target(self, target: Optional[Entity | tuple[int, int]]) -> None:
        if isinstance(target, Entity):
            transform = target.get_component("transform")
            self.target_transform = transform  # type: ignore
            self.target_position = None
        elif target is not None:
            self.target_position = tuple(target)  # type: ignore
            self.target_transform = None
        else:
            self.target_transform = None
            self.target_position = None
    
    def update(self) -> None:
        if (t_pos := self.target) is None: return
        
        position: list[float] = self.layer_offsets[self.central_layer]
        
        # calculate the displacement of the camera
        dt: float = self.registry["window"].dt
        displacement: list[float] = [
            (t_pos[0] - position[0]) * min(self.smoothing * dt, 1.0),
            (t_pos[1] - position[1]) * min(self.smoothing * dt, 1.0)
        ]
        
        # update the offsets for each layer
        for layer, multiplier in zip(self.layer_offsets, self.layer_multipliers):
            layer[0] += displacement[0] * multiplier
            layer[1] += displacement[1] * multiplier
    
    def world_to_camera(self, layer: int, position: tuple[float, float]) -> tuple[int, int]:
        return (
            round(position[0] - self.layer_offsets[layer][0]),
            round(position[1] - self.layer_offsets[layer][1])
        )
    
    def camera_to_world(self, layer: int, position: tuple[float, float]) -> tuple[int, int]:
        return (
            round(position[0] + self.layer_offsets[layer][0]),
            round(position[1] + self.layer_offsets[layer][1])
        )
