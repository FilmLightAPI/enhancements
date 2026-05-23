uniform sampler2D front;

uniform float limU,limL;
uniform bool clamping;
uniform bool preview;
uniform vec3 tint_up,tint_low;

void main(void)
{
    vec2 uv = gl_TexCoord[0].xy;
    vec3 val = texture2D(front, uv).rgb;

    if (preview == true)
    {
        if (val.r > limU) val.rgb = tint_up;
        if (val.g > limU) val.rgb = tint_up;
        if (val.b > limU) val.rgb = tint_up;

        if (val.r < limL) val.rgb = tint_low;
        if (val.g < limL) val.rgb = tint_low;
        if (val.b < limL) val.rgb = tint_low;
    }

    if (clamping == true)
    {
        val.rgb = clamp(val.rgb, limL, limU);
    }

    gl_FragColor.rgb = val.rgb;

}
