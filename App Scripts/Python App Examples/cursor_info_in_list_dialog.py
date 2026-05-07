# Makes a ListDialog, triggerable by a MenuItem, that displays info about the app's cursors

import flapi

# Define handler function for "MenuItemSelected" signal of 'list_dialog_menu_item'
def onListDialogMenuItemSelected(sender, signal, args):
    # Get all open cursors
    cursors = app.get_cursors()

    # Make a list of options for the ListDialog
    options = []
    for k, cursor in enumerate(cursors):
        v = "Cursor @ " + str(cursor.get_frame())
        # Flag the active cursor
        if cursor == app.get_current_cursor():
            v += " (ACTIVE)"
        v += " : viewing format %s" % cursor.get_viewing_format_name()
        options.append({"Key": k, "Text": v})

    # Create the list dialog, providing title, button text and items
    result = app.list_dialog("Open Cursors by Frame Number and Viewing Format", "Choose", options)
    # For now, just write the user's choice to the application log
    app.log("Example Log Category", flapi.LOGSEVERITY_SOFT, "User chose '%s'." % options[result]['Text'])

# Connect to FLAPI
conn = flapi.Connection.get() 
conn.connect()

# Get application
app = conn.Application.get()
 
# Place menu item on Scene menu
list_dialog_menu_item = conn.MenuItem.create("Show Cursor Info")
list_dialog_menu_item.register(flapi.MENULOCATION_APP_MENU)

# Connect up both the 'MenuItemSelected' signals
list_dialog_menu_item.connect("MenuItemSelected", onListDialogMenuItemSelected)
