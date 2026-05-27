//based on Film_Density_OFX by baldavenger. GNU GENERAL PUBLIC LICENSE

uniform sampler2D front;

uniform float p_Den, p_WR, p_WG, p_WB, p_LimitS, p_LimitL, SatGamma, satGain;

vec3 RGB_to_HSV(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);

}


vec3 HSV_to_RGB(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}


vec3 Saturation(vec3 RGB, float luma, float Sat) {
    RGB.x = (1.0 - Sat) * luma + RGB.x * Sat;
    RGB.y = (1.0 - Sat) * luma + RGB.y * Sat;
    RGB.z = (1.0 - Sat) * luma + RGB.z * Sat;
    return RGB;
}


float get_luma(vec3 RGB, float Rw, float Gw, float Bw) {
    float R, G, B;
    R = Rw + 1.0 - (Gw / 2.0) - (Bw / 2.0);
    G = Gw + 1.0 - (Rw / 2.0) - (Bw / 2.0);
    B = Bw + 1.0 - (Rw / 2.0) - (Gw / 2.0);
    float luma = (RGB.x * R + RGB.y * G + RGB.z * B) / 3.0;
return luma;
}


float Limiter(float val, float limiter) {
    float alpha = limiter > 1.0 ? val + (1.0 - limiter) * (1.0 - val) : limiter >= 0.0 ? (val >= limiter ? 1.0 : val / limiter) : limiter < -1.0 ? (1.0 - val) + (limiter + 1.0) * val : val <= (1.0 + limiter) ? 1.0 : (1.0 - val) / (1.0 - (limiter + 1.0));
    alpha = clamp(alpha, 0.0, 1.0);
    return alpha;
}


float RGB_to_Sat(vec3 RGB) {
    float min = min(min(RGB.x, RGB.y), RGB.z);
    float max = max(max(RGB.x, RGB.y), RGB.z);
    float delta = max - min;
    float Sat = max != 0.0 ? delta / max : 0.0;
    return Sat;
}



void main(void)
{
    vec2 uv = gl_TexCoord[0].xy;
    vec3 val = texture2D(front, uv).rgb;

    float WR = 2.0 - p_WR;
    float WG = 2.0 - p_WG;
    float WB = 2.0 - p_WB;
    float luma = get_luma(val, WR, WG, WB);
    float SatA = 1.0 / (p_Den + 1.0);
    vec3 rgbOut = Saturation(val, luma, SatA);

    float alphaS, alphaL, alpha;
    alphaS = alphaL = alpha = 1.0;

    if (p_LimitS > 0.0) {
        float sat = RGB_to_Sat(val);
        alphaS = Limiter(sat, p_LimitS);
        alpha = alphaS;
    }
    if (p_LimitL > 0.0) {
        alphaL = (val.r + val.g + val.b) / 3.0;
        alphaL = Limiter(alphaL, p_LimitL);
        alpha *= alphaL;
    }

    vec3 temp = RGB_to_HSV(rgbOut);
    float SatRange = (0.7-1.0)*SatGamma+1.0; // Range Sat slider
    temp.g = pow(temp.g, SatRange);
    temp.g = temp.g * satGain;
    temp.g *= 1.0 / SatA ;
    temp = HSV_to_RGB(temp);
    if (rgbOut.r < 0.0) temp.r = rgbOut.r; //restore negative values in a hacky way
    if (rgbOut.g < 0.0) temp.g = rgbOut.g;
    if (rgbOut.b < 0.0) temp.b = rgbOut.b;
    rgbOut = temp;

    if (alpha < 1.0) {
        rgbOut = rgbOut * alpha + (1.0 - alpha) * val;
    }

    gl_FragColor.rgb = rgbOut;
}
