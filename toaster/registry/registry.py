class Registry:
    _instance = None

    @staticmethod
    def instance():
        if Registry._instance is None: Registry._instance = Registry()
        return Registry._instance

    def __init__(self):
        if Registry._instance is not None:
            raise Exception("Multiple instances of Singleton created.")
        self.items: dict = {}

    def _get(self, name: str):
        try: return self.items[name]
        except KeyError: raise AttributeError(f"Registry has no item '{name}'")

    # dict access
    def __getitem__(self, name): return self._get(name)
    def __getattr__(self, name): return self._get(name)
    def __contains__(self, item): return item in self.items

    def register_item(self, reg_id, item):
        if reg_id in self.items:
            raise Exception("ID is already registered.")
        self.items[reg_id] = item

    def deregister_item(self, reg_id):
        return self.items.pop(reg_id, None)
