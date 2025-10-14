from toaster.entity.component import Component


class SpriteRenderer(Component):
    def __init__(self, image=None, animation_controller=None):
        super().__init__("sprite_renderer")

        self.transform = None
        self.animation_controller = None
        self.image = None

    def on_attach(self):
        super().on_attach()
        self.transform = self.owner.get_component("transform")
        if self.transform is None:
            return Exception("Entity does not have a transform component attached.")
