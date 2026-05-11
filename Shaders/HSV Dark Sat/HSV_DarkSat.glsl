uniform sampler2D source;

uniform float gain, gamma;

vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}


void main(void) 
{	
    vec2 uv = gl_TexCoord[0].xy;
    vec3 val = texture2D(source, uv).rgb;

    val = rgb2hsv(val);
    
    val.g = (gamma <= 0.0) ? pow(val.g * (gain + 1.0), (1.0 - gamma)) : pow(val.g * (gain + 1.0), 1.0 / (gamma + 1.0));
    
    val = hsv2rgb(val);
    
    gl_FragColor = vec4(val, texture2D(source, uv).a);
} 



