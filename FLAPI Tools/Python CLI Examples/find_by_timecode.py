import flapi
import sys

path = sys.argv[1]
startTC_str = None
endTC_str = None
startTC = None
endTC = None

if len(sys.argv) >= 4:
    startTC_str = sys.argv[2]
    endTC_str = sys.argv[3]

conn = flapi.Connection("localhost")

try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

if startTC_str != None:
    try:
        startTC = conn.Utilities.timecode_from_string( startTC_str, 24 )
    except flapi.FLAPIException as exc:
        print( "Cannot parse start timecode '%s': %s" % (startTC_str, exc) )
        sys.exit(1)

if endTC_str != None:
    try:
        endTC = conn.Utilities.timecode_from_string( endTC_str, 24 )
    except flapi.FLAPIException as exc:
        print( "Cannot parse end timecode '%s': %s" % (endTC_Str, exc) )
        sys.exit(1)

print( "Searching for:" )
print( "  Path %s" % path )
print( "  Timecode %s - %s" % (startTC, endTC) )

print( "Results" )
seqs = conn.SequenceDescriptor.get_for_template_with_timecode( path, startTC, endTC )
for s in seqs:
    print("%s %s-%s startF %d endF %d" % (s.get_full_filename_with_d(), s.get_start_timecode(0), s.get_end_timecode(0), s.get_start_frame(), s.get_end_frame()) )
