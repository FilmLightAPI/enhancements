import flapi

conn = flapi.Connection()
conn.connect()

# Fetch factory-defined formats

factoryFormats = conn.FormatSet.factory_formats();

########################################################
# Get burnin in existing factory format

fmtName = "HD 1920x1080"
burninName = "Data Dailies"

fmt = factoryFormats.get_format( fmtName )

print( "Get burnins for %s" % fmtName )

burninNames = fmt.get_burnin_names()
print( burninNames )

print( "Get '%s' burnin" % burninName )

data_burnin = fmt.get_burnin( burninName )
print( data_burnin )

print( "Get items in '%s' burnin" % burninName )

items = data_burnin.get_num_items()
for i in range(items):
    item = data_burnin.get_item(i)
    print( "Item %d : %s" % (i, item) )

########################################################
# Create a new burnin

burninName = "My Burnin"
print( "Create burnin '%s'" % burninName )

# Add text burnin
def make_text_item( x, y, size, text ):
    return flapi.FormatBurninItem({
        "Type": flapi.BURNIN_ITEM_TEXT,
        "X": x,
        "Y": y,
        "XAlign": flapi.BURNIN_HALIGN_LEFT,
        "YAlign": flapi.BURNIN_VALIGN_TOP,
        "Box": flapi.BURNIN_BORDER_LOZENGE,
        "Height": 30,
        "Text": text
    })

if fmt.get_burnin( burninName ) != None:
    fmt.delete_burnin( burninName )

myBurnin = fmt.add_burnin( burninName )

myBurnin.add_item( make_text_item( 20, 20, 20, "First"  ) )
myBurnin.add_item( make_text_item( 20, 50, 20, "Second" ) )
myBurnin.add_item( make_text_item( 20, 80, 20, "Third" ) )

print( "Get items in '%s'" % burninName )

items = myBurnin.get_num_items()
for i in range(items):
    item = myBurnin.get_item(i)
    print( "Item %d : %s" % (i, item) )

print( "Deleting burnin '%s'" % burninName )

fmt.delete_burnin( burninName )
