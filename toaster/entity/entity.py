class Entity:
    def __init__(self, name):
        self.name = name
        self.components = {}

        # event id: listeners (entity registry)
        self.events = {}

    def attach_component(self, component):
        if component.id in self.components:
            raise Exception("Entity already contains this type of handler.")
        if component.owner is not None:
            component.owner.detach_component(component.id)

        self.components[component.id] = component
        component.owner = self
        component.on_attach()

    def get_component(self, component_id):
        return self.components.get(component_id, None)

    def detach_component(self, component_id):
        if component_id not in self.components:
            raise Exception("Entity does not contain this type of component.")

        component = self.components.pop(component_id)
        component.on_detach()
        return component

    def add_event(self, event_id):
        if event_id in self.events:
            raise Exception("Event ID already exists.")
        self.events[event_id] = set()

    def is_registered(self, event_id, component_id):
        return event_id in self.events and component_id in self.events

    def register_observer(self, event_id, component_id):
        if event_id not in self.events:
            raise Exception("Event does not exist.")
        if component_id in self.events[event_id]:
            raise Exception("Component is already observing this event.")
        self.events[event_id].add(component_id)

    def broadcast_event(self, event_id):
        for component_id in self.events[event_id]:
            self.components[component_id].handle_event(event_id)
