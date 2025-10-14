#version 330

uniform sampler2D tex;
uniform vec2 resolution;

out vec4 f_colour;
in vec2 uv;

void main() {
    vec2 sample_uv = vec2(uv.x, 1 - uv.y);
    vec2 texelSize = 1.0 / resolution;
    int blur_amount = 4;

    f_colour = vec4(0);
    for(int x = -blur_amount; x <= blur_amount; ++x)
        for(int y = -blur_amount; y <= blur_amount; ++y)
            f_colour += texture(tex, sample_uv + vec2(x, y) * texelSize);
    f_colour /= pow(blur_amount * 2 + 1, 2);
}