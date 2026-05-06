uniform sampler2D front;

void main(void) 
{	
    vec2 uv = gl_TexCoord[0].xy;
	vec3 val = texture2D(front, uv).rgb;

    float l = 0.2126 * val.r + 0.7152 *val.g + 0.0722 * val.b;
        
    val = vec3(0, 0, 0); // -6
    if ( l > 0.0028125 )
        val = vec3(0.44, 0.19, 0.63); // -5
    if ( l > 0.005625 )
        val = vec3(0.0, 0.44, 0.76); // -4
    if ( l > 0.01125 )
        val = vec3(0.03, 0.69, 0.94); // -3
    if ( l > 0.0225 )
        val = vec3(0.09, 0.65, 0.06); // -2
    if ( l > 0.045 )
        val = vec3(0.19, 0.87, 0.14); // -1
    if ( l > 0.09 )
        val = vec3(0.01, 1.0, 0.01); // -1/2
    if ( l > 0.125 )
        val = vec3(0.55, 0.55, 0.55); // 0
    if ( l > 0.25 )
        val = vec3(1.0, 0.97, 0.0); // +1/2
    if ( l > 0.36 )
        val = vec3(1.0, 0.97, 0.45); // +1
    if ( l > 0.72 )
        val = vec3(0.99, 0.52, 0.01); // +2
    if ( l > 1.44 )
        val = vec3(0.99, 0.60, 0.01); // +3
    if ( l > 2.88 )
        val = vec3(0.99, 0.0, 0.0); // +4
    if ( l > 5.76 )
        val = vec3(0.99, 0.28, 0.28); // +5
    if ( l > 11.52 )
        val = vec3(1.0, 1.0, 1.0); // +6
        
    gl_FragColor.rgb = val;
} 



