import flapi
import time
import sys

if len(sys.argv) < 2:
    print( "No scene specified" )
    print( "Usage: %s host:job:scene" % sys.argv[0] )
    exit(1)

# Connect o  FLAPI
conn = flapi.Connection()
try:
    conn.connect()
except flapi.FLAPIException as ex:
    print( "Cannot connect to FLAPI: %s" % ex )
    sys.exit(1)

# Open the given scene
scene_path = conn.Scene.parse_path( sys.argv[1]  )

try:
    scene = conn.Scene.open_scene( scene_path, { flapi.OPENFLAG_READ_ONLY } )
except flapi.FLAPIException as ex:
    print( "Error loading scene: %s" % ex )
    sys.exit(1)

# Lookup names for each metadata item
tc_keys = {
    "srctc",
    "rectc"
}

md_keys = { 
    "filename", 
    "clip", 
    "tape", 
    "comment"
}

md_names = {}
mddefns = scene.get_metadata_definitions()
for k in tc_keys | md_keys:
    defns = [x for x in mddefns if x.Key == k]
    if defns and len(defns) > 0:
        md_names[k] = defns[0].Name

cat_names = {}
cat_keys = scene.get_strip_categories()
for k in cat_keys:
    cat_defn = scene.get_category(k)
    cat_names[k] = cat_defn.Name

# Lookup shots
nshots = scene.get_num_shots()
print( "Found %d shot(s)" % nshots )

if nshots > 0:
    shots = scene.get_shot_ids(0, nshots)
    for shot_ix, shot_inf in enumerate(shots):
        print("Shot %d:" % shot_ix)
        
        # Get Shot object for shot with the given ID
        shot = scene.get_shot(shot_inf.ShotId)
        
        # Get start/end source and record timecode metadata as native Timecode objects
        # using the get_metadata() method
        shot_tcs = shot.get_metadata( tc_keys )
        for tc_key, tc_val in shot_tcs.items():
            print("%15s: %s - %s" % (md_names[tc_key], shot_tcs[tc_key][0], shot_tcs[tc_key][1]))
        
        # Get other shot metadata in String form using the get_metadata_strings() method
        shot_md = shot.get_metadata_strings(md_keys)
        for md_key, md_val in shot_md.items():
            print("%15s: %s" % (md_names[md_key], md_val))

        # Get marks in shot
        mark_ids = shot.get_mark_ids()
        if len(mark_ids) > 0:
            print( "%15s:" % "Marks" )
            for ix,m in enumerate(mark_ids):
                mark = shot.get_mark(m)
                print( "%20d: Frame %d Type '%s' Message '%s'" % (
                        ix,
                        mark.get_record_frame(),
                        mark.get_category(),
                        mark.get_note_text()
                    )
                )
                mark.release()

        # Get shot categories
        categories = shot.get_categories()
        if len(categories) > 0:
            print("%15s: %s" % ("Categories", set(map(lambda c: cat_names.get(c), categories ) )) )

        # Release Shot object
        shot.release()

scene.close_scene()
scene.release()