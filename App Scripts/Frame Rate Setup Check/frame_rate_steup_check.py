import flapi
import subprocess
import re


def get_bl_setup_rate():
    try:
        result = subprocess.run(['bl-setup', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        match = re.search(r'Rate:\s*(\d+\.\d+)', result.stdout)
        if match:
            return float(match.group(1))
    except Exception as e:
        app.log("Setup Checker", flapi.LOGSEVERITY_SOFT, f"Error running bl-setup: {e}")
    return None


def is_fps_equal(fps1, fps2):
    return abs(fps1 - fps2) < 0.01  # Small tolerance for 23.98 vs 23.976


def onSceneOpen(sender, signal, args):
    conn = flapi.Connection.get()
    app = conn.Application.get()

    scene_string = app.get_current_scene_name()
    if scene_string and "baselight_gallery" not in scene_string:
        try:
            scene = app.get_current_scene()
            scene_settings = scene.get_scene_settings()
            fps = scene_settings.get_single('WorkingFrameRate')
            scene.release()
            bl_rate = get_bl_setup_rate()
            if bl_rate is not None and not is_fps_equal(bl_rate, fps):
                app.message_dialog('Setup Checker', f'Setup framerate ({bl_rate}) does not match scene FPS ({fps})', ['OK'])
        except Exception as e:
            app.log("Setup Checker", flapi.LOGSEVERITY_SOFT, f"Error checking framerate: {e}")


conn = flapi.Connection.get()
app = conn.Application.get()
app.connect('SceneOpened', onSceneOpen)