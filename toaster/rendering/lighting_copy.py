import time
from typing import TYPE_CHECKING
if TYPE_CHECKING: from toaster.rendering.renderer import Renderer

import numpy as np
import pygame
import moderngl as mgl
from math import log2, ceil
from toaster.rendering.opengl.double_buffer import DoubleTextureBuffer

class Lighting:
    def __init__(
        self, 
        renderer: 'Renderer',
    ) -> None:
        self.renderer = renderer

        # gi properties
        self.cascade_count: int = 7
        self.cascade_scale: int = 1
        self.cascade_interval: float = 1

        # calculate cascade res
        cc = float(2 ** (self.cascade_count - 1))
        self.cascade_resolution = (
            int(ceil(self.renderer.render_size[0] / cc) * cc),
            int(ceil(self.renderer.render_size[1] / cc) * cc)
        )
        
        # get lighting shader
        lighting_sh = renderer.shaders.get_shader('l2')
        if lighting_sh is None: raise RuntimeError("Lighting shader not loaded")

        # load programs from shader
        self.build = lighting_sh.get_kernel('build_cascade')
        self.merge = lighting_sh.get_kernel('merge_cascades')
        self.blit = renderer.create_screen_vao(lighting_sh.get_program('blit'))

        # create render textures/buffers
        self.albedo_tex = renderer.create_texture(swizzle='RGBA') # these are BGRA bc of pygame
        self.absorption_tex = renderer.create_texture(swizzle='RGBA') # these are BGRA bc of pygame
        self.emissive_tex = renderer.create_texture(swizzle='RGBA')
        self.cascades = renderer.ctx.texture_array(
            size=(*self.cascade_resolution, self.cascade_count),
            components=4, dtype='f2'
        )
        self.merge_tex = renderer.create_texture(self.cascade_resolution, swizzle='RGBA')

        self.t = 0

    def render(
        self, 
        albedo: pygame.Surface, 
        emissive: pygame.Surface,
        absorption: pygame.Surface
    ) -> None:
        # set up textures
        self.albedo_tex.write(albedo.get_view('1'))
        self.albedo_tex.use(0)

        self.emissive_tex.write(emissive.get_view('1'))
        self.emissive_tex.use(1)
        self.emissive_tex.build_mipmaps()

        self.absorption_tex.write(absorption.get_view('1'))
        self.absorption_tex.use(2)
        self.absorption_tex.build_mipmaps()
        
        # cascades
        self.build.set_uniforms(
            _emissiveTex=1, 
            _albedoTex=2,
            _renderResolution=self.renderer.render_size,
            _cascadeResolution=self.cascade_resolution,
            _cascadeScale=self.cascade_scale,
            _cascadeInterval=self.cascade_interval,
        #    _cascadeCount=self.cascade_count
        )

        self.cascades.bind_to_image(0, read=False)
        for i in range(0, self.cascade_count):
            self.build.set_uniform('_cascadeIndex', i)
            self.build.dispatch(
                ceil(self.cascade_resolution[0] / 16.0), 
                ceil(self.cascade_resolution[1] / 16.0)
            )

        self.merge_tex.bind_to_image(0, read=False)
        self.merge.set_uniforms(
            _cascadeTex=0, 
            _cascadeResolution=self.cascade_resolution, 
            _cascadeCount=self.cascade_count
        )
        self.merge.dispatch(
            ceil(self.cascade_resolution[0] / 16.0), 
            ceil(self.cascade_resolution[1] / 16.0)
        )

        self.display()

    def display(self):
        # self.renderer.ctx.screen.use()
        # self.cascades.use(0)
        # self.blit.program['_cascadeTex'] = 0
        # self.blit.program['_cascadeIndex'] = self.t
        # self.blit.render()

        # self.t += 1
        # self.t %= self.cascade_count

        d = self.renderer.default
        self.renderer.ctx.screen.use()
        self.merge_tex.use(0)
        d.program['_mainTex'] = 0
        d.program['_flip'] = False
        d.render()
