from typing import TYPE_CHECKING
if TYPE_CHECKING: from toaster.rendering.renderer import Renderer


class Lighting:
    def __init__(self, renderer: 'Renderer') -> None:
        self.renderer = renderer

        # get lighting shader
        light_sh = renderer.shaders.get_shader('lighting')
        assert light_sh is not None

        # load programs from shader
        self.screen_uv = light_sh.get_program('screen_uv')
        self.jump_flood = light_sh.get_program('jump_flood')
        self.distance_field = light_sh.get_program('distance_field')

        # create render textures
        self.renderer.create_texture()
