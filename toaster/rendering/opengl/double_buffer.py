from typing import TYPE_CHECKING
if TYPE_CHECKING: from toaster.rendering.renderer import Renderer

import moderngl as mgl

class _BufferAccessor:
    def __init__(self, parent: 'DoubleTextureBuffer', is_current: bool):
        self._parent = parent
        self._is_current = is_current
    
    @property
    def buf(self) -> mgl.Framebuffer:
        if self._is_current: return self._parent._buf1 if self._parent._flipped else self._parent._buf2
        else: return self._parent._buf2 if self._parent._flipped else self._parent._buf1
    
    @property
    def tex(self) -> mgl.Texture:
        if self._is_current: return self._parent._tex1 if self._parent._flipped else self._parent._tex2 # type: ignore
        else: return self._parent._tex2 if self._parent._flipped else self._parent._tex1 # type: ignore

class DoubleTextureBuffer:
    def __init__(self, buf1: mgl.Framebuffer, buf2: mgl.Framebuffer):
        self._flipped = False
        self._buf1, self._buf2 = buf1, buf2
        self._validate_buffers()
        self._tex1, self._tex2 = buf1.color_attachments[0], buf2.color_attachments[0]
        
        # Create accessor objects
        self._current = _BufferAccessor(self, is_current=True)
        self._next = _BufferAccessor(self, is_current=False)
    
    def _validate_buffers(self):
        if not self._buf1.color_attachments or not self._buf2.color_attachments:
            raise ValueError("Both framebuffers must have at least one color attachment")
        
        tex1 = self._buf1.color_attachments[0]
        tex2 = self._buf2.color_attachments[0]
        if not isinstance(tex1, mgl.Texture) or not isinstance(tex2, mgl.Texture):
            raise TypeError("Color attachments must be textures")
        
        if tex1.size != tex2.size:
            raise ValueError(f"Texture sizes must match: {tex1.size} != {tex2.size}")
    
    @property
    def current(self) -> _BufferAccessor:
        return self._current
    
    @property
    def next(self) -> _BufferAccessor:
        return self._next
    
    @property
    def size(self) -> tuple[int, int]:
        return self.current.tex.size
    
    def flip(self):
        self._flipped = not self._flipped
    
    def clear(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 0.0):
        self._buf1.clear(r, g, b, a)
        self._buf2.clear(r, g, b, a)
    
    def release(self):
        self._buf1.release()
        self._buf2.release()
    
    @classmethod
    def create(
        cls, 
        renderer: 'Renderer', 
        size: tuple[int, int] | None = None,
        components: int = 4, 
        swizzle: str = 'BGRA', 
        filter: tuple[int, int] = (mgl.NEAREST, mgl.NEAREST),
        repeat: tuple[bool, bool] = (False, False)
    ) -> 'DoubleTextureBuffer':
        tex1 = renderer.create_texture(size, components, swizzle, filter, repeat)
        tex2 = renderer.create_texture(size, components, swizzle, filter, repeat)
        buf1 = renderer.ctx.framebuffer(color_attachments=[tex1])
        buf2 = renderer.ctx.framebuffer(color_attachments=[tex2])
        return cls(buf1, buf2)
