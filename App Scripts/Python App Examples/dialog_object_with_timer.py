import flapi
import time
from datetime import datetime

#
# Define a dialog class which uses DynamicDialog to present a dialog to the user.
# It uses the timer callback to update asynchronously
# 

class MyDialog:
    def __init__(self, conn):
        self.conn = conn

        # define items to show in dialog
        self.items = [
            flapi.DialogItem(Key="Name", Label="Name", Type=flapi.DIT_STRING, Default = ""),
            flapi.DialogItem(Key="Desc", Label="Description", Type=flapi.DIT_STRING, Default=""),
            flapi.DialogItem(Key="Time", Label="Current Time", Type=flapi.DIT_STATIC_TEXT, Default=""),
        ]

        # create an empty dictionary for the default settings for the dialog
        self.settings = {
            "Name": "",
            "Desc": "",
            "Time": ""
        }

        # create dialog, which will be shown later
        self.dialog = self.conn.DynamicDialog.create( 
            "My Dialog",
            self.items,
            self.settings
        )

        # connect TimerCallback signal, which will trigger when dialog is presented
        self.dialog.connect( "TimerCallback", self.handle_timer )

    def handle_timer(self, sender, signal, args):
        # Update settings in dialog
        #
        # You can update the contents of the dialog by return a dictionary containing
        # the new settings
        #
        settings = args
        settings["Time"] = time.strftime("%H:%M:%S %Z")
        return { "Settings": settings }

    def show(self):
        # initialise the settings before we display the dialog
        self.settings["Time"] = time.strftime("%H:%M:%S %Z")
        self.dialog.set_settings( self.settings )

        # start the timer callback, to update every 1000 ms.
        # the TimerCallback signal will be emitted every 1000 ms.
        self.dialog.set_timer_callback( 1000 )

        # show the dialog modally
        # if the user clicks OK, the settings from the dialog will be returned
        # as a dictionary
        # 
        # If you pass a negative width/height, it will add this width/height to the
        # default with of the contents of the dialog.
        #
        return self.dialog.show_modal(-200, -50)

#
# Define a MenuItem class which will be used to launch our dialog when it is selected.
#

class MyDialogMenuItem:
    def __init__(self, conn):
        self.conn = conn
        
        # create the menu item
        # listen to its MenuItemSelected signal to launch the dialog
        self.menuItem = conn.MenuItem.create( "Show My Timer Dialog" )
        self.menuItem.register( flapi.MENULOCATION_APP_MENU )
        self.menuItem.connect( "MenuItemSelected", self.handle_menu_item )
        
        # create the dialog, which we will use later.
        self.dialog = MyDialog( self.conn )

    def handle_menu_item( self, sender, signal, args ):
        result = self.dialog.show()
        if result:
            # Show results.
            #
            # need to fetch an instance of the Application class to
            # use the message_dialog method.
            #
            app = self.conn.Application.get()
            app.message_dialog( 
                "Dialog Done",
                "Name was '%s' and Description was '%s'." % (result['Name'], result['Desc']),
                ["OK"]
            )


#
# Connect to FLAPI and create the menu item
#

conn = flapi.Connection.get()
menuItem = MyDialogMenuItem( conn )
