uniform sampler2D source;
uniform float adsk_result_w, adsk_result_h, nits;

void main()
{
	vec2 resolution = vec2(adsk_result_w, adsk_result_h);
	vec2 uv = gl_FragCoord.xy / resolution.x;
	float aspect = resolution.x / resolution.y;
        float c = pow((0.8359375 + 18.8515625*pow(nits / 10000.0, 0.1593017578125)) / (1.0 + 18.6875*pow(nits / 10000.0, 0.1593017578125)), 78.84375);    

	vec3 col = texture2D(source, vec2(uv.x, uv.y * aspect)).rgb;
        if (col.r > c) col.r = c;
        if (col.g > c) col.g = c;
        if (col.b > c) col.b = c;
	gl_FragColor = vec4(col, texture2D(source, vec2(uv.x, uv.y * aspect)).a);
}