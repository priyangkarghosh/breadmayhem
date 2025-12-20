from toaster.entity.components.transform import Transform
from toaster.entity.entity import Entity
from toaster.entity.component import Component

DEFAULT_EVENTS = [
    "entry", "update", "fixed_update", "exit"
]


class GameObject(Entity):
    def __init__(
        self, 
        name: str, 
        position: tuple[float, float] = (0, 0), 
        scale: tuple[float, float] = (1, 1), 
        rotation: float = 0
    ) -> None:
        super().__init__(name)
        for event_id in DEFAULT_EVENTS:
            self.add_event(event_id)
        self.attach_component(Transform(position, scale, rotation))
    
    def attach_component(self, component: Component) -> None:
        super().attach_component(component)
        for event_id in DEFAULT_EVENTS:
            component.register_event(event_id)
    
    # broadcasts
    def enter(self) -> None:
        self.broadcast_event(DEFAULT_EVENTS[0])
    
    def update(self) -> None:
        self.broadcast_event(DEFAULT_EVENTS[1])
    
    def fixed_update(self) -> None:
        self.broadcast_event(DEFAULT_EVENTS[2])
    
    def exit(self) -> None:
        self.broadcast_event(DEFAULT_EVENTS[3])