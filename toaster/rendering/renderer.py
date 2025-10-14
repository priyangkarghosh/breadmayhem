from array import array

import pygame
from toaster.rendering.opengl.material import Material
from toaster.registry.registry_item import RegistryItem

import moderngl

from toaster.rendering.lighting.light import *
from toaster.rendering.lighting.light_processor import LightProcessor


class Renderer(RegistryItem):
    def __init__(self, render_size=(300, 300), clear_colour=(0, 0, 0, 0)):
        super().__init__("renderer")
        assert "assets" in self.registry
        assert "window" in self.registry
        assert "camera" in self.registry

        # set the camera for the renderer
        self.camera = self.registry['camera']

        # set the render size and calculate the overall window size
        self.render_size = render_size
        self.aggregate_size = \
            (render_size[0] * self.camera.num_layers + self.camera.num_layers,
             render_size[1] + 1)  # layers are all stored horizontally

        # set the window size and reset colour
        self.window_size = self.registry['window'].size
        self.clear_colour = clear_colour
        self.view_rect = pygame.Rect(0, 0, *self.render_size)

        # calculate the conversion ratios
        self.PIXEL_TO_TANGENT = 2 / max(self.render_size)
        self.WORLD_TO_TANGENT = (1 / self.render_size[0],
                                 1 / self.render_size[1])

        # dict to store the texture ids
        self._textures = {}
        self._reg_tex_id = 0

        # create the context and screen buffer
        self.ctx = moderngl.create_context()

        # set the blend mode for the context
        self.ctx.enable(moderngl.BLEND)
        #self.ctx.blend_func = moderngl.PREMULTIPLIED_ALPHA

        # create the default screen buffer (covers whole screen)
        self.screen_buffer = self.ctx.buffer(data=array('f', [
            # position (x, y), uv coords (x, y)
            -1.0, 1.0, 0.0, 0.0,  # topleft
            1.0, 1.0, 1.0, 0.0,  # topright
            -1.0, -1.0, 0.0, 1.0,  # bottomleft
            1.0, -1.0, 1.0, 1.0,  # bottomright
        ]))

        # create and link the necessary textures
        self.render_texture = self.create_texture()
        self.link_texture("render_tex", self.render_texture)
        self.normal_texture = self.create_texture()
        self.link_texture("normal_tex", self.normal_texture)
        self.generic_texture = self.create_texture()
        self.link_texture("generic_tex", self.generic_texture)

        # set the layers
        self.layers = []

        # create the surfaces for the renderer
        temp_surf = pygame.Surface(self.render_size, pygame.SRCALPHA)

        # set each layer
        for i in range(self.camera.num_layers):
            subsurface_rect = (i * self.render_size[0], 0, *self.render_size)
            layer_dict = {
                "index": i,
                "tex_name": "layer_" + str(i),

                "lit_surf": temp_surf.copy(),
                "unlit_surf": temp_surf.copy(),
                "normal_surf": temp_surf.copy(),

                "render_lit": False, "render_unlit": False,
                "buffer": self.create_texture_buffer(),
            }

            self.link_texture(layer_dict['tex_name'], layer_dict['buffer'][1])
            self.layers.append(layer_dict)

        # list to hold render objects
        self.render_objects = []

        # create the light processor
        self.light_processor = LightProcessor(self)

        # create the materials
        self.default_mat = self.create_material()

        # add demo lights to scene
        self.add_light(PointLight(tint=(255, 255, 255), radius=150, intensity=0.3), self.camera.central_layer)
        self.add_light(
            PointLight(position=(230, -16), angle_range=0.3, direction=(-0.4, 0.6), tint=(255, 0, 255), radius=200,
                       intensity=0.8, opacity=0.3), self.camera.central_layer)
        self.add_light(
            PointLight(position=(60, -80), angle_range=0.4, direction=(0.4, 0.6), tint=(0, 255, 255), radius=400,
                       intensity=0.4), self.camera.central_layer)
        self.add_light(
            PointLight(position=(100, 170), angle_range=0.6, direction=(0.4, -0.6), tint=(255, 255, 0), radius=400,
                       intensity=0.6), self.camera.central_layer)
        self.add_light(
            PointLight(position=(12, 45), angle_range=0.3, direction=(1, 0), tint=(160, 255, 70), radius=100,
                       intensity=0.4), self.camera.central_layer)
        self.add_light(PointLight(position=(300, 100), tint=(180, 180, 180), radius=150, intensity=0.006),
                       self.camera.central_layer)
        self.add_light(GlobalLight(intensity=0.0001, opacity=0), self.camera.central_layer)
        self.add_light(GlobalLight(intensity=0.01, opacity=0), 0)
        self.add_light(GlobalLight(intensity=0.01, opacity=0), 3)

    # render the scene
    def render(self):
        mp = list(self.registry['inputs'].mouse_pos)
        mp[0] *= 0.5
        mp[1] *= 0.5

        self.light_processor.lights[self.camera.central_layer][0].position = self.camera.camera_to_world(self.camera.central_layer, mp)

        self.ctx.screen.clear()
        self.view_rect.topleft = self.camera.world_to_camera(3, (0, 0))

        # ::: RENDER INDIVIDUAL LAYERS
        for layer in reversed(self.layers):
            # clear the layer's frame buffer
            layer['buffer'][0].clear()

            # use the layer's buffer
            layer['buffer'][0].use()

            # if the lit surface was rendered to
            if layer['render_lit']:
                # change the blend function
                self.ctx.blend_func = moderngl.ADDITIVE_BLENDING

                # write the texture and the normal map using the layer surfaces
                self.render_texture.write(layer['lit_surf'].get_view('1'))
                self.normal_texture.write(layer['normal_surf'].get_view('1'))

                # render the lighting for this layer
                self.light_processor.render(layer['buffer'][0], layer['index'])

                # clear the surfaces
                layer['lit_surf'].fill((0, 0, 0, 0))
                layer['normal_surf'].fill((0, 0, 0, 0))

                # change the blend function
                self.ctx.blend_func = moderngl.DEFAULT_BLENDING

            #self.ctx.disable(moderngl.BLEND)
            # if the unlit surface was rendered to
            if layer['render_unlit']:
                # write the unlit surface to the render_texture
                self.generic_texture.write(layer['unlit_surf'].get_view('1'))

                # set the texture of the program
                self.default_mat.program['tex'] = self.texture_id("generic_tex")

                # disable flipping
                self.default_mat.program['flip'] = False

                # render the unlit texture on top
                self.default_mat.surface.render()

                # clear the surface
                layer['unlit_surf'].fill(self.clear_colour)

            # ::: RENDER TO SCREEN
            self.ctx.screen.use()
            self.default_mat.program['tex'] = self.texture_id(layer['tex_name'])
            self.default_mat.program['flip'] = True
            self.default_mat.surface.render()
            #self.ctx.enable(moderngl.BLEND)

    # add a light to the scene
    def add_light(self, light, layer=0):
        self.light_processor.lights[layer].append(light)

    # texture linking functions
    def link_texture(self, texture_name, texture):
        texture.use(self._reg_tex_id)
        self._textures[texture_name] = self._reg_tex_id
        self._reg_tex_id += 1
        return self._reg_tex_id - 1

    def texture_id(self, texture_name):
        return self._textures[texture_name]

    def unlink_texture(self, texture_name):
        del self._textures[texture_name]

    # creation functions
    def create_texture(self, components=4, swizzle='BGRA', size=None):
        if not size: size = self.render_size
        texture = self.ctx.texture(size, components)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.repeat_x, texture.repeat_y = False, False
        texture.swizzle = swizzle
        return texture

    def create_texture_buffer(self, components=4):
        buffer = self.ctx.framebuffer(color_attachments=[self.create_texture(components, 'RGBA')])
        return buffer, buffer.color_attachments[0]

    def create_program(self, vert="default_vert", frag="default_frag"):
        return self.ctx.program(
            vertex_shader=self.registry["assets"].get_shader(vert),
            fragment_shader=self.registry["assets"].get_shader(frag)
        )

    def create_material(self, vert="default_vert", frag="default_frag"):
        program = self.create_program(vert=vert, frag=frag)

        return Material(
            program, self.ctx.vertex_array(
                program, [(self.screen_buffer, '2f 2f', 'vert', 'texcoord')], mode=moderngl.TRIANGLE_STRIP
            )
        )

    def world_to_tangent(self, point, layer):
        point = self.registry['camera'].world_to_camera(layer, point)
        return point[0] * self.WORLD_TO_TANGENT[0], point[1] * self.WORLD_TO_TANGENT[1]

    def quit(self):
        self.render_texture.release()
        self.normal_texture.release()
