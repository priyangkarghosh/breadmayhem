from typing import Optional
from pygame import Rect

STATIC = 0
KINEMATIC = 1
DYNAMIC = 2


class PhysicsRect:
    _id: int = 0
    
    def __init__(
        self, 
        collision_mode: int = 0, 
        collision_layer: int = 0, 
        phys_rect: Optional[Rect] = None
    ) -> None:
        self.collision_mode: int = collision_mode
        self.collision_layer: int = collision_layer
        self.phys_rect: Optional[Rect] = phys_rect
        self.rect_id: int = PhysicsRect._id
        PhysicsRect._id += 1
    
    @property
    def static(self) -> bool:
        return self.collision_mode == STATIC
    
    @property
    def kinematic(self) -> bool:
        return self.collision_mode == KINEMATIC
    
    @property
    def dynamic(self) -> bool:
        return self.collision_mode == DYNAMIC
    
    @property
    def rect(self) -> Optional[Rect]:
        return self.phys_rect
    
    def __hash__(self) -> int:
        return self.rect_id
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PhysicsRect): return False
        return self.rect_id == other.rect_id