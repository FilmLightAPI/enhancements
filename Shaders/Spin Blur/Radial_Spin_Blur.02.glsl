#version 120

uniform float adsk_result_w, adsk_result_h;
uniform sampler2D adsk_results_pass1;

uniform vec2 Center;
uniform float Aspect;
uniform float FalloffRadius;
uniform float FalloffSoftness;
uniform float PreBlur;
uniform float Amount;

float get_blur_weight(vec2 uv) {
    vec2 p = uv - Center;
    p.x *= Aspect;
    float dist = length(p);
    float min_r = max(0.0, FalloffRadius - FalloffSoftness);
    float max_r = FalloffRadius + FalloffSoftness;
    return smoothstep(min_r, max_r, dist);
}

void main() {
    vec2 res = vec2(adsk_result_w, adsk_result_h);
    vec2 uv = gl_FragCoord.xy / res;
    
    float blur_weight = get_blur_weight(uv);
    float base_blur = abs(Amount) * 0.25; // 60 deg -> 15px blur, 10 deg -> 2.5px blur
    float blur_amount = base_blur * PreBlur * blur_weight;
    
    if (blur_amount < 0.1) {
        gl_FragColor = texture2D(adsk_results_pass1, uv);
        return;
    }
    
    vec4 color = vec4(0.0);
    float accum = 0.0;
    
    int limit = int(ceil(blur_amount));
    if (limit > 50) limit = 50;
    
    for (int i = -50; i <= 50; i++) {
        if (i > limit) break;
        if (i < -limit) continue;
        
        vec2 offset = vec2(0.0, float(i) / res.y);
        vec2 sample_uv = clamp(uv + offset, vec2(-10.0), vec2(10.0));
        float weight = 1.0 - (abs(float(i)) / (float(limit) + 1.0));
        color += texture2D(adsk_results_pass1, sample_uv) * weight;
        accum += weight;
    }
    
    gl_FragColor = color / accum;
}
