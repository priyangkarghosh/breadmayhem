from toaster.registry.registry import Registry


class RegistryItem:
    def __init__(self, item_id=None):
        # get the item id
        self.item_id = self.__class__.__name__ if not item_id else item_id

        # register self to the registry
        self.registry = Registry.instance()
        self.registry.register_item(self.item_id, self)

    def update(self):
        pass

    def deregister(self):
        self.registry.deregister_item(self.item_id)
