from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING: from .component import Component

class Entity:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.components: dict[str, 'Component'] = {}
        # event id: listeners (component ids)
        self.events: dict[str, set[str]] = {}
    
    def attach_component(self, component: 'Component') -> None:
        if component.id in self.components:
            raise ValueError("Entity already contains this type of component.")
        if component.owner is not None:
            component.owner.detach_component(component.id)
        self.components[component.id] = component
        component.owner = self
        component.on_attach()
    
    def get_component(self, component_id: str) -> Optional['Component']:
        return self.components.get(component_id)
    
    def detach_component(self, component_id: str) -> 'Component':
        if component_id not in self.components:
            raise ValueError("Entity does not contain this type of component.")
        component = self.components.pop(component_id)
        component.on_detach()
        return component
    
    def add_event(self, event_id: str) -> None:
        if event_id in self.events:
            raise ValueError("Event ID already exists.")
        self.events[event_id] = set()
    
    def is_registered(self, event_id: str, component_id: str) -> bool:
        return event_id in self.events and component_id in self.events[event_id]
    
    def register_observer(self, event_id: str, component_id: str) -> None:
        if event_id not in self.events:
            raise ValueError("Event does not exist.")
        if component_id in self.events[event_id]:
            raise ValueError("Component is already observing this event.")
        self.events[event_id].add(component_id)
    
    def broadcast_event(self, event_id: str) -> None:
        if event_id not in self.events:
            raise ValueError("Event does not exist.")
        for component_id in self.events[event_id]:
            self.components[component_id].handle_event(event_id)