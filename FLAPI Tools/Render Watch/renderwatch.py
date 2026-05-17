from datetime import datetime
from email.message import EmailMessage
from smtplib import SMTP
import flapi
import json
import os
import platform
import time

conn = flapi.Connection.get()
qm = conn.QueueManager.create_local()

SEND_EMAILS = True
smtp_server = "smtp.mycompany.com"
smtp_port = 25
smtp_use_starttls = False
smtp_username = None
smtp_password = None
smtp_sender = "renderwatch@mycompany.com"
smtp_recipients = [ "renders@mycompany.com" ]

# ActiveRender used to track the state of an operation in the queue
class ActiveRender:
    def __init__(self, desc):
        self.desc = desc 
        self.lastUpdateTime = 0.0
        self.lastStatus = None
        self.lastProgress = 0.0
        self.lastProgressText = None
        self.hung = False

# Map from operation ID to ActiveRender
activeRenders = {}

# This method will send an email
def send_email(subject:str, body:str):
    if not SEND_EMAILS:
      return
    try:
        with SMTP(smtp_server, port=smtp_port) as smtp:
            msg = EmailMessage()
            msg["From"] = smtp_sender
            msg["To"] = ", ".join(smtp_recipients)
            msg["Subject"] = subject
            msg.set_content(body)

            if smtp_use_starttls:
                smtp.starttls()
            smtp.ehlo_or_helo_if_needed()
            if smtp_username:
                smtp.login( smtp_username, smtp_password )
            smtp.send_message( msg )
    except Exception as e:
        print( f"Failed to send email: {e}", flush=True )

# Send notification that a render crash
def notify_render_crashed(opid:int, ar:ActiveRender):
    dtnow = datetime.now().strftime( "%H:%M:%S on %A %d-%m-%Y")

    msg = f"Render '{ar.desc.Description}' on '{platform.node()}' crashed at {dtnow}.\r\n"

    send_email( f"Render crashed: {ar.desc.Description}", msg)

# Send notification that a render failed
def notify_render_failed(opid:int, ar:ActiveRender):
    dtnow = datetime.now().strftime( "%H:%M:%S on %A %d-%m-%Y")

    msg = f"Render '{ar.desc.Description}' on '{platform.node()}' failed at {dtnow}.\r\n"

    log = qm.get_operation_log(opid)
    msg = msg + "\r\n"
    msg = msg + "Log:\r\n"
    for l in log:
        msg = msg + f"{l.Time}: {l.Message}: {l.Detail}"
        if l.Frame is not None and l.Frame >= 0:
            msg = msg + f", Frame {l.Frame}"
        msg = msg + "\r\n"

    send_email( f"Render failed: {ar.desc.Description}", msg )

# Send notification that a render hung
def notify_render_hung(opid:int, ar:ActiveRender):
    dtnow = datetime.now().strftime( "%H:%M:%S on %A %d-%m-%Y")
    msg = (
        f"Render '{ar.desc.Description}' on '{platform.node()}' hung at {dtnow}.\r\n"
        f"The services have been restarted.\n"
    )

    send_email( f"Render hung: {ar.desc.Description}", msg )

# Send notification that a render completed successfully
def notify_render_done(opid:int, ar:ActiveRender):
    dtnow = datetime.now().strftime( "%H:%M:%S on %A %d-%m-%Y")
    msg = (
        f"Render '{ar.desc.Description}' on '{platform.node()}' completed at {dtnow}.\r\n"
    )

    send_email( f"Render complete: {ar.desc.Description}", msg )

# Dump log for a render to file
def dump_render_log( dumpdir, opid ):
    with open( f"{dumpdir}/renderlog_{opid}", "w") as f:
        print( f"Saving operation log for {opid}" )
        log = qm.get_operation_log( opid )
        for l in log:
            msg = f"{l.Time}: {l.Message}: {l.Detail}"
            if l.Frame is not None and l.Frame >= 0:
                msg = msg + f", Frame {l.Frame}"
            msg = msg + "\n"
            f.write( msg )


# Dump diagnostic information about a render which has hung
def dump_render_status( opid, prev_opid ):


    # Dump the log for the previous operation


    # Lookup the renderworker process
    try:
        with os.popen("/usr/fl/server-scripts/getrenderport") as p:
            grp = json.load(p)
    except:
        print( "Cannot find pid/port informatino for renderworker", flush=True )
        return

    # Create dump directory
    try:
        dtnow = datetime.now().strftime("%Y%m%d_%H%M%S")
        dumpdir = f"/tmp/fl-queue-dump-{dtnow}"
        os.mkdir(dumpdir)
    except Exception as e:
        print( f"Failed to create dir {dumpdir}: {e}", flush=True )
        return

    print( f"Dumping log to {dumpdir}", flush=True )
    
    # Copy prerenderworker console.txt
    try:
        os.system( f"cp /usr/fl/log/$(hostname -s)-prerenderworker/console.txt {dumpdir}/prerenderworker-console.txt")
    except Exception as e:
        print( f"Failed to copy prerenderworker console.txt to {dumpdir}: {e}", flush=True )
        return

    # Copy renderworker console.txt
    try:
        os.system( f"cp /usr/fl/log/$(hostname -s)-renderworker/console.txt {dumpdir}/renderworker-console.txt")
    except Exception as e:
        print( f"Failed to copy renderworker console.txt to {dumpdir}: {e}", flush=True )
        return
    
    # Dump RC queues
    try:
        os.system( f"curl -s http://localhost:{grp['port']}/RC/rc_print_queues > {dumpdir}/rc_print_queues" )
        os.system( f"curl -s http://localhost:{grp['port']}/RC/rc_print_all_renders_with_str > {dumpdir}/rc_print_all_renders_with_str" )
    except:
        print( "Failed to dump RC queues for renderworker", flush=True )
        return

    # Dump threads for renderworker process
    try:
        os.system( f"gdb -p {grp['pid']} -ex 'set pagination off' -ex 'thread apply all bt' -ex 'detach' -ex 'quit' > {dumpdir}/gdb_renderworker_threads")
    except:
        print( "Failed to dump backtrace for renderworker", flush=True )
        return
    
    dump_render_log( dumpdir, opid )
    if prev_opid is not None:
        dump_render_log( dumpdir, prev_opid )

# Restart render services to get the operation running again
def restart_render_services():
    print( "Restarting services", flush=True )
    os.system("sudo fl-service restart prerender")
    os.system("sudo fl-service restart render")

# Check the status of the given operation ID
def check_op(opid, prev_opid):

    # Fetch information on the operation
    opstatus = qm.get_operation_status(opid)
    if opstatus.Status == flapi.OPSTATUS_STOPPED:
        # Someone has stopped this render, ignore it
        return

    # Fetch ActiveRender status
    ar = activeRenders.get(opid, None)
    if ar is None:
        print( f"New operation {opid}", flush=True )
        opinfo = qm.get_operation(opid)
        ar = ActiveRender(opinfo)
        activeRenders[opid] = ar

    # Check if operation has changed state
    if ar.lastStatus != opstatus.Status:
        if opstatus.Status == flapi.OPSTATUS_CRASHED:
            print( f"Operation {opid} crashed", flush=True )
            # Operation has changed
            notify_render_crashed(opid, ar)

        elif opstatus.Status == flapi.OPSTATUS_DONE:
            print( f"Operation {opid} done", flush=True )
            if opstatus.Errors > 0:
                notify_render_failed(opid, ar)
            else:
                notify_render_done(opid, ar)

        ar.lastStatus = opstatus.Status
        ar.lastUpdateTime = time.time()

    # Operation is active, check if it has hung
    elif opstatus.Status == flapi.OPSTATUS_ACTIVE:
        if( (ar.lastProgress != opstatus.Progress) or 
            (ar.lastProgressText != opstatus.ProgressText) 
            ):
            # Render progress has changed
            ar.lastProgress = opstatus.Progress
            ar.lastProgressText = opstatus.ProgressText
            ar.lastUpdateTime = time.time()
        else:
            # Render progress has not changed
            dt = time.time() - ar.lastUpdateTime
            if (dt > 60.0) and not ar.hung:
                ar.hung = True

                print( f"Operation {opid} hung", flush=True )
                notify_render_hung(opid, ar)

                dump_render_status(opid, prev_opid)

                restart_render_services()

# This method is called by the timer each time it ticks
def handle_timer_tick( sender, sig, args ):

    # Get all the operations in the queue
    opids = qm.get_operation_ids()

    # Check status of each operation
    prev_opid = None
    for opid in opids:
        check_op(opid, prev_opid)
        prev_opid = opid

    # Remove records for renders that are no longer in the queue
    ids_to_delete = []
    for opid in activeRenders.keys():
        if opid not in opids:
            ids_to_delete.append(opid)

    for opid in ids_to_delete:
        print( f"Operation {opid} has been deleted", flush=True )
        del activeRenders[opid]

# Initialise the list of current operations
# This ensure we only pick up on new operations created after the script started
opids = qm.get_operation_ids()
for opid in opids:
    opstatus = qm.get_operation_status(opid)
    opinfo = qm.get_operation(opid)
    ar = ActiveRender(opinfo)
    ar.lastStatus = opstatus.Status
    activeRenders[opid] = ar

# Timer fires every 5 seconds
timer = conn.Timer.create( 5000 )
timer.connect( "TimerTick", handle_timer_tick )
timer.start()
