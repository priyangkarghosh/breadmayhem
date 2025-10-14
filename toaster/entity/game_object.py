from toaster.entity.components.transform import Transform
from toaster.entity.entity import Entity

DEFAULT_EVENTS = [
    "entry", "update", "fixed_update", "exit"
]


class GameObject(Entity):
    def __init__(self, name, position=(0, 0), scale=(1, 1), rotation=0):
        super().__init__(name)
        for event_id in DEFAULT_EVENTS: self.add_event(event_id)
        self.attach_component(Transform(position, scale, rotation))

    def attach_component(self, component):
        super().attach_component(component)
        for event_id in DEFAULT_EVENTS:
            component.register_event(event_id)

    # broadcasts
    def enter(self): self.broadcast_event(DEFAULT_EVENTS[0])
    def update(self): self.broadcast_event(DEFAULT_EVENTS[1])
    def fixed_update(self): self.broadcast_event(DEFAULT_EVENTS[2])
    def exit(self): self.broadcast_event(DEFAULT_EVENTS[3])

