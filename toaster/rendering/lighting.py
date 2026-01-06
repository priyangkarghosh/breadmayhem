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
        lighting_sh = renderer.shaders.get_shader('lighting')
        if lighting_sh is None: raise RuntimeError("Lighting shader not loaded")

        # load programs from shader
        self.cascades = renderer.create_screen_vao(lighting_sh.get_program('cascades'))
        self.blit = renderer.create_screen_vao(lighting_sh.get_program('blit'))

        # create render textures/buffers
        self.albedo_tex = renderer.create_texture(swizzle='RGBA') # these are BGRA bc of pygame
        self.absorption_tex = renderer.create_texture(swizzle='RGBA') # these are BGRA bc of pygame
        self.emissive_tex = renderer.create_texture(swizzle='RGBA')

        self.diff_dbuf = DoubleTextureBuffer.create(renderer, swizzle='RGBA', size=self.cascade_resolution)
        self.gi_dbuf = DoubleTextureBuffer.create(
            renderer, 
            size=self.cascade_resolution,
            swizzle='RGBA', 
            filter=(mgl.LINEAR, mgl.LINEAR),
            dtype='f2'
        )

        # dda
        self.dda_kernel = renderer.shaders.get_shader('dda').get_kernel('dda')
        self.dda_buff = self.renderer.ctx.buffer(reserve=(4 * (ceil(self.renderer.render_size[0] / float(32)) * ceil(self.renderer.render_size[1] / float(32)))))

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

        # dda
        t = (ceil(self.renderer.render_size[0] / float(32)), ceil(self.renderer.render_size[1] / float(32)))
        self.dda_kernel.bind_ssbo("Grid", self.dda_buff)
        self.dda_kernel.set_uniforms(_mainTex=0)
        self.dda_kernel.dispatch(t[0], t[1])
        
        # cascades
        self.gi_dbuf.clear(a=1)
        self.cascades.program['_mainTex'] = 0
        self.cascades.program['_emissiveTex'] = 1
        self.cascades.program['_absorptionTex'] = 2

        self.cascades.program['_renderResolution'] = self.renderer.render_size
        self.cascades.program['_cascadeResolution'] = self.cascade_resolution
        self.cascades.program['_cascadeScale'] = self.cascade_scale
        self.cascades.program['_cascadeInterval'] = self.cascade_interval
        self.cascades.program['_cascadeCount'] = self.cascade_count

        for i in range(self.cascade_count - 1, -1, -1):
            self.cascades.program['_cascadeIndex'] = i

            self.gi_dbuf.current.buf.use()
            self.gi_dbuf.next.tex().use(0) # next cascade
            self.cascades.render()
            self.gi_dbuf.flip()
        self.gi_dbuf.flip()

        self.renderer.ctx.screen.use()
        self.albedo_tex.use(0)
        self.gi_dbuf.current.tex().use(1)
        # self.blit.program['_mainTex'] = 0
        self.blit.program['_radianceTex'] = 1
        self.blit.program['_renderResolution'] = self.renderer.render_size
        self.blit.render()

        # for i in range(self.t, self.cascade_count):
        #     self.cascades.program['_cascadeIndex'] = i

        #     self.gi_dbuf.current.buf.use()
        #     self.gi_dbuf.next.tex().use(0) # next cascade
        #     self.cascades.render()
        #     self.gi_dbuf.flip()
        #     break
        # self.t += 1
        # self.t %= self.cascade_count
        # time.sleep(1)
        # print('It took %d milliseconds' % (float(query.elapsed) * 1e-6))
        # print('to render %d samples' % query.samples)

        # self.diff_dbuf.next.tex().use(0)
        # self.diffuse.program['_mainTex'] = 0
        # self.diff_dbuf.current.buf.use()

        # self.gi_dbuf.next.tex().use(1)
        # self.diffuse.program['_radianceTex'] = 1

        # self.occlusion_tex.write(occlusion.get_view('1'))
        # self.occlusion_tex.use(2)
        # self.diffuse.program['_occlusionTex'] = 2

        # #self.diffuse.program['_renderResolution'] = self.renderer.render_size
        # self.diffuse.render()
        # self.diff_dbuf.flip()

        #a = np.frombuffer(self.dda_buff.read(), dtype=np.uint32)
        #print(a, len(a))

