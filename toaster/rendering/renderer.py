import pygame
import moderngl as mgl
from array import array
from typing import Literal, TypedDict

from toaster.rendering.camera import Camera
from toaster.rendering.opengl.material import Material
from toaster.registry.registry_item import RegistryItem


TextureType = Literal['albedo', 'occlusion', 'emissive', 'unlit']


class DirtyDict(TypedDict):
    albedo: bool
    occlusion: bool
    emissive: bool
    unlit: bool


class LayerDict(TypedDict):
    index: int
    tex_name: str
    albedo_surf: pygame.Surface
    occlusion_surf: pygame.Surface
    emissive_surf: pygame.Surface
    unlit_surf: pygame.Surface
    buffer: tuple[mgl.Framebuffer, mgl.Texture]
    dirty: DirtyDict


class Renderer(RegistryItem):    
    def __init__(
        self,
        render_size: tuple[int, int] = (300, 300),
        clear_colour: tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> None:
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
        self.ctx = mgl.create_context()
        
        # set the blend mode for the context
        self.ctx.enable(mgl.BLEND)
        
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

        self.default_mat = self.create_material()
        
        # texture types we support
        self.texture_types = ['albedo', 'occlusion', 'emissive', 'unlit']
        
        # create the layers
        self.layers = []
        for i in range(self.camera.num_layers):
            layer_dict: LayerDict = {
                "index": i,
                "tex_name": "layer_" + str(i),

                "albedo_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),
                "occlusion_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),
                "emissive_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),
                "unlit_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),

                "buffer": self.create_texture_buffer(),
                "dirty": {
                    "albedo": False,
                    "occlusion": False,
                    "emissive": False,
                    "unlit": False
                }
            }
            self.link_texture(layer_dict['tex_name'], layer_dict['buffer'][1])
            self.layers.append(layer_dict)
        
        # list to hold render objects
        self.render_objects = []
    
    def mark_dirty(self, layer_index: int, texture_type: TextureType) -> None:
        if 0 <= layer_index < len(self.layers):
            if texture_type in self.texture_types:
                self.layers[layer_index]['dirty'][texture_type] = True
    
    def render(self) -> None:
        self.ctx.screen.clear()
        self.view_rect.topleft = self.camera.world_to_camera(3, (0, 0))
        
        # ::: RENDER INDIVIDUAL LAYERS
        for layer in reversed(self.layers):
            # only process layer if something is dirty
            if not any(layer['dirty'].values()):
                self.ctx.screen.use()
                self.default_mat.program['tex'] = self.texture_id(layer['tex_name'])
                self.default_mat.program['flip'] = True
                self.default_mat.surface.render()
                continue
            
            # use the layers frame buffer
            layer['buffer'][0].clear()
            layer['buffer'][0].use()
            
            # process lit texture
            if layer['dirty']['albedo'] or layer['dirty']['occlusion'] or layer['dirty']['emissive']:
                layer['dirty']['albedo'] = layer['dirty']['occlusion'] = layer['dirty']['emissive'] = False
            
            # process unlit texture
            if layer['dirty']['unlit']:
                # write the unlit surface to the render_texture
                self.render_texture.write(layer['unlit_surf'].get_view('1'))
                
                # set the texture of the program
                self.default_mat.program['tex'] = self.texture_id("render_tex")
                
                # disable flipping
                self.default_mat.program['flip'] = False
                self.default_mat.surface.render()
                
                # clear the surface
                layer['unlit_surf'].fill(self.clear_colour)
                
                # mark as clean
                layer['dirty']['unlit'] = False
            
            # ::: RENDER TO SCREEN
            self.ctx.screen.use()
            self.default_mat.program['tex'] = self.texture_id(layer['tex_name'])
            self.default_mat.program['flip'] = True
            self.default_mat.surface.render()
    
    def link_texture(self, texture_name: str, texture: mgl.Texture) -> int:
        texture.use(self._reg_tex_id)
        self._textures[texture_name] = self._reg_tex_id
        self._reg_tex_id += 1
        return self._reg_tex_id - 1
    
    def texture_id(self, texture_name: str) -> int:
        return self._textures[texture_name]
    
    def unlink_texture(self, texture_name: str) -> None:
        del self._textures[texture_name]
    
    def create_texture(
        self, 
        components: int = 4, 
        swizzle: str = 'BGRA', 
        size: tuple[int, int] | None = None
    ) -> mgl.Texture:
        if not size: 
            size = self.render_size
        texture: mgl.Texture = self.ctx.texture(size, components)
        texture.filter = (mgl.NEAREST, mgl.NEAREST)
        texture.repeat_x, texture.repeat_y = False, False
        texture.swizzle = swizzle
        return texture
    
    def create_texture_buffer(
        self, 
        components: int = 4
    ) -> tuple[mgl.Framebuffer, mgl.Texture]:
        buffer: mgl.Framebuffer = self.ctx.framebuffer(
            color_attachments=[self.create_texture(components, 'RGBA')]
        )
        assert isinstance(buffer.color_attachments[0], mgl.Texture)
        return buffer, buffer.color_attachments[0]
    
    def create_program(
        self, 
        vert: str = "default_vert", 
        frag: str = "default_frag"
    ) -> mgl.Program:
        return self.ctx.program(
            vertex_shader=self.registry["assets"].get_shader(vert),
            fragment_shader=self.registry["assets"].get_shader(frag)
        )
    
    def create_material(
        self, 
        vert: str = "default_vert", 
        frag: str = "default_frag"
    ) -> Material:
        program: mgl.Program = self.create_program(vert=vert, frag=frag)
        return Material(
            program, self.ctx.vertex_array(
                program, 
                [(self.screen_buffer, '2f 2f', 'vert', 'texcoord')], 
                mode=mgl.TRIANGLE_STRIP
            )
        )
    
    def world_to_tangent(self, point: tuple[float, float], layer: int) -> tuple[float, float]:
        converted_point: tuple[float, float] = self.registry['camera'].world_to_camera(layer, point)
        return (
            converted_point[0] * self.WORLD_TO_TANGENT[0], 
            converted_point[1] * self.WORLD_TO_TANGENT[1]
        )
    
    def quit(self) -> None:
        self.render_texture.release()
