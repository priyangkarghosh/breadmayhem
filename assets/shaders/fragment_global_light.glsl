#version 330

uniform sampler2D render_tex;

uniform vec3 tint;
uniform float intensity;
uniform float opacity;

in vec2 uv;
out vec4 f_colour;

void main() {
    vec4 tex_colour = vec4(texture(render_tex, uv));
    vec3 shaded_colour = tex_colour.rgb;
    shaded_colour *= tint * intensity;
    shaded_colour += tint * opacity;
    f_colour = vec4(shaded_colour, tex_colour.a + opacity);
}