class DoubleBuffer:
    def __init__(self, renderer, components=4):
        self._flipped = False
        self._buffer_a, self._buffer_a_tex = renderer.create_texture_buffer(components)
        self._buffer_b, self._buffer_b_tex = renderer.create_texture_buffer(components)
        self.buffer = self._buffer_a

    def get_texture(self, other=True):
        if other: return self._buffer_a_tex if self._flipped else self._buffer_b_tex
        return self.buffer.color_attachments[0]

    def flip(self):
        self.buffer = self._buffer_a if self._flipped else self._buffer_b
        self._flipped = not self._flipped

    def clear(self):
        self._buffer_a.clear()
        self._buffer_b.clear()
        if self._flipped: self.flip()
