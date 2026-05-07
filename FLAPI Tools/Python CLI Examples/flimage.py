import sys
import flapi

conn = flapi.Connection("localhost")
conn.connect()

result = conn.FLImage.get_raw_metadata(sys.argv[1])

print( result )
