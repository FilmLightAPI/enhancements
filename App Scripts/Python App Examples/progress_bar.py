# Makes a ProgressBar, triggered by a MenuItem

import flapi
import time

scene = None

# Define handler function for "MenuItemSelected" signal of 'menu_item'
def onMenuItemSelected(sender, signal, args):
    # Create the ProgressBar
    pb = conn.ProgressDialog.create("A Progress Bar That Counts to 9", "", True)
    # Show the ProgressBar
    try: # We'll wrap the ProgressBar updates with Try/Except to avoid getting stuck with it displayed should we have an error in the following code
        pb.show()
        for i in range(10):
            pb.set_progress(i/10., "Count: %i" % i)
            time.sleep(0.5)
        pb.hide()
    except Exception as e: # Hide ProgressBar on any error
        pb.hide()
        print("Error: %s" % e, flush=True)

# Connect to FLAPI
conn = flapi.Connection.get() 
conn.connect()

# Get application
app = conn.Application.get()
 
# Place menu item on Scene menu
menu_item = conn.MenuItem.create("Show Progress Bar")
menu_item.register(flapi.MENULOCATION_APP_MENU)

# Connect up both the 'MenuItemSelected' signal
menu_item.connect("MenuItemSelected", onMenuItemSelected)
