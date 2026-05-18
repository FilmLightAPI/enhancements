uniform sampler2D front;

// Image dimensions
uniform float adsk_result_w;
uniform float adsk_result_h;

uniform int edgeDetectionMethod; // 0 = None, 1 = Sobel, 2 = Prewitt, 3 = Roberts
uniform int mode; //0 = RGB, 1 = BW, 2 = Alpha
uniform float sensitivity; // Edge intensity multiplier
uniform int radius; // Sampling radius


int clampInt(int value, int minVal, int maxVal) {
    if (value < minVal) {
        return minVal;
    } else if (value > maxVal) {
        return maxVal;
    } else {
        return value;
    }
}


// Sobel kernels
const mat3 sobelX = mat3(
    -1, 0, 1,
    -2, 0, 2,
    -1, 0, 1
);

const mat3 sobelY = mat3(
    -1, -2, -1,
     0,  0,  0,
     1,  2,  1
);

// Prewitt kernels
const mat3 prewittX = mat3(
    -1, 0, 1,
    -1, 0, 1,
    -1, 0, 1
);

const mat3 prewittY = mat3(
    -1, -1, -1,
     0,  0,  0,
     1,  1,  1
);

// Roberts kernels
const mat3 robertsX = mat3(
     0,  0,  0,
     0, -1,  0,
     0,  0,  1
);

const mat3 robertsY = mat3(
     0,  0,  0,
     0,  0, -1,
     0,  1,  0
);

vec3 applyKernel(mat3 kernel, vec2 texCoords, vec2 texelSize, int radius) {
    vec3 result = vec3(0.0);
    for (int i = -radius; i <= radius; i++) {
        for (int j = -radius; j <= radius; j++) {
            vec2 offset = vec2(float(i), float(j)) * texelSize;
            vec3 sample = texture2D(front, texCoords + offset).rgb;
            
            // Ensure kernel indexing stays within bounds (clamped to 3x3 max)
            int ki = clampInt(i + 1, 0, 2);
            int kj = clampInt(j + 1, 0, 2);
            result += sample * kernel[ki][kj];
        }
    }
    return result;
}

vec3 robertsEdgeDetection(vec2 texCoords, vec2 texelSize) {
    vec3 robertsXResult = applyKernel(robertsX, texCoords, texelSize, 1);
    vec3 robertsYResult = applyKernel(robertsY, texCoords, texelSize, 1);
    return sqrt(robertsXResult * robertsXResult + robertsYResult * robertsYResult) * sensitivity;
}

void main(void) {
    vec2 uv = gl_TexCoord[0].xy;
    vec2 texelSize = vec2(1.0 / adsk_result_w, 1.0 / adsk_result_h);
    vec4 val = texture2D(front, uv);
    vec3 edgeColor = vec3(0.0);

    if (edgeDetectionMethod == 1) { // Sobel
        vec3 sobelXResult = applyKernel(sobelX, uv, texelSize, radius);
        vec3 sobelYResult = applyKernel(sobelY, uv, texelSize, radius);
        edgeColor = sqrt(sobelXResult * sobelXResult + sobelYResult * sobelYResult) * sensitivity;
    } else if (edgeDetectionMethod == 2) { // Prewitt
        vec3 prewittXResult = applyKernel(prewittX, uv, texelSize, radius);
        vec3 prewittYResult = applyKernel(prewittY, uv, texelSize, radius);
        edgeColor = sqrt(prewittXResult * prewittXResult + prewittYResult * prewittYResult) * sensitivity;
    } else if (edgeDetectionMethod == 3) { // Roberts
        edgeColor = robertsEdgeDetection(uv, texelSize);
    } else if (edgeDetectionMethod == 0) { // None
        edgeColor = val.rgb;
    }
    if (mode==0) { // RGB output
        val.rgb = edgeColor;
    } else if (mode==1) { //BW Output
        float bw = length(edgeColor);
        val.rgb = vec3(bw);
    } else if (mode==2) { //Alpha Output
        float bw = length(edgeColor);
        val.a = bw;
    }

    gl_FragColor = val;
}
