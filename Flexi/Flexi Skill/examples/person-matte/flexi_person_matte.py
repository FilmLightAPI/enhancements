import os
import sys

import flexi

EFFECT_ID = 'com.example.person_matte'
EFFECT_VERSION = 1
WEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weights', 'deeplabv3_mobilenet_v3_large.pth')
PERSON = 15

# VRAM model measured on CUDA, with about 40% headroom: a fixed part (CUDA context, weights,
# workspace), a part for the inference resolution, and a part per frame pixel for the full-size buffers.
FIXED_MB = {'cuda': 600, 'mps': 300, 'cpu': 0}
INFER_MB = {1024: 200, 512: 100}
FRAME_BYTES_PER_PIXEL = 24


def vram_needed_mb(device_type, width, height, long_side):
    return int(FIXED_MB.get(device_type, 0) + INFER_MB[long_side] + width * height * FRAME_BYTES_PER_PIXEL / (1 << 20))


class PersonMatteEffect(flexi.Effect):

    def __init__(self):
        self.device = None
        self.model = None
        self.limit_mb = None

    def describe_effect(self, effect_id):
        return {
            'process_mode': {'linux': 'cuda_ipc', 'macos': 'shm'},
            'inputs': [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '3XFLOAT', 'planar': True,
                        'normalise': {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]}}],
            'outputs': [{'name': 'matte', 'label': 'Matte', 'type': 'image', 'format': '1XFLOAT', 'planar': True}],
            'input_colour_space': 'sRGB_Display',
            'roi_sensitive': True,
            'params': [
                {'name': 'invert', 'label': 'Invert', 'type': 'bool', 'default': 0, 'uilocation': [0, 0]},
            ],
            'help': 'Makes a soft matte of the people in the frame.',
        }

    def _device_type(self):
        # From the platform alone: query methods must answer at once and the same way every time
        return 'mps' if sys.platform == 'darwin' else 'cuda'

    def query_vram_requirement(self, effect_id, data):
        device_type = self._device_type()
        w, h = data['width'], data['height']
        return {'min_mb': vram_needed_mb(device_type, w, h, min(INFER_MB)),
                'max_mb': vram_needed_mb(device_type, w, h, max(INFER_MB))}

    def set_vram_limit(self, effect_id, data):
        self.limit_mb = int(data['limit_mb'])
        if self.model is not None and self.limit_mb < FIXED_MB.get(self.device.type, 0) + min(INFER_MB.values()):
            if self.device.type == 'cuda':
                return 'quit'
            self.release()
        return {}

    def load(self):
        import torch
        from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large
        self.device = self.get_torch_device()
        model = deeplabv3_mobilenet_v3_large(weights=None, weights_backbone=None, aux_loss=True)
        model.load_state_dict(torch.load(WEIGHTS, map_location='cpu', mmap=True, weights_only=True))
        self.model = model.eval().to(self.device)

    def release(self):
        import torch
        self.model = None
        if self.device is not None and self.device.type == 'mps':
            torch.mps.empty_cache()

    def long_side_for(self, width, height):
        if self.limit_mb is None:
            return max(INFER_MB)
        for long_side in sorted(INFER_MB, reverse=True):
            if vram_needed_mb(self.device.type, width, height, long_side) <= self.limit_mb:
                return long_side
        return min(INFER_MB)

    def infer(self, image, long_side):
        """image: (1, 3, H, W) normalised tensor on self.device. Returns the (1, H, W) person matte."""
        import torch
        import torch.nn.functional as F
        h, w = image.shape[-2:]
        scale = min(1.0, long_side / max(h, w))
        # MPS has no 'area' resize for uneven ratios, and torch 2.2 MPS no antialias: pool by a whole factor first
        factor = max(1, min(int(1 / scale), h, w))
        small = F.avg_pool2d(image, factor) if factor > 1 else image
        small = F.interpolate(small, size=(max(1, round(h * scale)), max(1, round(w * scale))), mode='bilinear',
                              align_corners=False)
        with torch.inference_mode():
            logits = self.model(small)['out']
            prob = logits.softmax(1)[:, PERSON:PERSON + 1]
            return F.interpolate(prob, size=(h, w), mode='bilinear', align_corners=False)[0]

    def run_generate(self, effect_id, instance, data):
        import torch
        if self.model is None:
            self.load()
        with self.open_input(data['inputs'], 'src', 3, planar=True) as (src, irect), \
             self.open_output(data['output'], 1, planar=True) as (out, orect):
            image = torch.as_tensor(src).to(self.device).unsqueeze(0)
            matte = self.infer(image, self.long_side_for(irect['width'], irect['height']))
            if data['params'].get('invert'):
                matte = 1.0 - matte
            self.write_output(out, orect, matte, irect)
        return {}


if __name__ == '__main__':
    effect = PersonMatteEffect()
    effect.init([(EFFECT_ID, EFFECT_VERSION)])
    flexi.run()
