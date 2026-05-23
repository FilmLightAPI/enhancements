// Tetrahedral color transformation inspired by Steve Yedlin
// http://www.yedlin.net/DisplayPrepDemo/DispPrepDemoFollowup.html (at 14:30)
// based on an implementation by Juanjo L. Salazar 2020
// https://www.juanjosalazar.com/color-science

uniform sampler2D front;

uniform vec3 red,green,blue,cyan,magenta,yellow;
uniform float black,white;


void main(void)
{
    vec2 uv = gl_TexCoord[0].xy;
    vec3 val = texture2D(front, uv).rgb;

//  vec3 white = vec3(1.0,1.0,1.0);
    vec3 temp = val;

     
    if (val.r>val.g) {
         //r>g>b
        if (val.g>val.b){
            temp = val.r*(red-black) + black + val.g*(yellow-red) + val.b*(white-yellow);
        }
        //r>b>g
        else if (val.r>val.b){
            temp = val.r*(red-black) + black + val.g*(white-magenta) + val.b*(magenta-red);
        }
        //b>r>g
        else{
            temp = val.r*(magenta-blue) + val.g*(white-magenta) + val.b*(blue-black) + black;
        }
    } else {
        //b>g>r
        if (val.b>val.g){
            temp = val.r*(white-cyan) + val.g*(cyan-blue) + val.b*(blue-black) + black;
        }
        //g>b>r
        else if (val.b>val.r){
            temp = val.r*(white-cyan) + val.g*(green-black) + black + val.b*(cyan-green);
        }
        //g>r>b
        else{
            temp = val.r*(yellow-green) + val.g*(green-black) + black + val.b*(white-yellow);
        }
     }

     gl_FragColor.rgb = temp.rgb;

}
