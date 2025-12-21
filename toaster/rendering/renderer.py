import pygame
import moderngl as mgl
from array import array
from typing import Literal, TypedDict

from toaster.rendering.camera import Camera
from toaster.rendering.lighting import Lighting
from toaster.registry.registry_item import RegistryItem
from tlang import ShaderManager

SHADERS_PATH = "assets/shaders"
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
    texture: mgl.Texture
    buffer: mgl.Framebuffer
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
        self.camera: Camera = self.registry['camera']
        
        # set the render size and calculate the overall window size
        self.render_size = render_size
        self.aggregate_size = \
            (render_size[0] * self.camera.num_layers + self.camera.num_layers,
             render_size[1] + 1)  # layers are all stored horizontally
        
        # set the window size and reset colour
        self.window_size = self.registry['window'].size
        self.clear_colour = clear_colour
        
        # calculate the conversion ratios
        self.PIXEL_TO_TANGENT = 2 / max(self.render_size)
        self.WORLD_TO_TANGENT = (1 / self.render_size[0],
                                 1 / self.render_size[1])
        
        # create the context
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.BLEND)

        # create the shader manager
        self.shaders = ShaderManager(self.ctx, '330 core', SHADERS_PATH, {})
        
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

        # create the lighting renderer
        self.lighting = Lighting(self)
        
        # create the default material for rendering a surf to a texture
        self.default = self.create_screen_vao(self.shaders.get_shader('default').get_program('default')) # type: ignore

        # texture types we support
        self.texture_types = ['albedo', 'occlusion', 'emissive', 'unlit']
        
        # create the layers
        self.layers = []
        for i in range(self.camera.num_layers):
            tex = self.create_texture(components=4, swizzle='RGBA')
            buf = self.ctx.framebuffer(color_attachments=[tex])

            layer_dict: LayerDict = {
                "index": i,
                "tex_name": "layer_" + str(i),

                "albedo_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),
                "occlusion_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),
                "emissive_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),
                "unlit_surf": pygame.Surface(self.render_size, pygame.SRCALPHA),

                "texture": tex,
                "buffer": buf,
                "dirty": {
                    "albedo": False,
                    "occlusion": False,
                    "emissive": False,
                    "unlit": False
                }
            }
            self.layers.append(layer_dict)
        
        # list to hold render objects
        self.render_objects = []
    
    def mark_dirty(self, layer_index: int, texture_type: TextureType) -> None:
        if 0 <= layer_index < len(self.layers):
            if texture_type in self.texture_types:
                self.layers[layer_index]['dirty'][texture_type] = True
    
    def render(self) -> None:
        self.ctx.screen.clear()
        
        # ::: RENDER INDIVIDUAL LAYERS
        for layer in reversed(self.layers):
            # only process layer if something is dirty
            if not any(layer['dirty'].values()):
                self.ctx.screen.use()
                layer['texture'].use(0)
                self.default.program['tex'] = 0
                self.default.program['flip'] = True
                self.default.render()
                continue
            
            # use the layers frame buffer
            layer['buffer'].clear()
            layer['buffer'].use()
            
            # process lit texture
            if layer['dirty']['albedo'] or layer['dirty']['occlusion'] or layer['dirty']['emissive']:
                self.lighting.render(layer['albedo_surf'], layer['occlusion_surf'], layer['emissive_surf'])
                layer['occlusion_surf'].fill(self.clear_colour)
                layer['dirty']['albedo'] = layer['dirty']['occlusion'] = layer['dirty']['emissive'] = False
            
            # process unlit texture
            if layer['dirty']['unlit']:
                # write the unlit surface to the render_texture
                layer['buffer'].use()
                self.render_texture.write(layer['unlit_surf'].get_view('1'))
                self.render_texture.use(0)
                
                # set the texture of the program
                self.default.program['tex'] = 0
                
                # disable flipping
                self.default.program['flip'] = False
                self.default.render()
                
                # clear the surface
                layer['unlit_surf'].fill(self.clear_colour)
                
                # mark as clean
                layer['dirty']['unlit'] = False
            
            # ::: RENDER TO SCREEN
            self.ctx.screen.use()
            layer['texture'].use(0)
            self.default.program['tex'] = 0
            self.default.program['flip'] = True
            self.default.render()
            
            # self.lighting.dist_buf.color_attachments[0].use(0)
            self.lighting.jump_dbuf.current.tex.use(0)
            self.default.program['tex'] = 0
            self.default.program['flip'] = True
            self.default.render()
    
    def create_screen_vao(
        self, program: mgl.Program
    ) -> mgl.VertexArray:
        return self.ctx.vertex_array(
            program, [(self.screen_buffer, '2f 2f', 'vert', 'texCoord')], 
            mode=mgl.TRIANGLE_STRIP
        ) 

    def create_texture(
        self, 
        size: tuple[int, int] | None = None,
        components: int = 4, 
        swizzle: str = 'BGRA', 
        filter: tuple[int, int] = (mgl.NEAREST, mgl.NEAREST),
        repeat: tuple[bool, bool] = (False, False)
    ) -> mgl.Texture:
        if not size: size = self.render_size
        texture: mgl.Texture = self.ctx.texture(size, components)
        texture.filter = filter
        texture.repeat_x, texture.repeat_y = repeat
        texture.swizzle = swizzle
        return texture
    
    def world_to_tangent(self, point: tuple[float, float], layer: int) -> tuple[float, float]:
        converted_point: tuple[float, float] = self.registry['camera'].world_to_camera(layer, point)
        return (
            converted_point[0] * self.WORLD_TO_TANGENT[0], 
            converted_point[1] * self.WORLD_TO_TANGENT[1]
        )
    
    def quit(self) -> None:
        self.render_texture.release()
