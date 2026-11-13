import sys

import flexi

EFFECT_ID = 'com.example.gain'
EFFECT_VERSION = 1
# The CUDA context alone takes about 400 MB of GPU memory
FIXED_MB = 64 if sys.platform == 'darwin' else 500


class GainEffect(flexi.Effect):

    def __init__(self):
        self.device = None

    def describe_effect(self, effect_id):
        return {
            'process_mode': {'linux': 'cuda_ipc', 'macos': 'shm'},
            'inputs': [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '3XFLOAT', 'planar': True}],
            'outputs': [{'name': 'out', 'label': 'Result', 'type': 'image', 'format': '3XFLOAT', 'planar': True}],
            'params': [
                {'name': 'gain', 'label': 'Gain', 'type': 'float',
                 'default': 1.0, 'range': [0.0, 4.0, 0.01], 'animated': True,
                 'tooltip': 'Multiplier applied to every channel.',
                 'uilocation': [0, 0]},
            ],
            'help': 'Multiplies the image by a constant. A starting point for new effects.',
        }

    def query_vram_requirement(self, effect_id, data):
        frame_mb = data['width'] * data['height'] * 3 * 4 // (1024 * 1024)
        return {'min_mb': FIXED_MB + 2 * frame_mb, 'max_mb': FIXED_MB + 2 * frame_mb}

    def set_vram_limit(self, effect_id, data):
        if int(data['limit_mb']) == 0 and self.device is not None:
            if self.device.type == 'cuda':
                return 'quit'
            if self.device.type == 'mps':
                import torch
                torch.mps.empty_cache()
        return {}

    def run_generate(self, effect_id, instance, data):
        import torch
        if self.device is None:
            self.device = self.get_torch_device()

        gain = float(data['params'].get('gain', 1.0))
        with self.open_input(data['inputs'], 'src', channels=3, planar=True) as (src, irect), \
             self.open_output(data['output'], channels=3, planar=True) as (out, orect):
            image = torch.as_tensor(src).to(self.device)
            result = image * gain
            self.write_output(out, orect, result, irect)
        return {}


if __name__ == '__main__':
    effect = GainEffect()
    effect.init([(EFFECT_ID, EFFECT_VERSION)])
    flexi.run()
