# Jump To Clipboard Timecode
#
# Reads the system clipboard and, if it contains a valid timecode
# (e.g. 01:00:00:00), moves the current cursor to that timecode in the scene.
#
# On macOS clipboard capture uses the bult-in "pbpaste" utility
# On Linux the "xsel" utility must be installed, e.g. with:
#  sudo dnf --enablerepo=epel install xsel
#
# Access via the main Baselight/Daylight menu > Jump To Clipboard Timecode.
# or via Keyboard shortcut "Ctrl + Opt + V" on Mac, "Win + Alt + V" on Linux
#

import re
import subprocess
import sys

import flapi

conn = flapi.Connection.get()

TC_PATTERN = re.compile(r"^\s*(\d{2})[:. ](\d{2})[:. ](\d{2})[:. ](\d{2})\s*$")


def get_clipboard_text():
    """Return the system clipboard's text content, or None if unavailable."""
    if sys.platform == "darwin":
        return _get_clipboard_command(["pbpaste"])
    return _get_clipboard_command(["xsel", "--clipboard", "--output"])


def _get_clipboard_command(cmd):
    """Run a clipboard tool and return its stdout as text, or None."""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def parse_timecode(text, fps):
    """Return a flapi.Timecode if text matches HH:MM:SS:FF, else None."""
    if not text:
        return None
    match = TC_PATTERN.match(text)
    if not match:
        return None
    hour, minute, second, frame = (int(g) for g in match.groups())
    if minute >= 60 or second >= 60 or frame >= int(fps):
        return None
    return flapi.Timecode(hour, minute, second, frame)


def timecode_to_frames(tc, fps):
    """Convert a Timecode to an absolute frame count at the given fps."""
    return int(((tc.hour * 3600 + tc.minute * 60 + tc.second) * fps) + tc.frame)


class JumpToClipboardTimecodeMenuItem:
    def __init__(self, message):
        self.menuItem = conn.MenuItem.create(message)
        self.menuItem.register(flapi.MENULOCATION_APP_MENU)
        # Keyboard shortcut "Ctrl + Opt + V" on Mac, "Win + Alt + V" on Linux
        self.menuItem.set_keyboard_accelerator("v", {"Alt", "Meta"})
        self.menuItem.connect("MenuItemSelected", self.handle_signal)

    def handle_signal(self, sender, signal, args):
        app = conn.Application.get()

        text = get_clipboard_text()
        if text is None:
            app.log(
                "Clipboard Timecode",
                flapi.LOGSEVERITY_SOFT,
                "Could not read the system clipboard."
            )
            return

        scene = app.get_current_scene()
        if scene is None:
            app.log(
                "Clipboard Timecode",
                flapi.LOGSEVERITY_SOFT,
                "No scene is open"
            )
            return

        text = text.strip()
        fps = scene.get_working_frame_rate()
        print(f"Jump To Clipboard Timecode: clipboard text = '{text}'", flush=True)

        tc = parse_timecode(text, fps)
        if tc is None:
            if len(text) > 12:
                text = text[:12] + "..."
            app.log(
                "Clipboard Timecode",
                flapi.LOGSEVERITY_SOFT,
                f"'{text}' is not a valid timecode. Expecting HH:MM:SS:FF",
            )
            return

        cursor = app.get_current_cursor()
        if cursor is None:
            app.log(
                "Clipboard Timecode",
                flapi.LOGSEVERITY_SOFT,
                "No cursor is active.",
            )
            return

        timecode_at_zero = scene.get_record_timecode_for_frame(0)
        target_frame = timecode_to_frames(tc, fps) - timecode_to_frames(
            timecode_at_zero, fps
        )

        cursor.set_frame(target_frame)


jump_menu_item = JumpToClipboardTimecodeMenuItem("Jump To Clipboard Timecode")
