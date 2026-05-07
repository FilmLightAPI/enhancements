import flapi

c = flapi.Connection("localhost")

c.connect()

jobs = c.JobManager.get_jobs("localhost")

print( "Found %d jobs on localhost:" % len(jobs) )
for j in jobs:
    print( "  %s" % j )

print( "Done" )

