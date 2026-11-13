import sys

import flexi

EFFECT_ID = 'com.example.point_matte'
EFFECT_VERSION = 1
SIZE = 512
# The CUDA context alone takes about 400 MB of GPU memory
FIXED_MB = 64 if sys.platform == 'darwin' else 500


class PointMatteEffect(flexi.Effect):

    def __init__(self):
        self.device = None

    def describe_effect(self, effect_id):
        return {
            'process_mode': {'linux': 'cuda_ipc', 'macos': 'shm'},
            'inputs': [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '3XFLOAT', 'planar': True}],
            'outputs': [{'name': 'matte', 'label': 'Matte', 'type': 'image', 'format': '1XFLOAT', 'planar': True}],
            'fixed_image_size': {'width': SIZE, 'height': SIZE, 'scaling': 'fit_inside'},
            'roi_sensitive': True,
            'params': [
                {'name': 'radius', 'label': 'Radius', 'type': 'float',
                 'default': 200.0, 'range': [1.0, 2000.0, 1.0], 'animated': True,
                 'tooltip': 'Radius of the matte, in frame pixels.', 'uilocation': [0, 0]},
                {'name': 'softness', 'label': 'Softness', 'type': 'float',
                 'default': 0.5, 'range': [0.0, 1.0, 0.01], 'animated': True,
                 'tooltip': 'Fraction of the radius over which the matte fades out.', 'uilocation': [0, 1]},
                {'name': 'centre', 'label': 'Centre', 'type': 'point', 'default': [0.5, 0.5],
                 'drawstyle': {'shape': 'Diamond', 'colour': [1.0, 0.5, 0.0], 'label': 'Centre'},
                 'uilocation': [0, 2]},
            ],
            'help': 'A soft round matte around a point you place in the viewer.',
        }

    def query_vram_requirement(self, effect_id, data):
        frame_mb = data['width'] * data['height'] * 4 * 4 // (1024 * 1024)
        return {'min_mb': FIXED_MB + frame_mb, 'max_mb': FIXED_MB + frame_mb}

    def set_vram_limit(self, effect_id, data):
        if int(data['limit_mb']) == 0 and self.device is not None:
            if self.device.type == 'cuda':
                return 'quit'
            if self.device.type == 'mps':
                import torch
                torch.mps.empty_cache()
        return {}

    def centre_in_fixed(self, value, data):
        if isinstance(value, dict):
            p = {'X': value['X'], 'Y': value['Y']}
            self.transform_point(p, data['transform_to_fixed'])
            return p['X'], p['Y']
        # fl-flexi-test sends the param's default: fractions of the frame
        return value[0] * data['width'], value[1] * data['height']

    def run_generate(self, effect_id, instance, data):
        import torch
        if self.device is None:
            self.device = self.get_torch_device()

        params = data['params']
        cx, cy = self.centre_in_fixed(params['centre'], data)
        radius = max(float(params['radius']) * data['transform_to_fixed']['Xx'], 1e-3)
        fade = max(float(params['softness']) * radius, 1e-3)

        with self.open_output(data['output'], channels=1, planar=True) as (out, orect):
            cols = torch.arange(orect['width'], device=self.device) + orect['left'] + 0.5
            rows = torch.arange(orect['height'], device=self.device) + orect['top'] + 0.5
            dist = torch.hypot(cols[None, :] - cx, rows[:, None] - cy)
            matte = ((radius - dist) / fade).clamp(0.0, 1.0)
            self.write_output(out, orect, matte[None], orect)
        return {}


if __name__ == '__main__':
    effect = PointMatteEffect()
    effect.init([(EFFECT_ID, EFFECT_VERSION)])
    flexi.run()
