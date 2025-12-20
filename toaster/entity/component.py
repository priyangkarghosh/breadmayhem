from typing import Optional, Callable, TYPE_CHECKING
if TYPE_CHECKING: from .entity import Entity

from toaster.registry.registry import Registry

class Component:
    def __init__(self, component_id: str) -> None:
        self.owner: Optional['Entity'] = None
        self.id: str = component_id
        self.responses: dict[str, list[Callable[[], None]]] = {}
        self.registry: Registry = Registry.instance()
    
    def on_attach(self) -> None:
        pass
    
    def on_detach(self) -> None:
        pass
    
    def handle_event(self, event_id: str) -> None:
        if event_id not in self.responses:
            return
        for response in self.responses[event_id]:
            response()
    
    def register_event(self, event_id: str) -> None:
        assert self.owner is not None, "Component must be attached to an entity"
        if not self.owner.is_registered(event_id, self.id):
            self.owner.register_observer(event_id, self.id)
    
    def register_response(self, event_id: str, response: Callable[[], None]) -> None:
        if event_id not in self.responses:
            self.responses[event_id] = []
        self.responses[event_id].append(response)
