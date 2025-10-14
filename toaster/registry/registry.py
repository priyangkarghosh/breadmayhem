class Registry:
    _instance = None

    @staticmethod
    def instance():
        if Registry._instance is None: Registry._instance = Registry()
        return Registry._instance

    def __init__(self):
        if Registry._instance is not None:
            raise Exception("Multiple instances of Singleton created.")
        self.items = {}

    def __getitem__(self, key): return self.items[key]
    def __contains__(self, item): return item in self.items

    def register_item(self, reg_id, item):
        if reg_id in self.items:
            raise Exception("ID is already registered.")
        self.items[reg_id] = item

    def deregister_item(self, reg_id):
        return self.items.pop(reg_id, None)
