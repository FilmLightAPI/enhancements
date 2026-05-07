# Creates MenuItems with counters in an object-oriented way

import flapi

conn = flapi.Connection.get()

class MyMenuItem:
    def __init__(self, message):
        # Save variables in this object instance
        self.message = message
        self.counter = 0

        # Register menu item with the application
        self.menuItem = conn.MenuItem.create( f"{self.message}: {self.counter}" )
        self.menuItem.register( flapi.MENULOCATION_APP_MENU )

        self.menuItem.connect( "MenuItemSelected", self.handle_signal )

    def handle_signal( self, sender, signal, args ):
        # Let's implement a local counter just to show we can update the menu item title
        self.counter += 1
        self.menuItem.set_title( f"{self.message}: {self.counter}" )

myMenuItem1 = MyMenuItem( "Apples" ) 
myMenuItem2 = MyMenuItem( "Oranges" ) 