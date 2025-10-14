#version 330

uniform sampler2D tex;
uniform bool flip;

out vec4 f_colour;
in vec2 uv;

void main() {
    vec2 sample_pos = vec2(uv.x, (flip) ? 1 - uv.y : uv.y);
    f_colour = vec4(texture(tex, sample_pos).rgba);
}