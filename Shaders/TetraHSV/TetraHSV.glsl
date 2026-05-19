// Tetrahedral color transformation in CIE XYZ inspired by Steve Yedlin
// http://www.yedlin.net/DisplayPrepDemo/DispPrepDemoFollowup.html (at 14:30)
// based on an implementation by calvinsilly with HSV controls by hotgluebanjo
// https://github.com/calvinsilly/Tetrahedral-Interpolation
// https://github.com/hotgluebanjo/TetraInterp-DCTL

uniform sampler2D front;

uniform float P_black,P_white;
uniform vec3 P_red,P_green,P_blue,P_cyan,P_magenta,P_yellow;


void main(void)
{
    vec2 uv = gl_TexCoord[0].xy;
    vec3 val = texture2D(front, uv).rgb;

    float r = val.r;
    float g = val.g;
    float b = val.b;

    float r_Hue = P_red.x;
    float r_Sat = P_red.y;
    float r_Val = P_red.z;
    float g_Hue = P_green.x;
    float g_Sat = P_green.y;
    float g_Val = P_green.z;
    float b_Hue = P_blue.x;
    float b_Sat = P_blue.y;
    float b_Val = P_blue.z;
    float c_Hue = P_cyan.x;
    float c_Sat = P_cyan.y;
    float c_Val = P_cyan.z;
    float m_Hue = P_magenta.x;
    float m_Sat = P_magenta.y;
    float m_Val = P_magenta.z;
    float y_Hue = P_yellow.x;
    float y_Sat = P_yellow.y;
    float y_Val = P_yellow.z;


    vec3 blk = vec3(P_black, P_black, P_black);
    vec3 wht = vec3(P_white, P_white, P_white);
    vec3 red = vec3(r_Val + 1.0, r_Val - r_Sat, r_Val + r_Hue - r_Sat);
    vec3 grn = vec3(g_Val - g_Sat, g_Val + 1.0, g_Val + g_Hue - g_Sat);
    vec3 blu = vec3(b_Val + b_Hue - b_Sat, b_Val - b_Sat, b_Val + 1.0);
    vec3 cyn = vec3(c_Val - c_Sat, c_Val + 1.0 + c_Hue, c_Val + 1.0);
    vec3 mag = vec3(m_Val + 1.0, m_Val - m_Sat, m_Val + 1.0 + m_Hue);
    vec3 yel = vec3(y_Val + 1.0 + y_Hue, y_Val + 1.0, y_Val - y_Sat);

    if (r > g) {
        // r > g > b
        if (g > b) {
            val = r * (red - blk) + blk + g * (yel - red) + b * (wht - yel);
        }
        // r > b > g
        else if (r > b) {
            val = r * (red - blk) + blk + g * (wht - mag) + b * (mag - red);
        }
        // b > r > g
        else {
            val = r * (mag - blu) + g * (wht - mag) + b * (blu - blk) + blk;
        }
    } else {
        // b > g > r
        if (b > g) {
            val = r * (wht - cyn) + g * (cyn - blu) + b * (blu - blk) + blk;
        }
        // g > b > r
        else if (b > r) {
            val = r * (wht - cyn) + g * (grn - blk) + blk + b * (cyn - grn);
        }
        // g > r > b
        else {
            val = r * (yel - grn) + g * (grn - blk) + blk + b * (wht - yel);
        }
    }

    gl_FragColor.rgb = val.rgb;

}
