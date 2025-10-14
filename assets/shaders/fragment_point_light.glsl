#version 330 core

uniform sampler2D render_tex;
uniform sampler2D normal_tex;
uniform sampler2D shadow_map;

uniform vec2 light_position;
uniform vec2 light_direction;
uniform float angle_range;

uniform float radius;
uniform float power;

uniform vec3 tint;
uniform float intensity;
uniform float opacity;

in vec2 uv;
out vec4 f_colour;

void main() {
    vec2 direction = uv - light_position;
    float distance = length(direction);

    // get the colour of the render tex
    vec4 tex_colour = texture(render_tex, uv);

    // normalize the direction
    direction /= distance;
    float angle = dot(direction, normalize(light_direction));

    // calculate the radial falloff (attenuation
    float radial_falloff = clamp(1.0 - distance / radius, 0, 1);
    radial_falloff = pow(radial_falloff, power);

    // calculate the angular falloff
    float difference = 1 - angle_range;
    float angular_falloff = clamp((angle - difference) / angle_range, 0.0, 1.0);
    angular_falloff = pow(angular_falloff, power);

    vec3 norm_colour = vec3(texture(normal_tex, uv).rgb);
    vec2 norm_vector = normalize(norm_colour.xy * 2.0 - 1.0);
    float strength = clamp(dot(-direction, norm_vector), 0.0, 1.0);
    strength = mix(1.0, strength, norm_colour.b);

    float shadowmap = texture(shadow_map, uv).r;
    float shadow_strength = clamp(shadowmap / 0.4, 0.0, 1.0);

    vec4 shaded_colour = vec4(0);
    vec3 light_colour = tint / 255 * strength * intensity;

    if (tex_colour.a > 0) {
        shaded_colour.rgb = light_colour * tex_colour.rgb * radial_falloff * angular_falloff;
        shaded_colour.a = 1.0;
    }
    else {
        shaded_colour.rgb = tex_colour.rgb;
        shaded_colour.a = radial_falloff * angular_falloff * opacity;
    }

    shaded_colour.rgb += light_colour * radial_falloff * angular_falloff * opacity;
    f_colour = mix(shaded_colour, vec4(0.0, 0.0, 0.0, shaded_colour.a * shadow_strength), shadow_strength);
}