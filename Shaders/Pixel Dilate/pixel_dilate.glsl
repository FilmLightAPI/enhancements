/*
 * Pixel Dilate=
 *
 * Single-pass, pixel-radius dilate (or erode) using a per-channel
 * max (or min) over a circular, square or diamond kernel.
 */

uniform sampler2D adsk_input1;
uniform float adsk_result_w;
uniform float adsk_result_h;

uniform float radius;        // kernel radius in pixels
uniform int   shape;         // 0 = Circle, 1 = Square, 2 = Diamond
uniform int   mode;          // 0 = Dilate, 1 = Erode
uniform int   channels;      // 0 = RGBA, 1 = RGB only, 2 = Alpha only

// Upper limit for the loops, comput costs increase by the square of this number
const int MAX_RADIUS = 64;

void main()
{
    vec2 res = vec2(adsk_result_w, adsk_result_h);
    vec2 px  = gl_FragCoord.xy;                       // pixel centre (x + 0.5)

    vec4 orig   = texture2D(adsk_input1, px / res);
    vec4 result = orig;

    float r  = clamp(radius, 0.0, float(MAX_RADIUS));
    int   ri = int(ceil(r));
    bool  dilate = (mode == 0);

    if (ri > 0)
    {
        for (int j = -MAX_RADIUS; j <= MAX_RADIUS; j++)
        {
            if (abs(j) > ri) continue;

            for (int i = -MAX_RADIUS; i <= MAX_RADIUS; i++)
            {
                if (abs(i) > ri) continue;

                vec2  o = vec2(float(i), float(j));
                float d;

                if (shape == 0)      d = length(o);                    // circle
                else if (shape == 1) d = max(abs(o.x), abs(o.y));      // square
                else                 d = abs(o.x) + abs(o.y);          // diamond

                // Smooth edges with kernel weight: 1 inside the radius, ramping to 0 one pixel outside
                float w = clamp(r + 1.0 - d, 0.0, 1.0);
                if (w <= 0.0) continue;

                // Ignore samples that fall outside the frame
                vec2 p = px + o;
                if (p.x < 0.0 || p.y < 0.0 || p.x > res.x || p.y > res.y) continue;

                vec4 s = texture2D(adsk_input1, p / res);
                vec4 c = mix(orig, s, w);

                result = dilate ? max(result, c) : min(result, c);
            }
        }
    }

    // Channel selection
    if (channels == 1)      result.a   = orig.a;    // RGB only
    else if (channels == 2) result.rgb = orig.rgb;  // Alpha only

    gl_FragColor = result;
}
