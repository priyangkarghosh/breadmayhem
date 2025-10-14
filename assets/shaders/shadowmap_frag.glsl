#version 330

out vec4 f_colour;

void main() {
    float shadow_strength = 0.1;
    f_colour = vec4(shadow_strength, 0, 0, 1.0);
}