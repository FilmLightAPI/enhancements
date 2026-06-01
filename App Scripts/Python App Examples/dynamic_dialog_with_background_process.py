#!/usr/bin/env python3
"""
dynamic_dialog_with_background_process.py - A DynamicDialog that validates
input against a slow (fake) server without freezing the UI.

Adds a "Show Dialog" item to the App menu. The dialog has a password field and
a status line. The flow:

  - You type a value. OK is dimmed and the status shows "Checking with
    server..." (driven by the "Valid" flag returned from SettingsChanged).
  - The slow check (fake_server_lookup, which sleeps to imitate latency) runs
    on a worker thread so it never freezes the modal.
  - A REPEATING dialog timer (set_timer_callback(delay, repeat=1) +
    TimerCallback) fires every POLL_MS and checks the worker for doneness. When
    it's done, the timer handler returns the verdict the same way SettingsChanged
    does ({Valid, Settings, Updates}), which repaints the dialog: green (correct)
    or red (incorrect). OK only enables (Valid=1) when the value is correct.

Enter "baselight" to pass.

Deploy: place (or symlink) in /vol/.support/scripts
Reload after edits via Views > Scripts > Gear > Reload Scripts.
As a UI script it shares the app's connection via Connection.get().
"""

import threading
import time
import flapi

EXPECTED = "baselight"     # the password the fake server accepts
SERVER_LATENCY_S = 2       # how long the fake server "takes"
POLL_MS = 250              # how often the timer checks for doneness


def fake_server_lookup(work, value):
    """Runs on a worker thread. Sleeps to imitate server latency, then records
    the verdict in the shared `work` dict for the timer to pick up."""
    time.sleep(SERVER_LATENCY_S)
    work["ok"] = (value == EXPECTED)
    work["done"] = True


class PasswordDialog:
    def __init__(self, conn):
        self.conn = conn
        self.dialog = None
        self.pending = None         # value currently being checked
        self.work = None            # shared state with the worker thread
        self.resolved_value = None  # value we have a verdict for
        self.resolved_ok = False    # that verdict

    def show(self, sender, signal, args):
        # Reset state so every time the dialog opens it checks afresh.
        self.pending = None
        self.work = None
        self.resolved_value = None
        self.resolved_ok = False

        items = [
            flapi.DialogItem(Key="Entry", Label="Password",
                             Type=flapi.DIT_STRING, Default="",
                             Help=f"The password is '{EXPECTED}'"),
            flapi.DialogItem(Key="Status", Label="",
                             Type=flapi.DIT_STATIC_TEXT, Default=""),
        ]
        settings = {"Entry": "", "Status": ""}

        self.dialog = self.conn.DynamicDialog.create("Authenticate", items, settings)
        self.dialog.connect("SettingsChanged", self.on_changed)
        self.dialog.connect("TimerCallback", self.on_timer)

        result = self.dialog.show_modal(340, 120)
        print(f"Dialog result: {result}", flush=True)

    def on_changed(self, sender, signal, args):
        entry = args.get("Entry") or ""

        # Empty field -> invalid, OK dimmed.
        if not entry:
            self.dialog.cancel_timer_callback()
            self.pending = None
            self.work = None
            return self._reply(args, valid=0, msg="Enter the password.", style="orange")

        # We already have a verdict for this exact value.
        if entry == self.resolved_value:
            if self.resolved_ok:
                return self._reply(args, valid=1, msg="Correct - click OK.", style="green")
            return self._reply(args, valid=0, msg="Incorrect - try again.", style="red")

        # New value: kick off the worker and a repeating poll timer (once).
        if entry != self.pending:
            self.pending = entry
            self.work = {"done": False, "ok": False}
            threading.Thread(target=fake_server_lookup,
                             args=(self.work, entry), daemon=True).start()
            self.dialog.set_timer_callback(POLL_MS, 1)  # repeat=1

        return self._reply(args, valid=0, msg="Checking with server...", style="orange")

    def on_timer(self, sender, signal, args):
        # Fires repeatedly. Keep waiting until the worker reports done.
        if not self.work or not self.work["done"]:
            return

        # Done: record the verdict, stop the timer, and return the styled
        # result. Like SettingsChanged, the TimerCallback handler updates the
        # dialog (OK button + status + colour) via what it returns.
        ok = self.work["ok"]
        self.resolved_value = self.pending
        self.resolved_ok = ok
        self.pending = None
        self.work = None
        self.dialog.cancel_timer_callback()

        if ok:
            return self._reply(args, valid=1, msg="Correct - click OK.", style="green")
        return self._reply(args, valid=0, msg="Incorrect - try again.", style="red")

    def _reply(self, args, valid, msg, style):
        args["Status"] = msg
        return {
            "Valid": valid,
            "Settings": args,
            "Updates": [{"Name": "Status", "Style": style}],
        }


conn = flapi.Connection.get()
password_dialog = PasswordDialog(conn)

menu_item = conn.MenuItem.create("Show Password Dialog")
menu_item.connect("MenuItemSelected", password_dialog.show)
menu_item.register(flapi.MENULOCATION_APP_MENU)
