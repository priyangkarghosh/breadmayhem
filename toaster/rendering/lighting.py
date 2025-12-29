from typing import TYPE_CHECKING
if TYPE_CHECKING: from toaster.rendering.renderer import Renderer

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
        self.cascade_count: int = 6
        self.cascade_scale: int = 1
        self.cascade_interval: float = 1

        # calculate cascade res
        cc = 2 ** self.cascade_count
        self.cascade_resolution = (
            int(ceil((self.renderer.render_size[0] / self.cascade_scale) / float(cc)) * cc),
            int(ceil((self.renderer.render_size[1] / self.cascade_scale) / float(cc)) * cc)
        )

        # get lighting shader
        lighting_sh = renderer.shaders.get_shader('lighting')
        if lighting_sh is None: raise RuntimeError("Lighting shader not loaded")

        # load programs from shader
        self.cascades = renderer.create_screen_vao(lighting_sh.get_program('cascades'))
        self.diffuse = renderer.create_screen_vao(lighting_sh.get_program('diffuse'))

        # create render textures/buffers
        self.dist_tex = renderer.create_texture(swizzle='RGBA')
        self.albedo_tex = renderer.create_texture(swizzle='RGBA') # these are BGRA bc of pygame
        self.emissive_tex = renderer.create_texture(swizzle='RGBA')
        self.occlusion_tex = renderer.create_texture(swizzle='RGBA')

        self.diff_dbuf = DoubleTextureBuffer.create(renderer, swizzle='RGBA', size=self.cascade_resolution)
        self.gi_dbuf = DoubleTextureBuffer.create(
            renderer, 
            size=self.cascade_resolution,
            swizzle='RGBA', 
            filter=(mgl.LINEAR, mgl.LINEAR),
            dtype='f2'
        )
    
    def render(
        self, 
        albedo: pygame.Surface, 
        occlusion: pygame.Surface, 
        emissive: pygame.Surface
    ) -> None:
        # cascades
        self.gi_dbuf.clear(a=1)
        self.cascades.program['_tex'] = 0

        self.albedo_tex.write(albedo.get_view('1'))
        self.albedo_tex.use(1)
        #self.albedo_tex.build_mipmaps()
        self.cascades.program['_albedoTex'] = 1

        self.emissive_tex.write(emissive.get_view('1'))
        self.emissive_tex.use(2)
       # self.emissive_tex.build_mipmaps()
        self.cascades.program['_emissiveTex'] = 2

        #self.diff_dbuf.next.tex().use(3)
        #self.cascades.program['_diffuseTex'] = 3

        self.cascades.program['_renderResolution'] = self.renderer.render_size
        self.cascades.program['_cascadeResolution'] = self.cascade_resolution
        self.cascades.program['_cascadeScale'] = self.cascade_scale
        self.cascades.program['_cascadeInterval'] = self.cascade_interval
        self.cascades.program['_cascadeCount'] = self.cascade_count

        query = self.renderer.ctx.query(samples=True, time=True)
        with query:
            for i in range(self.cascade_count - 1, -1, -1):
                self.cascades.program['_cascadeIndex'] = i

                self.gi_dbuf.current.buf.use()
                self.gi_dbuf.next.tex().use(0) # next cascade
                self.cascades.render()
                self.gi_dbuf.flip()
        # print('It took %d milliseconds' % (float(query.elapsed) * 1e-6))
        # print('to render %d samples' % query.samples)

        # self.diff_dbuf.next.tex().use(0)
        # self.diffuse.program['_tex'] = 0
        # self.diff_dbuf.current.buf.use()

        # self.gi_dbuf.next.tex().use(1)
        # self.diffuse.program['_radianceTex'] = 1

        # self.occlusion_tex.write(occlusion.get_view('1'))
        # self.occlusion_tex.use(2)
        # self.diffuse.program['_occlusionTex'] = 2

        # #self.diffuse.program['_renderResolution'] = self.renderer.render_size
        # self.diffuse.render()
        # self.diff_dbuf.flip()

