//Copyright (c) 2020-2021 BNPR, Miguel Pozo and contributors. MIT license.

#include "Common.glsl"

#ifdef VERTEX_SHADER
void main()
{
    POSITION = in_position;
    UV[0] = in_position.xy * 0.5 + 0.5;
    
    VERTEX_SETUP_OUTPUT();

    gl_Position = vec4(POSITION, 1);
}
#endif

#ifdef PIXEL_SHADER

uniform sampler2D blend_texture;

layout (location = 0) out vec4 OUT_COLOR;

void main()
{
    PIXEL_SETUP_INPUT();

    vec4 color = texture(blend_texture, UV[0]);
    color.rgb *= color.a;
    OUT_COLOR = color;
}

#endif //PIXEL_SHADER
