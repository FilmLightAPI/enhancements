import contextlib
import sys

import flexi

EFFECT_ID = 'com.example.temporal_average'
EFFECT_VERSION = 1
OFFSETS = (-1, 0, 1)
# The CUDA context alone takes about 400 MB of GPU memory
FIXED_MB = 64 if sys.platform == 'darwin' else 500


class TemporalAverageEffect(flexi.Effect):

    def __init__(self):
        self.device = None

    def describe_effect(self, effect_id):
        return {
            'process_mode': {'linux': 'cuda_ipc', 'macos': 'shm'},
            'inputs': [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '4XFLOAT',
                        'planar': True, 'temporal': list(OFFSETS)}],
            'outputs': [{'name': 'out', 'label': 'Result', 'type': 'image', 'format': '4XFLOAT', 'planar': True}],
            'params': [
                {'name': 'mix', 'label': 'Mix', 'type': 'float', 'default': 1.0, 'range': [0.0, 1.0, 0.01],
                 'animated': True, 'tooltip': 'Blend between the current frame and the average of its neighbours.',
                 'uilocation': [0, 0]},
            ],
            'help': 'Averages each frame with the frames either side of it, alpha included. At the start and end '
                    'of a shot only the frames that exist are used.',
        }

    def query_vram_requirement(self, effect_id, data):
        frame_mb = data['width'] * data['height'] * 4 * 4 / (1024 * 1024)
        need = int(FIXED_MB + 6 * frame_mb)
        return {'min_mb': need, 'max_mb': need}

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

        inputs = data['inputs']
        mix = float(data['params'].get('mix', 1.0))
        present = [t for t in OFFSETS if inputs.get(f'src:{t}')]

        with contextlib.ExitStack() as stack:
            frames = {}
            for t in present:
                arr, rect = stack.enter_context(self.open_input(inputs, 'src', 4, planar=True, temporal_index=t))
                frames[t] = torch.as_tensor(arr).to(self.device)
            if len({tuple(f.shape) for f in frames.values()}) > 1:
                return flexi.error('Neighbouring frames differ in size',
                                   ', '.join(f'{t}: {tuple(f.shape)}' for t, f in frames.items()))
            out, orect = stack.enter_context(self.open_output(data['output'], 4, planar=True))
            current = frames[0]
            average = sum(frames.values()) / len(frames)
            self.write_output(out, orect, current + mix * (average - current), inputs['src:0']['rect'])
        return {}


if __name__ == '__main__':
    effect = TemporalAverageEffect()
    effect.init([(EFFECT_ID, EFFECT_VERSION)])
    flexi.run()
