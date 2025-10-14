#version 330

uniform sampler2D tex_a;
uniform sampler2D tex_b;

out vec4 f_colour;
in vec2 uv;

void main() {
  vec2 sample_pos = vec2(uv.x, 1 - uv.y);
  f_colour = vec4(texture(tex_a, sample_pos).rgb + texture(tex_b, sample_pos).rgb, 0.0);
}