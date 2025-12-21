from typing import TYPE_CHECKING
if TYPE_CHECKING: from toaster.rendering.renderer import Renderer

import pygame
from math import log2, ceil
from toaster.rendering.opengl.double_buffer import DoubleTextureBuffer

class Lighting:
    def __init__(self, renderer: 'Renderer') -> None:
        self.renderer = renderer

        # get lighting shader
        light_sh = renderer.shaders.get_shader('lighting')
        if light_sh is None: raise RuntimeError("Lighting shader not loaded")

        # load programs from shader
        self.screen_uv = renderer.create_screen_vao(light_sh.get_program('screen_uv'))
        self.jump_flood = renderer.create_screen_vao(light_sh.get_program('jump_flood'))
        self.distance_field = renderer.create_screen_vao(light_sh.get_program('distance_field'))

        # create render textures
        self.jump_dbuf = DoubleTextureBuffer.create(renderer, swizzle='RGBA')
        
        self.dist_tex = renderer.create_texture(swizzle='RGBA')
        self.dist_buf = renderer.ctx.framebuffer(color_attachments=[self.dist_tex])
    
    def render(
        self, 
        albedo: pygame.Surface, 
        occlusion: pygame.Surface, 
        emission: pygame.Surface
    ) -> None:
        self.jump_dbuf.clear()

        # write occlusion buffer to jump1
        self.jump_dbuf.current.tex.write(occlusion.get_view('1'))

        # render seed to jump buffer
        self.jump_dbuf.next.buf.use()
        self.jump_dbuf.current.tex.use(0)
        self.screen_uv.program['tex'] = 0
        self.screen_uv.render()
        self.jump_dbuf.flip()

        # init jump flood algorithm
        self.jump_flood.program['tex'] = 0
        steps = max(1, int(ceil(log2(max(self.renderer.render_size)))))
        step_size_px = 1 << (steps - 1)

        # start jump flood algorithm
        # -> final ends up rendering to current buf
        # -> can add smoothing steps if necessary
        for _ in range(steps):
            # calculate and set step size
            self.jump_flood.program['stepSize'] = step_size_px
            step_size_px >>= 1

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
        self.distance_field.program['tex'] = 0
        self.distance_field.render()
