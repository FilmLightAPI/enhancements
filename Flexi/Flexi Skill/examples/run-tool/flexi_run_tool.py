import os
import signal
import subprocess
import sys

import flexi

EFFECT_ID = 'com.example.run_tool'
EFFECT_VERSION = 1

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = [sys.executable, os.path.join(HERE, 'tool', 'gamma.py')]
# Baselight waits for every reply without a time limit: a hung tool would hang the render
TIMEOUT_S = 120


class RunToolEffect(flexi.Effect):

    def describe_effect(self, effect_id):
        return {
            'process_mode': 'file',
            'process_filetype': 'PPM16',
            'inputs': [{'name': 'src', 'label': 'Source', 'type': 'image', 'format': '3XFLOAT'}],
            'outputs': [{'name': 'out', 'label': 'Result', 'type': 'image', 'format': '3XFLOAT'}],
            'params': [
                {'name': 'gamma', 'label': 'Gamma', 'type': 'float',
                 'default': 2.2, 'range': [0.1, 4.0, 0.01], 'animated': True,
                 'tooltip': 'Passed to the tool as --gamma.',
                 'uilocation': [0, 0]},
            ],
            'help': 'Runs a command-line tool on each frame, through image files.',
            # The input file then covers exactly the output area, so the tool's result fits it
            'local_methods': {'query_input_rects_v1': {'src': 'output'}},
        }

    def query_vram_requirement(self, effect_id, data):
        return {'min_mb': 0, 'max_mb': 0}

    def set_vram_limit(self, effect_id, data):
        return {}

    def run_generate(self, effect_id, instance, data):
        src = data['inputs']['src:0']['file']
        dst = data['output']['file']
        if os.path.exists(dst):
            os.unlink(dst)
        cmd = TOOL + ['--gamma', str(float(data['params'].get('gamma', 2.2))), src, dst]
        try:
            tool = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    encoding='utf-8', errors='replace', start_new_session=True)
        except OSError as e:
            return flexi.error('The tool could not be started', f'{cmd[0]}: {e}')
        try:
            stdout, stderr = tool.communicate(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            # Its own process group: whatever the tool started goes too
            try:
                os.killpg(tool.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            tool.wait()
            # Not communicate(): anything that escaped the group may still hold the pipes open
            tool.stdout.close()
            tool.stderr.close()
            return flexi.error('The tool did not finish', f'{" ".join(cmd)}\nstopped after {TIMEOUT_S}s')
        if tool.returncode != 0:
            return flexi.error(f'The tool failed (exit code {tool.returncode})', (stderr or stdout)[-2000:])
        if not os.path.exists(dst):
            return flexi.error('The tool wrote no output', ' '.join(cmd))
        return {}


if __name__ == '__main__':
    effect = RunToolEffect()
    effect.init([(EFFECT_ID, EFFECT_VERSION)])
    flexi.run()
