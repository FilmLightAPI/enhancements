#version 120

uniform float adsk_result_w, adsk_result_h;
uniform sampler2D adsk_results_pass2;

uniform vec2 Center;
uniform float Aspect;
uniform float FalloffRadius;
uniform float FalloffSoftness;

uniform float Amount;
uniform float ChromaSpread;
uniform float VignetteStrength;
uniform int Samples;

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
    float angle_total = radians(Amount) * blur_weight;
    
    // Smoothly reduce exposure up to -6 stops (1/64 factor) based on vignette strength
    float stops = blur_weight * VignetteStrength * 6.0;
    float vignette = pow(2.0, -stops);
    
    if (abs(angle_total) < 0.0001 || Samples <= 1) {
        gl_FragColor = texture2D(adsk_results_pass2, uv) * vignette;
        return;
    }
    
    vec2 p = uv - Center;
    p.x *= Aspect;
    
    vec4 color = vec4(0.0);
    float accum = 0.0;
    
    float angle_step = angle_total / float(Samples - 1);
    float start_angle = -angle_total / 2.0;
    
    // Scale chroma spread with blur_weight and ramp smoothly from 0 to 10 degrees Amount
    float amount_factor = clamp(abs(Amount) / 10.0, 0.0, 1.0);
    float effective_chroma = ChromaSpread * 0.01 * amount_factor * blur_weight;
    
    for (int i = 0; i < 100; i++) {
        if (i >= Samples) break;
        
        float a = start_angle + float(i) * angle_step;
        float c = cos(a);
        float s = sin(a);
        
        vec2 rotated_p = vec2(p.x * c - p.y * s, p.x * s + p.y * c);
        
        rotated_p.x /= Aspect;
        
        vec2 uv_r = rotated_p * (1.0 - effective_chroma) + Center;
        vec2 uv_g = rotated_p + Center;
        vec2 uv_b = rotated_p * (1.0 + effective_chroma) + Center;
        
        uv_r = clamp(uv_r, vec2(-10.0), vec2(10.0));
        uv_g = clamp(uv_g, vec2(-10.0), vec2(10.0));
        uv_b = clamp(uv_b, vec2(-10.0), vec2(10.0));
        
        color.r += texture2D(adsk_results_pass2, uv_r).r;
        color.g += texture2D(adsk_results_pass2, uv_g).g;
        color.b += texture2D(adsk_results_pass2, uv_b).b;
        color.a += texture2D(adsk_results_pass2, uv_g).a;
        accum += 1.0;
    }
    
    gl_FragColor = (color / accum) * vignette;
}
