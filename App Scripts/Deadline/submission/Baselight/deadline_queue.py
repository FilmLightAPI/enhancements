# Deadline Queue submission manager for Baselight/Daylgiht
#
# Place it in /vol/.support/scripts/ 
#
# Release 2024-04-07

import flapi
import os
import sys
import subprocess

#######################################################################
# get_deadline_command()
#
# Get full path to deadlinecommand utility

def get_deadline_command():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        pass
    
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists("/Users/Shared/Thinkbox/DEADLINE_PATH"):
        with open("/Users/Shared/Thinkbox/DEADLINE_PATH") as f:
            deadlineBin = f.read().strip()
    
    # Default fall-back
    if deadlineBin == "" and  os.path.exists("/opt/Thinkbox/Deadline10/bin"):
        deadlineBin = "/opt/Thinkbox/Deadline10/bin"
        
    if not deadlineBin:
        return ""
    else:
        return os.path.join(deadlineBin, "deadlinecommand")



#######################################################################
# Operation
#
# Class used to track the state of the current operation

class Operation: 
    in_update_tasks = False         # Flag indicating whether update_tasks is running
    current = None                  # The current operation

    def __init__(self, opid):
        self.opid = opid            # ID in QueueManager for operation
        self.working = False        # Waiting for a task to finish?
        self.task = None            # Current task of the operation


#######################################################################
# handle_tasks()
#
# This function is called repeatedly by handle_timer_tick() to execute 
# the tasks in the Frame.io Operation.
#
# Outer function uses a flag in_handle_tasks to 

def handle_tasks():
    cur = Operation.current
    opid = cur.opid
    task = cur.task

    ##################################################################################
    # Update based on the current state of the operation

    # Check for cancelation
    opstatus = qm.get_operation_status( opid )
    if opstatus == None:
        print("Deadline submission removed from queue.", flush=True)
        Operation.current = None
        return
    elif opstatus.Status == flapi.OPSTATUS_STOPPED:
        qm.add_operation_log( opid, flapi.QUEUELOGTYPE_WARN, "Deadline submission stopped", "" )
        Operation.current = None
        return

    #--------------------------------------------
    if not cur.working:
        # Start processing this operation
        task = qm.get_next_task( opid )
        if task is None:
            # Operation has no more tasks
            qm.add_operation_log( opid, flapi.QUEUELOGTYPE_INFO, "Operation complete", "" )
            Operation.current = None
            return

        cur.task = task
        cur.working = True
        
        filename1 = '/tmp/bl_job.job'
        filename2 = '/tmp/bl_plugin.job'
                
        # Create job info file.
        f = open(filename1, 'w')
        f.write( "Plugin=Baselight\n" )
        f.write( "Name=%s\n" % task.Params['Name'] )
        f.write( "Group=%s\n" % task.Params['Group'] )
        f.write( "Frames=%s\n" % task.Params['Frames'] )
        if task.Params['BatchName']:
            f.write( "BatchName=%s\n" % task.Params['BatchName'] )
        f.write( "ChunkSize=%s\n" % task.Params['ChunkSize'] )
        f.close()
        
        # Create plugin info file.
        f = open(filename2, 'w')
        f.write("ScenePath=%s\n" % task.Params['ScenePath'] )
        f.close()

        qm.add_operation_log( opid, flapi.QUEUELOGTYPE_INFO, task.Desc, "" )

        stdoutPipe = subprocess.PIPE
        proc = subprocess.Popen([deadlineCommand, filename1, filename2], stdout=stdoutPipe, startupinfo=None, env=None)
        output = ""
        output = proc.stdout.read()

        # Relatively safe manner in which to ensure we get a 'str' back from deadlinecommand
        if not isinstance(output, str):
            output = output.decode()
        
        for line in output.split('\n'):
            if line and not line.isspace():
                if line.startswith('Error'):
                    qm.add_operation_log( opid, flapi.QUEUELOGTYPE_FAIL, line, "" )
                else:
                    qm.add_operation_log( opid, flapi.QUEUELOGTYPE_INFO, line, "" )
        
        # Cleanup tmp files
        os.remove(filename1)
        os.remove(filename2)

        # This task is done
        qm.set_task_done( task.ID, task.Seq, "Done with %s" % task.Desc )
        cur.working = False

#######################################################################
# update_tasks
#
# This method is called by:
#
#  1. the QueueOpsChanged signal whenever the state of the queue changes
#
#  2. the TimerTick signal, when the Timer is enabled
#
# If there is a current operation, it will update the progress of
# the operation.
#
# It checks for a new DeadlineOp if we are not already processing
# an operation.
#
# If there is no current operation, it will stop the timer.
#

def update_tasks( sender, signal, args ):

    # Prevent re-entrancy in update_tasks, as it can be called from
    # two different signals, and signals may be delivered whilst we
    # are in the middle of this method.
    if Operation.in_update_tasks:
        return

    Operation.in_update_tasks = True

    if Operation.current:
        handle_tasks()        

    if Operation.current is None:
        opid = qm.get_next_operation_of_type("DeadlineOp", 1)
        if opid:
            print( f"New Deadline submission operation {opid}", flush=True )
            Operation.current = Operation(opid)
            if not timer.is_started():
                timer.start()
        elif timer.is_started():
            print( "No pending Deadline submission operation, stopping timer", flush=True )
            timer.stop()
    
    Operation.in_update_tasks = False



#######################################################################
# Initialisation
#
# This code is executed when the Deadline Queue script is loaded by flapid

conn = flapi.Connection.get()
deadlineCommand = get_deadline_command()
if not deadlineCommand:
    print ("ERROR: Could not find 'deadlinecommand' utility, please set the DEADLINE_PATH environment variable.", flush=True)
    sys.exit(1)

# Subscribe to the QueueManager QueueOpsChanged signal
# This will start our timer whenever a new operation is added to the queue
qm = conn.QueueManager.create_local()
qm.connect( "QueueOpsChanged", update_tasks )
qm.connect( "QueueOpStatusChanged", update_tasks )
qm.enable_updates()

# Create a timer which will handle updating the state machine for the current operation
# We start the timer to check for the operation on startup.
# If there are no operations, the timer will turn itself off.
timer = conn.Timer.create( 500 ) # every 500ms
timer.connect( "TimerTick", update_tasks )
timer.start()