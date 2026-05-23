uniform sampler2D front;

uniform float p_Hue, p_Sat, p_Val, p_Cr, p_Cb,p_Mix, p_Smoothness;
uniform bool t_Hue, t_Sat, t_Val, t_Cr, t_Cb;
uniform int p_Method;
float pi = 3.14159265359;

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

vec3 RGBtoYCC(vec3 rgb) {
  float Y = 0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b;
  float Cb = -0.168736 * rgb.r - 0.331264 * rgb.g + 0.5 * rgb.b;
  float Cr = 0.5 * rgb.r - 0.418688 * rgb.g - 0.081312 * rgb.b;
  return vec3(Y, Cb, Cr);
}

vec3 YCCtoRGB(vec3 ycc) {
    float R = ycc.x + 1.402 * ycc.z;
    float G = ycc.x - 0.344136 * ycc.y - 0.714136 * ycc.z;
    float B = ycc.x + 1.772 * ycc.y;
    return vec3(R, G, B);
}


//Smooth2 functions
float t(float l, float value) {
    float arg = (1.0 - l) * sin(2.0 * pi * value);
    return 1.0 - 2.0 * acos(arg) / pi;
}

float s(float l, float value) {
    float arg = sin(2.0 * pi * value) / l;
    return 2.0 * atan(arg) / pi;
}

float w(float l, float value) {
    float tx = t(l, (2.0 * value - 1.0) / 4.0);
    float sx = s(l, value / 2.0);
    return (1.0 + tx * sx) / 2.0;
}

float Smooth2(float val, float l) {
    return val - w(l, val + 0.5) + 0.5;
}



float Quantize(float channel, float steps) {
    channel = channel * steps;
    if (p_Method == 0) {channel = floor(channel+0.5);}
    if (p_Method == 1) {channel = channel - (sin(2.0*pi*channel)/(2.0*pi));}
    if (p_Method == 3) {channel = Smooth2(channel, p_Smoothness);}

    channel = channel / steps;
    return channel;
}




void main(void)
{
    vec2 uv = gl_TexCoord[0].xy;
    vec3 val = texture2D(front, uv).rgb;
    vec3 source = val;

    val = RGB_to_HSV(val);

    if (t_Hue) { val.x = Quantize(val.x,p_Hue); }
    if (t_Sat) { val.y = Quantize(val.y,p_Sat); }
    if (t_Val) { val.z = Quantize(val.z,p_Val); }

    val = HSV_to_RGB(val);
    val = RGBtoYCC(val);

    if (t_Cr) { val.y = Quantize(val.y,p_Cr); }
    if (t_Cb) { val.z = Quantize(val.z,p_Cb); }

    val = YCCtoRGB(val);
    val = mix(val,source,p_Mix);

    gl_FragColor.rgb = val;
}
