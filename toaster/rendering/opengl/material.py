from dataclasses import dataclass
from moderngl import Program, VertexArray


@dataclass
class Material:
    program: Program
    surface: VertexArray
