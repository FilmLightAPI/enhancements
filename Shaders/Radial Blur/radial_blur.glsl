/*
 * Radial Blur
 *
 * Blurs around a centre point, simulating a zooming and/or rotating camera.
 * Each pixel is averaged along an arc/ray: every sample is the pixel's offset
 * from the centre scaled (zoom) and rotated (spin) by a small amount.
 *
 * Controls: Blur Type, Center, Radial Amount, Rotation Amount, Falloff, Edge Mode
 */

uniform sampler2D adsk_input1;
uniform float adsk_result_w;
uniform float adsk_result_h;

uniform int   blur_type;      // 0 Box, 1 Pyramid, 2 Gaussian
uniform vec2  center;         // on-screen pick: normalised 0-1 OR pixels (auto-detected)
uniform float radial_amount;  // percent; total zoom range across the blur
uniform float rotation_amount;// degrees; total rotation range across the blur
uniform float falloff;        // percent of half-diagonal over which blur ramps in
uniform int   edge_mode;      // 0 Transparent, 1 Repeat, 2 Reflect

// Compile-time loop bound (some GLSL compilers reject variable bounds).
const int   MAX_SAMPLES = 128;
const int   MIN_SAMPLES = 8;
const float DEG2RAD     = 0.01745329252;

// Weight across the blur path. u = 0 at the centre sample, 1 at either end.
float blurWeight(float u)
{
    if (blur_type == 0) return 1.0;                       // Box
    float w = 1.0 - u;
    if (blur_type == 1) return w * w * (3.0 - 2.0 * w);   // Pyramid (smoother triangle)
    return exp(-4.0 * u * u);                             // Gaussian-like
}

// Fetch with edge handling. Returns vec4(0) when transparent and outside.
vec4 fetch(vec2 uv)
{
    if (edge_mode == 0)
    {
        if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0)
            return vec4(0.0);
    }
    else if (edge_mode == 1)
    {
        uv = clamp(uv, 0.0, 1.0);                         // Repeat edge pixels
    }
    else
    {
        uv = 1.0 - abs(1.0 - mod(uv, 2.0));               // Reflect
    }
    return texture2D(adsk_input1, uv);
}

void main()
{
    vec2 res  = vec2(adsk_result_w, adsk_result_h);
    vec2 px   = gl_FragCoord.xy;
    vec2 uv0  = px / res;
    vec4 orig = texture2D(adsk_input1, uv0);

    float zoom = radial_amount   * 0.01;                  // fraction
    float spin = rotation_amount * DEG2RAD;               // radians

    // Resolve the on-screen pick to pixel coordinates (origin bottom-left).
    // normalised 0-1 and scaled by the frame size.
    vec2 c = center;
    if (max(abs(c.x), abs(c.y)) <= 2.0) c *= res;

    vec2  d    = px - c;
    float dist = length(d);

    // Falloff: blur strength ramps from 0 at the centre to full at
    // falloff% of the half-diagonal. 0 = no ramp (full strength everywhere).
    float maxDist = 0.5 * length(res);
    float mask = 1.0;
    if (falloff > 0.0)
        mask = smoothstep(0.0, falloff * 0.01 * maxDist, dist);

    // Total blur length in pixels at this pixel (zoom travel + arc length)
    float travel = dist * (abs(zoom) + abs(spin)) * mask;

    // Sample count
    float nf;
    nf = ceil(travel);      // ~1 sample per pixel
    nf = clamp(nf, float(MIN_SAMPLES), float(MAX_SAMPLES));
    int n = int(nf);

    // Nothing to blur here
    if (travel < 0.01)
    {
        gl_FragColor = orig;
        return;
    }

    vec4  acc  = vec4(0.0);
    float wsum = 0.0;

    for (int i = 0; i < MAX_SAMPLES; i++)
    {
        if (i >= n) break;

        float t = (float(i) + 0.5) / nf - 0.5;            // -0.5 .. +0.5
        float w = blurWeight(abs(t) * 2.0);

        float s  = 1.0 + zoom * t * mask;
        float a  = spin * t * mask;
        float ca = cos(a);
        float sa = sin(a);

        // Rotate/scale the offset in pixel space so rotation stays circular
        vec2 o = vec2(d.x * ca - d.y * sa,
                      d.x * sa + d.y * ca) * s;

        acc  += fetch((c + o) / res) * w;
        wsum += w;
    }

    gl_FragColor = (wsum > 0.0) ? acc / wsum : orig;
}
