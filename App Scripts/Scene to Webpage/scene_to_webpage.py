#!/usr/bin/env python3
"""
scene_to_webpage.py - Serve the current scene's shots as a local web page.

Adds a "Show Scene as Webpage" item to the App menu. When selected it reads
every shot in the current scene, builds an HTML table, serves it from a small
background web server, and opens your browser at the URL. A self-contained
example of turning FLAPI scene data into something viewable - no accounts, no
credentials, standard library only.

The web server runs on a daemon thread so the Baselight/Daylight UI never
blocks. The page is read from a temp file on each request, so re-running the
menu item just refreshes what the already-running server serves.

As a UI script it shares the app's connection via Connection.get().

Deploy: place (or symlink) in /vol/.support/scripts
Reload after edits via Views > Scripts > Gear > Reload Scripts.
"""

import html
import http.server
import threading
import webbrowser

import flapi

PORT = 8765
PAGE_FILE = "/tmp/flapi_scene_page.html"

conn = flapi.Connection.get()
app = conn.Application.get()

_server = None  # the running web server, started on first use


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            with open(PAGE_FILE, "rb") as fh:
                body = fh.read()
        except FileNotFoundError:
            body = b"<html><body>No scene exported yet.</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep the app log quiet


def ensure_server():
    """Start the web server once, on a daemon thread."""
    global _server
    if _server is not None:
        return
    try:
        _server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    except OSError:
        # Port already taken, almost certainly by a server we started before a
        # script reload. It will serve the refreshed page file, so carry on.
        return
    threading.Thread(target=_server.serve_forever, daemon=True).start()


def get_shot_rows(scene):
    """Return one [source path, start frame, end frame] row per shot."""
    rows = []
    nshots = scene.get_num_shots()
    if nshots > 0:
        for shot_inf in scene.get_shot_ids(0, nshots):
            shot = scene.get_shot(shot_inf.ShotId)
            seq = shot.get_sequence_descriptor()
            rows.append([
                f"{seq.get_path()}/{seq.get_name()}",
                seq.get_start_frame(),
                seq.get_end_frame(),
            ])
            seq.release()
            shot.release()
    return rows


def build_html(title, rows):
    cells = "\n".join(
        f"      <tr><td>{i}</td><td>{html.escape(src)}</td>"
        f"<td>{start}</td><td>{end}</td></tr>"
        for i, (src, start, end) in enumerate(rows, 1)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; margin: 2rem; color: #222; }}
    h1 {{ font-size: 1.25rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #ddd; }}
    th {{ background: #f4f4f4; }}
    tr:hover td {{ background: #fafafa; }}
    th:first-child, td:first-child {{ color: #888; width: 3rem; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)} &mdash; {len(rows)} shot(s)</h1>
  <table>
    <thead><tr><th>#</th><th>Source</th><th>Start</th><th>End</th></tr></thead>
    <tbody>
{cells}
    </tbody>
  </table>
</body>
</html>
"""


def show_scene_as_webpage(sender, signal, args):
    scene = app.get_current_scene()
    if scene is None:
        app.message_dialog("Scene Webpage", "Open a scene first.", ["OK"])
        return

    title = app.get_current_scene_name()
    try:
        rows = get_shot_rows(scene)
    finally:
        scene.release()

    with open(PAGE_FILE, "w") as fh:
        fh.write(build_html(title, rows))

    ensure_server()
    url = f"http://127.0.0.1:{PORT}/"
    webbrowser.open(url)
    app.message_dialog("Scene Webpage",
                       f"Serving {len(rows)} shot(s) at:\n{url}", ["OK"])


menu_item = conn.MenuItem.create("Show Scene as Webpage")
menu_item.register(flapi.MENULOCATION_SCENE_MENU)
menu_item.connect("MenuItemSelected", show_scene_as_webpage)
