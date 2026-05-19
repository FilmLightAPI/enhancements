//WIP Andym 03-2025

uniform vec3 color1, color2, color3, color4;
uniform vec2 pos1, pos2, pos3, pos4;
uniform bool enable1, enable2, enable3, enable4;
uniform int interpolation;
uniform float centerX, centerY;
uniform int steps;

uniform float adsk_result_w;
uniform float adsk_result_h;

float smoothstep(float edge0, float edge1, float x) {
    float t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

// Cubic interpolation
float cubicInterpolate(float a, float b, float c, float d, float t) {
    float p = (d - c) - (a - b);
    float q = (a - b) - p;
    float r = c - a;
    float s = b;
    return p * t * t * t + q * t * t + r * t + s;
}

vec3 cubicInterpolateVec3(vec3 a, vec3 b, vec3 c, vec3 d, float t) {
    return vec3(
        cubicInterpolate(a.r, b.r, c.r, d.r, t),
        cubicInterpolate(a.g, b.g, c.g, d.g, t),
        cubicInterpolate(a.b, b.b, c.b, d.b, t)
    );
}

vec3 mix4(vec3 c1, vec3 c2, vec3 c3, vec3 c4, vec2 uv, vec2 p1, vec2 p2, vec2 p3, vec2 p4) {
    float d1 = enable3 ? distance(uv, p1) : 1000000.0;  // top-left
    float d2 = enable4 ? distance(uv, p2) : 1000000.0;  // top-right
    float d3 = enable1 ? distance(uv, p3) : 1000000.0;  // bottom-left
    float d4 = enable2 ? distance(uv, p4) : 1000000.0;  // bottom-right
    
    float w1 = enable3 ? 1.0 / (d1 * d1 + 0.0001) : 0.0;  // top-left
    float w2 = enable4 ? 1.0 / (d2 * d2 + 0.0001) : 0.0;  // top-right
    float w3 = enable1 ? 1.0 / (d3 * d3 + 0.0001) : 0.0;  // bottom-left
    float w4 = enable2 ? 1.0 / (d4 * d4 + 0.0001) : 0.0;  // bottom-right
    
    float sum = w1 + w2 + w3 + w4;
    if (sum < 0.0001) return vec3(0.0);
    
    return (c1 * w1 + c2 * w2 + c3 * w3 + c4 * w4) / sum;
}

// Barycentric coordinates calculation
vec3 barycentric(vec2 p, vec2 a, vec2 b, vec2 c) {
    vec2 v0 = b - a;
    vec2 v1 = c - a;
    vec2 v2 = p - a;
    
    float d00 = dot(v0, v0);
    float d01 = dot(v0, v1);
    float d11 = dot(v1, v1);
    float d20 = dot(v2, v0);
    float d21 = dot(v2, v1);
    
    float denom = d00 * d11 - d01 * d01;
    if (abs(denom) < 0.0001) return vec3(1.0, 0.0, 0.0);
    
    float v = (d11 * d20 - d01 * d21) / denom;
    float w = (d00 * d21 - d01 * d20) / denom;
    float u = 1.0 - v - w;
    
    return vec3(u, v, w);
}

// Harmonic weights calculation (inverse distance weighted with harmonic falloff)
vec4 harmonicWeights(vec2 p, vec2 p1, vec2 p2, vec2 p3, vec2 p4) {
    float d1 = distance(p, p1);
    float d2 = distance(p, p2);
    float d3 = distance(p, p3);
    float d4 = distance(p, p4);
    
    // Prevent division by zero
    d1 = max(d1, 0.0001);
    d2 = max(d2, 0.0001);
    d3 = max(d3, 0.0001);
    d4 = max(d4, 0.0001);
    
    // Harmonic weights (1/r)
    float w1 = 1.0 / d1;
    float w2 = 1.0 / d2;
    float w3 = 1.0 / d3;
    float w4 = 1.0 / d4;
    
    // Normalize weights
    float sum = w1 + w2 + w3 + w4;
    return vec4(w1, w2, w3, w4) / sum;
}

float quantize(float value, int numSteps) {
    if (numSteps <= 0) return value;
    return floor(value * float(numSteps)) / float(numSteps);
}

void main(void) {
    vec2 uv = gl_TexCoord[0].xy;
    vec3 result;
    vec2 center = vec2(centerX, centerY);
    
    if (interpolation == 0) { // Linear
        float tx = smoothstep(pos1.x, pos2.x, uv.x);
        float ty = smoothstep(pos1.y, pos3.y, uv.y);
        
        if (steps > 0) {
            tx = quantize(tx, steps);
            ty = quantize(ty, steps);
        }
        
        vec3 top = mix(
            enable3 ? color1 : vec3(0.0),
            enable4 ? color2 : vec3(0.0),
            tx
        );
        vec3 bottom = mix(
            enable1 ? color3 : vec3(0.0),
            enable2 ? color4 : vec3(0.0),
            tx
        );
        result = mix(top, bottom, ty);
    }
    else if (interpolation == 1) { // Bilinear
        if (steps > 0) {
            uv = vec2(quantize(uv.x, steps), quantize(uv.y, steps));
        }
        result = mix4(color1, color2, color3, color4, uv, pos1, pos2, pos3, pos4);
    }
    else if (interpolation == 2) { // Smooth
        vec2 st = uv;
        float smoothValue = 0.1;
        float tx = smoothstep(pos1.x - smoothValue, pos2.x + smoothValue, st.x);
        float ty = smoothstep(pos1.y - smoothValue, pos3.y + smoothValue, st.y);
        
        if (steps > 0) {
            tx = quantize(tx, steps);
            ty = quantize(ty, steps);
        }
        
        vec3 top = mix(
            enable3 ? color1 : vec3(0.0),
            enable4 ? color2 : vec3(0.0),
            tx
        );
        vec3 bottom = mix(
            enable1 ? color3 : vec3(0.0),
            enable2 ? color4 : vec3(0.0),
            tx
        );
        result = mix(top, bottom, ty);
    }
    else if (interpolation == 3) { // Radial
        float dist = distance(uv, center);
        float maxDist = distance(vec2(0.0, 0.0), vec2(1.0, 1.0));
        float t = dist / maxDist * 2.0;
        
        if (steps > 0) {
            t = quantize(t, steps);
        }
        
        // Create a radial gradient using the 4 colors
        if (t < 0.33) {
            result = mix(enable1 ? color3 : vec3(0.0), enable3 ? color1 : vec3(0.0), t * 3.0);
        } else if (t < 0.66) {
            result = mix(enable3 ? color1 : vec3(0.0), enable4 ? color2 : vec3(0.0), (t - 0.33) * 3.0);
        } else {
            result = mix(enable4 ? color2 : vec3(0.0), enable2 ? color4 : vec3(0.0), (t - 0.66) * 3.0);
        }
    }
    else if (interpolation == 4) { // Angular
        vec2 dir = uv - center;
        float angle = atan(dir.y, dir.x) / (3.14159 * 2.0) + 0.5;
        
        if (steps > 0) {
            angle = quantize(angle, steps);
        }
        
        // Create an angular gradient using the 4 colors
        if (angle < 0.25) {
            result = mix(enable1 ? color3 : vec3(0.0), enable3 ? color1 : vec3(0.0), angle * 4.0);
        } else if (angle < 0.5) {
            result = mix(enable3 ? color1 : vec3(0.0), enable4 ? color2 : vec3(0.0), (angle - 0.25) * 4.0);
        } else if (angle < 0.75) {
            result = mix(enable4 ? color2 : vec3(0.0), enable2 ? color4 : vec3(0.0), (angle - 0.5) * 4.0);
        } else {
            result = mix(enable2 ? color4 : vec3(0.0), enable1 ? color3 : vec3(0.0), (angle - 0.75) * 4.0);
        }
    }
    else if (interpolation == 5) { // Cubic
        float tx = (uv.x - pos1.x) / (pos2.x - pos1.x);
        float ty = (uv.y - pos1.y) / (pos3.y - pos1.y);
        
        if (steps > 0) {
            tx = quantize(tx, steps);
            ty = quantize(ty, steps);
        }
        
        vec3 c00 = enable3 ? color1 : vec3(0.0);  // top-left
        vec3 c10 = enable4 ? color2 : vec3(0.0);  // top-right
        vec3 c01 = enable1 ? color3 : vec3(0.0);  // bottom-left
        vec3 c11 = enable2 ? color4 : vec3(0.0);  // bottom-right
        
        // Extra control points for cubic interpolation
        vec3 c_1_1 = c00 - (c10 - c00) * 0.5;
        vec3 c21 = c11 + (c11 - c01) * 0.5;
        vec3 c0_1 = c00 - (c01 - c00) * 0.5;
        vec3 c12 = c11 + (c11 - c10) * 0.5;
        
        vec3 a = cubicInterpolateVec3(c_1_1, c00, c10, c21, tx);
        vec3 b = cubicInterpolateVec3(c0_1, c01, c11, c12, tx);
        
        result = mix(a, b, smoothstep(0.0, 1.0, ty));
    }
    else if (interpolation == 6) { // Barycentric
        // Split quad into two triangles and interpolate
        vec3 bary1, bary2;
        bool useFirstTriangle;
        
        // First triangle (p1, p2, p3)
        bary1 = barycentric(uv, pos1, pos2, pos3);
        // Second triangle (p2, p3, p4)
        bary2 = barycentric(uv, pos2, pos3, pos4);
        
        // Determine which triangle contains the point
        useFirstTriangle = (bary1.x >= 0.0 && bary1.y >= 0.0 && bary1.z >= 0.0);
        
        if (useFirstTriangle) {
            result = (enable3 ? bary1.x * color1 : vec3(0.0)) +
                    (enable4 ? bary1.y * color2 : vec3(0.0)) +
                    (enable1 ? bary1.z * color3 : vec3(0.0));
        } else {
            result = (enable4 ? bary2.x * color2 : vec3(0.0)) +
                    (enable1 ? bary2.y * color3 : vec3(0.0)) +
                    (enable2 ? bary2.z * color4 : vec3(0.0));
        }
        
        // Normalize if any colors are enabled
        float sum = (useFirstTriangle ? 
            float(enable3) * bary1.x + float(enable4) * bary1.y + float(enable1) * bary1.z :
            float(enable4) * bary2.x + float(enable1) * bary2.y + float(enable2) * bary2.z);
            
        if (sum > 0.0) {
            result /= sum;
        }
    }
    else if (interpolation == 7) { // Harmonic
        vec4 weights = harmonicWeights(uv, pos1, pos2, pos3, pos4);
        
        // Apply enabled state to weights
        weights *= vec4(float(enable3), float(enable4), float(enable1), float(enable2));
        
        // Normalize weights
        float weightSum = weights.x + weights.y + weights.z + weights.w;
        if (weightSum > 0.0) {
            weights /= weightSum;
        }
        
        // Blend colors using harmonic weights
        result = weights.x * color1 +  // top-left
                weights.y * color2 +  // top-right
                weights.z * color3 +  // bottom-left
                weights.w * color4;   // bottom-right
    }
    
    gl_FragColor = vec4(result, 1.0);
}
