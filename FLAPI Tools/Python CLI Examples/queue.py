import flapi
import sys

conn = flapi.Connection("localhost")

conn.connect()

qm = conn.QueueManager.create_local()

ids  = qm.get_operation_ids()
for id_ in ids:
    print( "Operation %d" % id_ )

    op = qm.get_operation( id_ )
    status = qm.get_operation_status( id_ )
    log = qm.get_operation_log( id_ )

    print( "  Desc:  %s" % op.Description  )

    print( "  Status: %s"  % status.Status )
    print( "  Progress: %.1f" % (status.Progress * 100.0) )
    print( "  Last Message:  %s" %  status.ProgressText )

    print( "  Log:" )
    for l in log:
        print( "   %s %s: %s" % (l.Time, l.Message, l.Detail) )

