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
        self.cascade_count: int = 5
        self.cascade_linear: int = 1
        self.cascade_interval: float = 2
        # self.cascade_resolution = (
        #     int(self.renderer.render_size[0] / self.cascade_linear),
        #     int(self.renderer.render_size[1] / self.cascade_linear)
        # )
        self.cascade_resolution = self.renderer.render_size

        # get lighting shader
        lighting_sh = renderer.shaders.get_shader('lighting')
        if lighting_sh is None: raise RuntimeError("Lighting shader not loaded")

        # load programs from shader
        self.screen_uv = renderer.create_screen_vao(lighting_sh.get_program('screen_uv'))
        self.jump_flood = renderer.create_screen_vao(lighting_sh.get_program('jump_flood'))
        self.distance_field = renderer.create_screen_vao(lighting_sh.get_program('distance_field'))
        self.cascades = renderer.create_screen_vao(lighting_sh.get_program('cascades'))

        # create render textures/buffers
        self.dist_tex = renderer.create_texture(swizzle='RGBA')
        self.albedo_tex = renderer.create_texture(swizzle='RGBA') # these are BGRA bc of pygame
        self.emissive_tex = renderer.create_texture(swizzle='RGBA')

        self.jump_dbuf = DoubleTextureBuffer.create(renderer, swizzle='RGBA')
        self.dist_buf = renderer.ctx.framebuffer(color_attachments=[self.dist_tex])
        self.gi_dbuf = DoubleTextureBuffer.create(
            renderer, 
            size=self.cascade_resolution,
            swizzle='RGBA', 
            #filter=(mgl.LINEAR, mgl.LINEAR)
        )
    
    def render(
        self, 
        albedo: pygame.Surface, 
        occlusion: pygame.Surface, 
        emissive: pygame.Surface
    ) -> None:
        self.jump_dbuf.clear()

        # write occlusion buffer to jump1
        self.jump_dbuf.current.tex.write(occlusion.get_view('1'))

        # render seed to jump buffer
        self.jump_dbuf.next.buf.use()
        self.jump_dbuf.current.tex.use(0)
        self.screen_uv.program['_tex'] = 0
        self.screen_uv.render()
        self.jump_dbuf.flip()

        # init jump flood algorithm
        self.jump_flood.program['_tex'] = 0

        max_dim = max(self.renderer.render_size)
        steps = max(1, int(ceil(log2(max_dim))))
        step_size_px = 1 << (steps - 1)
        aspect = (
            self.renderer.render_size[0] / max_dim,
            self.renderer.render_size[1] / max_dim
        )

        # start jump flood algorithm
        # -> final ends up rendering to current buf
        # -> can add smoothing steps if necessary
        for _ in range(steps):
            # calculate and set step size
            self.jump_flood.program['_stepSize'] = (
                int(step_size_px * aspect[0]), 
                int(step_size_px * aspect[1])
            ); step_size_px >>= 1

            # clear buffer
            self.jump_dbuf.next.buf.clear()
            self.jump_dbuf.next.buf.use()

            # run program
            self.jump_dbuf.current.tex.use(0)
            self.jump_flood.render()
            self.jump_dbuf.flip()

        # render distance field
        self.dist_buf.use()
        self.jump_dbuf.current.tex.use(0)
        self.distance_field.program['_tex'] = 0
        self.distance_field.render()

        # cascades
        self.gi_dbuf.clear(a=1)
        self.cascades.program['_tex'] = 0

        self.albedo_tex.write(albedo.get_view('1'))
        self.albedo_tex.use()
        self.cascades.program['_albedoTex'] = 1

        self.emissive_tex.write(emissive.get_view('1'))
        self.emissive_tex.use(2)
        self.cascades.program['_emissiveTex'] = 2

        self.dist_tex.use(3)
        #self.cascades.program['_distanceTex'] = 3

        self.jump_dbuf.current.tex.write(occlusion.get_view('1'))
        self.jump_dbuf.current.tex.use(4)
        self.cascades.program['_occlusionTex'] = 4

        self.cascades.program['_renderResolution'] = self.renderer.render_size
        self.cascades.program['_cascadeResolution'] = self.cascade_resolution
        self.cascades.program['_cascadeLinear'] = self.cascade_linear
        self.cascades.program['_cascadeInterval'] = self.cascade_interval
        self.cascades.program['_cascadeCount'] = self.cascade_count

        for i in range(self.cascade_count - 1, -1, -1):
            self.cascades.program['_cascadeIndex'] = i

            #self.gi_dbuf.current.buf.clear(alpha=1)
            self.gi_dbuf.current.buf.use()
            self.gi_dbuf.next.tex.use(0)
            self.cascades.render()
            self.gi_dbuf.flip()
            #break
        # for i in range(1, 2):
        #     self.cascades.program['_cascadeIndex'] = i

        #     #self.gi_dbuf.current.buf.clear(alpha=1)
        #     self.gi_dbuf.current.buf.use()
        #     self.gi_dbuf.next.tex.use(0)
        #     self.cascades.render()
        #     self.gi_dbuf.flip()
        #     #break
            
