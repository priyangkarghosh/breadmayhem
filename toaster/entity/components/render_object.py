from toaster.entity.component import Component
from toaster.registry.registry import Registry


class RenderObject(Component):
    def __init__(self, renderer=None, layer=0):
        super().__init__("render_object")

        self.layer = layer
        self.transform = None

        if renderer: self._renderer = renderer
        else: self._renderer = Registry.instance()['renderer']

    def on_attach(self):
        super().on_attach()
        self.transform = self.owner.get_component("transform")
        if self.transform is None:
            return Exception("Entity does not have a transform component attached.")

    def render(self):
        return


class LitRenderObject(RenderObject):
    def __init__(self, renderer=None, layer=0, texture=None, normal_map=None, vertices=None):
        super().__init__(renderer, layer)

        self.texture = texture
        self.normal_map = normal_map
        # self.vertices = vertices

    def render(self):
        layer_dict = self._renderer.layers[self.layer]
        blit_position = self._renderer.camera.world_to_camera(self.transform.position)
        layer_dict['lit_surf'].blit(self.texture, blit_position)
        if self.normal_map: layer_dict['normal_surf'].blit(self.normal_map, blit_position)
        layer_dict['render_lit'] = True


class UnlitRenderObject(RenderObject):
    def __init__(self, renderer=None, layer=0, texture=None):
        super().__init__(renderer, layer)

        self.texture = texture

    def render(self):
        layer_dict = self._renderer.layers[self.layer]
        blit_position = self._renderer.camera.world_to_camera(self.transform.position)
        layer_dict['unlit_surf'].blit(self.texture, blit_position)
        layer_dict['render_unlit'] = True
