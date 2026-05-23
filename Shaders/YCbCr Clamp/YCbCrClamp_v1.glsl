uniform sampler2D front;
uniform int model_type;  // 0: Y only - YCbCr, 1: RGB
uniform int matrix_type; // 0: BT.709, 1: BT.2020
uniform int clamp_low_10bit;
uniform int clamp_high_10bit;
uniform bool enable_clamp;
uniform bool enable_preview;

void main(void)
{
    vec2 uv = gl_TexCoord[0].xy;
    vec3 rgb = texture2D(front, uv).rgb;
    
    // Convert 10-bit integer clamp values to 0.0-1.0 float
    float low = float(clamp_low_10bit) / 1023.0;
    float high = float(clamp_high_10bit) / 1023.0;
    
    vec3 result_rgb = rgb;
    bool is_low = false;
    bool is_high = false;
    
    if (model_type == 0) {
        // --- MODEL: Y only - YCbCr ---
        float kr, kb;
        if (matrix_type == 0) { kr = 0.2126; kb = 0.0722; }
        else { kr = 0.2627; kb = 0.0593; }
        float kg = 1.0 - kr - kb;
        
        float y_norm = kr * rgb.r + kg * rgb.g + kb * rgb.b;
        float cb_norm = 0.5 * (rgb.b - y_norm) / (1.0 - kb);
        float cr_norm = 0.5 * (rgb.r - y_norm) / (1.0 - kr);
        
        is_low = y_norm < low;
        is_high = y_norm > high;
        
        if (enable_clamp) {
            float y_clamped = clamp(y_norm, low, high);
            float r_new = y_clamped + cr_norm * (2.0 * (1.0 - kr));
            float b_new = y_clamped + cb_norm * (2.0 * (1.0 - kb));
            float g_new = (y_clamped - kr * r_new - kb * b_new) / kg;
            result_rgb = vec3(r_new, g_new, b_new);
        }
    } else {
        // --- MODEL: RGB ---
        is_low = (rgb.r < low || rgb.g < low || rgb.b < low);
        is_high = (rgb.r > high || rgb.g > high || rgb.b > high);
        
        if (enable_clamp) {
            result_rgb = clamp(rgb, low, high);
        }
    }
    
    // Apply Preview Tint if enabled (overwrites image for clamped areas)
    if (enable_preview) {
        if (is_low) {
            result_rgb = vec3(1.0, 0.0, 1.0); // Magenta for shadows
        } else if (is_high) {
            result_rgb = vec3(1.0, 0.5, 0.0); // Orange for highlights
        }
    }
    
    gl_FragColor = vec4(result_rgb, 1.0);
}
