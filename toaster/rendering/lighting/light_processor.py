from array import array

import moderngl
from pygame import Rect

from toaster.rendering.opengl.double_buffer import DoubleBuffer
from toaster.rendering.renderer import Material
from toaster.rendering.lighting.light import *

LIGHT_RESOLUTION = 42
SHADOW_STRENGTH = 0.3

SHADOWMODE_SHADE = 0
SHADOWMODE_CUTOUT = 1


class LightProcessor:
    def __init__(self, renderer):
        self._renderer = renderer

        # create the shadow buffer (has to be a double buffer for two passes)
        self.shadow_buffer = DoubleBuffer(self._renderer, 1)

        # link the pre-pass shadow texture
        self.shade_pass_shadow_texture = self.shadow_buffer.get_texture(other=False)
        self._renderer.link_texture("shade_pass_shadow_tex", self.shade_pass_shadow_texture)

        # link the final pass shadow texture
        self.blur_pass_shadow_texture = self.shadow_buffer.get_texture(other=True)
        self._renderer.link_texture("blur_pass_shadow_tex", self.blur_pass_shadow_texture)

        # create the vertex buffer for the shadows
        vertices = array('f', [float(0)] * 14400)
        self.shadow_obj_buffer = renderer.ctx.buffer(data=vertices, dynamic=True)
        shadow_program = self._renderer.create_program(vert="shadowmap_vert", frag="shadowmap_frag")
        shadow_surface = renderer.ctx.vertex_array(
            shadow_program, [(self.shadow_obj_buffer, '2f 4f', 'in_position', 'in_normal')]
        )

        # create the required lighting materials
        self.point_mat = self._renderer.create_material(frag="fragment_point_light")
        self.global_mat = self._renderer.create_material(frag="fragment_global_light")
        self.shadow_mat = Material(program=shadow_program, surface=shadow_surface)
        self.blur_mat = self._renderer.create_material(frag="fragment_blur")

        # init program surfaces
        self.point_mat.program['render_tex'] = self._renderer.texture_id("render_tex")
        self.point_mat.program['normal_tex'] = self._renderer.texture_id("normal_tex")
        self.point_mat.program['shadow_map'] = self._renderer.texture_id("blur_pass_shadow_tex")

        self.global_mat.program['render_tex'] = self._renderer.texture_id("render_tex")

        self.blur_mat.program['tex'] = self._renderer.texture_id("shade_pass_shadow_tex")
        self.blur_mat.program['resolution'] = self._renderer.render_size

        self.shadow_mat.program['resolution'] = self._renderer.render_size

        # init light list per layer
        self.lights = [[] for i in range(self._renderer.camera.num_layers)]

    def render(self, layer_buffer, layer):
        vertices = []
        # new vertices
        for trect in self._renderer.registry['physics'].iter_bodies:
            rect = Rect(*self._renderer.camera.world_to_camera(layer, trect.rect.topleft), *trect.rect.size)
            vertices.extend([
                float(rect.left), float(rect.top), -1.0, 0.0, 0.0, -1.0,
                float(rect.right), float(rect.top), 0.0, -1.0, 1.0, 0.0,
                float(rect.left), float(rect.bottom), 0.0, 1.0, -1.0, 0.0,
                float(rect.left), float(rect.bottom), 0.0, 1.0, -1.0, 0.0,
                float(rect.right), float(rect.bottom), 1.0, 0.0, 0.0, 1.0,
                float(rect.right), float(rect.top), 0.0, -1.0, 1.0, 0.0,
            ])

        vertices = array('f', vertices)
        #self.shadow_obj_buffer.clear()
        self.shadow_obj_buffer.write(vertices)

        # render all the lights
        for light in self.lights[layer]:
            if not light.enabled: continue

            if isinstance(light, PointLight):
                # clear the shadow buffer
                self.shadow_buffer.clear()

                # shade the shadows for this light
                self.shadow_buffer.buffer.use()
                self.shadow_mat.program['mode'] = SHADOWMODE_SHADE
                self.shadow_mat.program['light_position'] = self._renderer.camera.world_to_camera(layer, light.position)
                self.shadow_mat.surface.render(moderngl.TRIANGLES)

                # change the blend_func so objects are cutout from shadow properly
                self._renderer.ctx.blend_equation = moderngl.FUNC_REVERSE_SUBTRACT

                # cut out the shadow
                self.shadow_mat.program['mode'] = SHADOWMODE_CUTOUT
                self.shadow_mat.surface.render(moderngl.TRIANGLES)

                # reset the blend_func back to its original
                self._renderer.ctx.blend_equation = moderngl.FUNC_ADD

                # flip the buffer and use the flipped buffer
                self.shadow_buffer.flip()
                self.shadow_buffer.buffer.use()

                # use blur to fake soft shadows
                self.blur_mat.surface.render()

                # now render the light
                layer_buffer.use()

                # set the properties of the light
                self.point_mat.program['light_position'] = self._renderer.world_to_tangent(light.position, layer)
                self.point_mat.program['light_direction'] = light.direction
                self.point_mat.program['angle_range'] = light.angle_range
                self.point_mat.program['radius'] = light.radius * self._renderer.PIXEL_TO_TANGENT
                self.point_mat.program['power'] = light.power
                self.point_mat.program['tint'] = light.tint
                self.point_mat.program['intensity'] = light.intensity
                self.point_mat.program['opacity'] = light.opacity

                # render the light
                self.point_mat.surface.render()
            else:
                # set the properties of the light
                self.global_mat.program['tint'] = light.tint
                self.global_mat.program['intensity'] = light.intensity
                self.global_mat.program['opacity'] = light.opacity

                # render the light
                self.global_mat.surface.render()
