# Demonstrates DIT_SCENE_SELECTION: shows a dialog with a scene picker, then
# opens the selected scene in the Baselight timeline.

import flapi

conn = flapi.Connection.get()

def handle_menu_item(sender, signal, args):
    app = conn.Application.get()

    items = [
        flapi.DialogItem(
            Key="Scene",
            Label="Select Scene",
            Type=flapi.DIT_SCENE_SELECTION,
        ),
    ]

    result = conn.DynamicDialog.modal(
        "Select Scene",
        items,
        {}
    )

    if result is None:
        return

    scene_ref = result["Scene"]
    try:
        scene = app.open_scene_in_ui(
            scene_ref,
            flapi.UI_SCENE_USAGE_TIMELINE,
            {flapi.OPENFLAG_ALLOW_UNKNOWN_OFX}
        )
        scene.release()
    except flapi.FLAPIException as ex:
        app.message_dialog(
            "Error Opening Scene",
            str(ex),
            ["OK"]
        )

menuItem = conn.MenuItem.create("Open Scene from FLAPI")
menuItem.register(flapi.MENULOCATION_SCENE_MENU)
menuItem.connect("MenuItemSelected", handle_menu_item)

def handle_close_menu_item(sender, signal, args):
    app = conn.Application.get()
    scene = app.get_current_scene()
    if scene is None:
        app.message_dialog("Close Scene", "No scene is currently open.", ["OK"])
        return
    try:
        app.close_scene_in_ui(scene, flapi.UI_SCENE_USAGE_TIMELINE)
    except flapi.FLAPIException as ex:
        app.message_dialog("Error Closing Scene", str(ex), ["OK"])
    finally:
        scene.release()

closeMenuItem = conn.MenuItem.create("Close Scene from FLAPI")
closeMenuItem.register(flapi.MENULOCATION_SCENE_MENU)
closeMenuItem.connect("MenuItemSelected", handle_close_menu_item)
