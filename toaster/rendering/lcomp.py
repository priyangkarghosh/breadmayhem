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
        lighting_sh = renderer.shaders.get_shader('lcomp')
        if lighting_sh is None: raise RuntimeError("Lighting shader not loaded")

        # load programs from shader
        self.build = lighting_sh.get_kernel('build_cascade')
        self.blit = renderer.create_screen_vao(lighting_sh.get_program('blit'))

        # create render textures/buffers
        self.albedo_tex = renderer.create_texture(swizzle='RGBA')
        self.absorption_tex = renderer.create_texture(swizzle='RGBA')
        self.emissive_tex = renderer.create_texture(swizzle='RGBA')

        self.cascades_dbuf = DoubleTextureBuffer.create(
            renderer, 
            size=self.cascade_resolution,
            swizzle='RGBA', 
            filter=(mgl.LINEAR, mgl.LINEAR),
            dtype='f2'
        )

        # dda
        self.dda_kernel = renderer.shaders.get_shader('dda').get_kernel('dda')
        self.dda_buff = self.renderer.ctx.buffer(reserve=(4 * (ceil(self.renderer.render_size[0] / float(32)) * ceil(self.renderer.render_size[1] / float(32)))))

    def render(
        self, 
        albedo: pygame.Surface, 
        emissive: pygame.Surface,
        absorption: pygame.Surface
    ) -> None:
        # set up textures
        self.albedo_tex.write(albedo.get_view('1'))

        self.emissive_tex.write(emissive.get_view('1'))
        self.emissive_tex.build_mipmaps()
        self.emissive_tex.use(1)

        self.absorption_tex.write(absorption.get_view('1'))
        self.absorption_tex.build_mipmaps()
        self.absorption_tex.use(2)

        self.cascades_dbuf.clear(a=1)

        # set up dda
        t = (ceil(self.renderer.render_size[0] / float(32)), ceil(self.renderer.render_size[1] / float(32)))
        self.dda_kernel.bind_ssbo("Grid", self.dda_buff)
        self.dda_kernel.set_uniforms(_mainTex=2)
        self.dda_kernel.dispatch(t[0], t[1])

        # build cascades
        self.build.set_uniforms(
            _mergeTex=0, _emissiveTex=1, _absorptionTex=2,
            _renderResolution=self.renderer.render_size,
            _cascadeResolution=self.cascade_resolution,
            _cascadeScale=self.cascade_scale,
            _cascadeInterval=self.cascade_interval,
            _cascadeCount=self.cascade_count
        )

        for i in range(self.cascade_count - 1, -1, -1):
            self.cascades_dbuf.next.tex().bind_to_image(0)
            self.cascades_dbuf.current.tex().use(0)

            self.build.set_uniform('_cascadeIndex', i)
            self.build.dispatch(
                ceil(self.cascade_resolution[0] / 16.0), 
                ceil(self.cascade_resolution[1] / 16.0)
            )

            self.cascades_dbuf.flip()

        # self.cascades.bind_to_image(0)
        # self.merge.set_uniforms(
        #     _cascadeResolution=self.cascade_resolution, 
        #     _cascadeCount=self.cascade_count
        # )
        # for i in range(self.cascade_count, -1, -1):
        #     self.merge.set_uniform('_cascadeIndex', i)
        #     self.merge.dispatch(
        #         ceil(self.cascade_resolution[0] / 16.0), 
        #         ceil(self.cascade_resolution[1] / 16.0)
        #     )

        self.display()

    def display(self):
        self.renderer.ctx.screen.use()
        self.cascades_dbuf.current.tex().use(0)
        self.blit.program['_cascadeTex'] = 0
        self.blit.program['_renderResolution'] = self.renderer.render_size
        self.blit.render()
