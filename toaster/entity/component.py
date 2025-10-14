from toaster.registry.registry import Registry


class Component:
    def __init__(self, component_id):
        self.owner = None
        self.id = component_id
        self.responses = {}

        self.registry = Registry.instance()

    def on_attach(self):
        pass

    def on_detach(self):
        pass

    def handle_event(self, event_id):
        if event_id not in self.responses: return
        for response in self.responses[event_id]: response()

    def register_event(self, event_id):
        if not self.owner.is_registered(event_id, self.id):
            self.owner.register_observer(event_id, self.id)

    def register_response(self, event_id, response):
        if event_id not in self.responses: self.responses[event_id] = []
        self.responses[event_id].append(response)
