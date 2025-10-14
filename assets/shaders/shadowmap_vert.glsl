#version 330 core

uniform vec2 light_position;
uniform vec2 resolution;
uniform int mode;

in vec2 in_position;
in vec4 in_normal;

void main() {
    vec2 vertex_clip = (in_position / resolution - 0.5) * 2;
    vec2 light_clip = (light_position / resolution - 0.5) * 2;

    vec2 light_dir = normalize(vertex_clip - light_clip);
    if (mode == 0 && (dot(light_dir, in_normal.xy) > 0 && dot(light_dir, in_normal.zw) > 0))
        gl_Position = vec4(vertex_clip + light_dir * 2, 0, 1);
    else
        gl_Position = vec4(vertex_clip, 0, 1);
}