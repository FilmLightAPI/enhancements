uniform float adsk_result_w;
uniform float adsk_result_h;
uniform sampler2D input1;

float width = adsk_result_w;   //texture width
float height = adsk_result_h;  //texture height


uniform float fixWidth01;		//size of dead pixel area in pixels
uniform float fixHeight01;		//
uniform vec2 Position01;		//location of fix 0.0 - 1.0
uniform vec3 Colour01;			//Colour of cursor
uniform bool cross01;			//display cross?
uniform int fill01;				//fix type eg horiz, vert or both




vec4 drawCursor(float fixWidth, float fixHeight, vec2 position, vec3 colour, bool display)
{
	//vec2 gl_FragCoord is current coord of pixel 0.0-1.0
	
	vec4 result;
	float alpha,alpha2;
	
	result.rgb = colour;
	alpha = step(position.x * width - (fixWidth /2.0), gl_FragCoord.x) * step( gl_FragCoord.x, position.x * width + (fixWidth /2.0));
	alpha += step(position.y * height - (fixHeight /2.0), gl_FragCoord.y) * step( gl_FragCoord.y, position.y * height + (fixHeight /2.0));
	
	//remove centre block of cursor
	alpha2 = step(position.x * width - (fixWidth * 4.0), gl_FragCoord.x) * step( gl_FragCoord.x, position.x * width + (fixWidth * 4.0));
	alpha2 *= step(position.y * height - (fixHeight * 4.0), gl_FragCoord.y) * step( gl_FragCoord.y, position.y * height + (fixHeight * 4.0));
	
	if (display) result.a = clamp(alpha, 0.0, 1.0) * (1.0 - alpha2);
	else result.a = 0.0;
	
	return result;
}

vec4 fixPixel(float fixWidth, float fixHeight, vec2 position, int fillType)
{
	vec4 top, left, right, bottom, resultv, resulth, result; //samples for the fix
	vec2 topCoord, leftCoord, rightCoord, bottomCoord;
	
	float alpha;
	vec2 texSize = vec2(width,height);  		//size of texture in pixels
	
	
	result = vec4(1.0, 1.0, 1.0, 0.0);
	alpha = step(position.x * width - (fixWidth / 2.0), gl_FragCoord.x) * step( gl_FragCoord.x, position.x * width + (fixWidth / 2.0));
	alpha *= step(position.y * height - (fixHeight / 2.0), gl_FragCoord.y) * step( gl_FragCoord.y, position.y * height + (fixHeight / 2.0));
	
	topCoord = vec2(gl_FragCoord.x / texSize.x, position.y + ((fixHeight / 2.0) + 0.0) / texSize.y);
	bottomCoord = vec2(gl_FragCoord.x / texSize.x, position.y - ((fixHeight / 2.0) + 0.0) / texSize.y);
	leftCoord = vec2( position.x - ((fixWidth / 2.0) + 0.0) / texSize.x , gl_FragCoord.y / texSize.y);
	rightCoord = vec2( position.x + ((fixWidth / 2.0) + 0.0) / texSize.x , gl_FragCoord.y / texSize.y);
	
	top = texture2D(input1, topCoord);  
	bottom = texture2D(input1, bottomCoord );  
	left = texture2D(input1, leftCoord); 
	right = texture2D(input1, rightCoord); 
	
	resultv = mix(bottom, top, smoothstep(bottomCoord.y, topCoord.y, gl_FragCoord.y / texSize.y));
	resulth = mix(left, right, smoothstep(leftCoord.x, rightCoord.x, gl_FragCoord.x / texSize.x));
	if (fillType == 1) result = resulth;
	if (fillType == 2) result = resultv;
	if (fillType == 3) result = mix(resultv,resulth, 0.5);
	
	if (fillType > 0)
		result.a = alpha;
    	else result.a = 0.0;
	
	return result;
}




////////////////////////////////////////////////////

void main(void) {
	

	vec2 texSize = vec2(width,height);  		//size of texture in pixels

	vec2 coords = gl_FragCoord.xy / texSize;    // current coords in 0.0-1.0 
	gl_FragColor = texture2D(input1,coords); 	//if nothing happens pass through
	//vec2 fix; 									//centre coord of fix
	//fix = floor(Position01 * texSize);			//converted to 0.0-1.0

	vec4 cursor = drawCursor(fixWidth01, fixHeight01, Position01, Colour01, cross01);
	gl_FragColor = gl_FragColor * (1.0-cursor.a) + (cursor * cursor.a);  // comp on the cursor using it's alpha
	
	vec4 fix  = fixPixel(fixWidth01, fixHeight01, Position01, fill01); //generate the fix for that pixel
	gl_FragColor = gl_FragColor * (1.0-fix.a) + (fix * fix.a);  // comp on the fix using it's alpha
	

	return;
}	
