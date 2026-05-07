import flapi

def onMenuItem1Selected(sender, signal, args):
    result = app.message_dialog("You clicked 'Menu Item 1'", "", ['OK'])

def onMenuItem2Selected(sender, signal, args):
    result = app.message_dialog("You clicked 'Menu Item 2'", "", ['OK'])

# Connect to FLAPI
conn = flapi.Connection.get() 
conn.connect()

# Get application
app = conn.Application.get()
 
# Place menu items
holder_menu = conn.Menu.create()

menu_items_label = conn.MenuItem.create("My Top Level Menu")
menu_items_label.register(flapi.MENULOCATION_EDIT_MENU)
menu_items_label.set_sub_menu(holder_menu)

menu_item_1 = conn.MenuItem.create("Menu Item 1")
menu_item_1.connect("MenuItemSelected", onMenuItem1Selected)
holder_menu.add_item(menu_item_1)

menu_item_2 = conn.MenuItem.create("Menu Item 2")
menu_item_2.connect("MenuItemSelected", onMenuItem2Selected)
holder_menu.add_item(menu_item_2)