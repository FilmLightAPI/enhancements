import os
import sys
import flapi

c = flapi.Connection("localhost")

try:
    c.connect()
except flapi.FLAPIException as exc:
    print( "Error: %s" % exc )
    sys.exit(1)

print( "Connection OK" )
