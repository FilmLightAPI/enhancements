from enum import IntEnum
from datetime import datetime
import time
import flapi
import subprocess

#######################################################################
# OpState
#
# Possible states for the Operation object

class OpState(IntEnum):
    READY = 1
    DELETING = 2
    CANCELING = 3
    DONE = 4

#######################################################################
# DOGServer
#
# This is the main state holder for the Delete Old Galleries process
#
# This connects to the QueueManager to be notified of new operations,
# and creates a timer to monitor active operations.

class DOGServer:
    def __init__(self):
        self.conn = flapi.Connection.get()

        self.in_update_tasks = False        # Flag indicating whether update() is running
        self.currentOp = None               # The current operation

        # Enable updates from the QueueManager
        # Subscribe to the QueueManager QueueOpsChanged signal
        # This will start our timer whenever a new operation is added to the queue
        self.qm = self.conn.QueueManager.create_local()
        self.qm.enable_updates()
        
        # Listen to QueueOpStatusChanged to catch operations which are added
        self.qm.connect( "QueueOpsChanged", lambda sender, signal, args: self.queue_changed() )

        # Listen to QueueOpStatusChanged to catch operations which are paused/resumed
        self.qm.connect( "QueueOpStatusChanged", lambda sender, signal, args: self.queue_status_changed(args) )
        
        # Create a timer which will handle updating the state machine for the current operation
        # We start the timer to check for the operation on startup.
        # If there are no operations, the timer will turn itself off.
        self.timer = self.conn.Timer.create( 500 ) # every 500ms
        self.timer.connect( "TimerTick", lambda sender, signal, args: self.timer_tick() )
        
        print( "Watching for Delete Old Galleries requests", flush=True)

        # Do an initial update to check for tasks in queue
        self.update()

    def queue_changed(self):
        self.update()
    
    def queue_status_changed(self, opid):
        self.update()

    def timer_tick(self):
        self.update()

    def update(self):
        # Prevent reentrancy in update_tasks, as it can be called from
        # three different signals, and signals may be delivered while in
        # the middle of this method.        
        if self.in_update_tasks:
            return

        self.in_update_tasks = True

        # Update the current operation.
        if self.currentOp:
            try:
                self.currentOp.update()
            except Exception as ex:
                self.currentOp.abort( str(ex) )

            # If the op is complete, clear the current operation
            if self.currentOp.state == OpState.DONE:
                print( "Delete Old Galleries process complete.", flush=True)
                self.currentOp = None

        if self.currentOp is None:
            opid = self.qm.get_next_operation_of_type("DOG", 0)
            if opid is not None:
                print( f"Processing Delete Old Galleries op {opid}", flush=True)

                self.currentOp = DOGRun(self, opid)
                self.timer.start()
            else:
                # No operation found
                self.timer.stop()
        
        self.in_update_tasks = False


#######################################################################
# DOGRun
#
# Class used to track the state of the current Gallery Deletion operation

class DOGRun: 

    def __init__(self, DOGServer, opid):
        self.conn = DOGServer.conn
        self.qm = DOGServer.qm
        self.opid = opid            # ID in QueueManager for operation
        self.params = None          # Operation-wide parameters
        self.host = None                 # Postgres Database host
        self.job = None                  # Gallery job folder
        self.cutoff = None               # Datetime cutoff for deletion
        self.total_scenes = 0       # Total number of scenes to check
        self.scene_count = 0        # Number of scenes checked so far
        self.deleted_scenes = 0     # Number of deleted scenes
        self.deleted_folders = 0    # Number of deleted folders
        self.progress_timer = 0     # Time since last progress update
        self.task = None            # Current task of the operation
        self.state = OpState.READY  # Current state of the operation
        
        self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Operation starting", "" )
    
    # Check for manual cancelation and upgrade progress bar
    def progress_update(self):
        # No need to update more than every 2 seconds
        if (time.time() - self.progress_timer) > 2:
            # Check if our operation has been stopped
            opstatus = self.qm.get_operation_status( self.opid )
            if opstatus.Status != flapi.OPSTATUS_ACTIVE:
                print( f"Delete Gallery operation {opstatus.Status}", flush=True )
                print( f"Canceling {self.opid}", flush=True )
                self.state = OpState.CANCELING
                return
            
            # Upgate progress
            progress = float(self.scene_count) / float(self.total_scenes)
            self.qm.set_task_progress( self.task.ID, self.task.Seq, progress)
            self.progress_timer = time.time()
    
    # Core function to recursively check scene in the baselight gallery,
    # delete ones not modified since the cutoff date, and deletes empty subfolders
    def check_folder(self, folder):
        if self.state == OpState.CANCELING:
            return
        try:
            scenes = self.conn.JobManager.get_scenes(self.host, self.job, folder)
        except Exception as ex:
            self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_WARN, f"Unable to get scenes in folder: {folder}", f"{ex}")
            return
    
        # Check all the scenes in the job
        for scene in scenes:
            self.scene_count += 1
            scenename = scene
            if not folder == "":
                scenename = folder + ':' + scene
            try:
                scene_info = self.conn.JobManager.get_scene_info(self.host, self.job, scenename)
                dt = datetime.strptime(scene_info.ModifiedDate, "%Y-%m-%d %H:%M")
                if dt < self.cutoff:
                    self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Deleting scene", f"{scenename}" )
                    self.conn.JobManager.delete_scene(self.host, self.job, scenename, 1)
                    self.deleted_scenes += 1
                else:
                    # print(f"keeping: {scenename} {dt}")
                    pass
                self.progress_update()
                if self.state == OpState.CANCELING:
                    return
            except Exception as ex:
                self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_WARN, f"Unable to process scene: {scenename}", f"{ex}")
    
        # check any sub-folders
        # recursion is disabled on JobManager.get_folders() because it returns the highest
        # level folders first and we need to be sure to vist the lowest level folders first
        folders = self.conn.JobManager.get_folders(self.host, self.job, folder, False)
        for new_folder in folders:
            self.check_folder(new_folder)
    
        # Check to see if this folder is now empty, if so delete it
        if not folder == "":
            try:
                scenes = self.conn.JobManager.get_scenes(self.host, self.job, folder)
                folders = self.conn.JobManager.get_folders(self.host, self.job, folder)
                if len(scenes) == 0 and len(folders) == 0:
                    self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Deleting empty folder", f"{folder}" )
                    self.conn.JobManager.delete_folder(self.host, self.job, folder)
                    self.deleted_folders += 1
            except Exception as ex:
                self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_WARN, f"Unable to process folder: {folder}", f"{ex}")
                
    # Setup this operation, check how many scenes we have to check
    # then start the process of checking them all
    def begin(self):
        self.state = OpState.DELETING
        self.params = self.qm.get_operation_params( self.opid )
        self.host = self.params['host']
        self.job = self.params['job']
        self.cutoff = datetime.fromisoformat(self.params['cutoff'])
            
        # Start processing this operation
        task = self.qm.get_next_task( self.opid )
        if task is None:
            # Operation no tasks
            self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Operation complete", "" )
            self.state = OpState.DONE
            return

        self.task = task
      
        try:
            result = subprocess.run(f"bl-lsscenes {self.host}:{self.job} | wc -l", shell=True, capture_output=True, text=True, check=True)
            self.total_scenes = int(result.stdout.strip())
            self.scene_count = 0 
            self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Summary", f"Checking {self.total_scenes} scenes" )
        except Exception as ex:
            self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_FAIL, "Failed counting number of scenes in gallery", f"{ex}" )
            self.qm.set_task_failed( self.task.ID, self.task.Seq, "Error", "Failed counting number of scenes in gallery" )
            self.state = OpState.DONE
            return
        
        self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Starting Gallery Cleanup", "" )
        
        self.progress_timer = time.time()
        self.check_folder("")
        
        self.qm.add_operation_log( self.opid, flapi.QUEUELOGTYPE_INFO, "Summary", f"Deleted {self.deleted_scenes} scenes and {self.deleted_folders} folders." )
        self.qm.set_task_done( self.task.ID, self.task.Seq, f"Done with {self.task.Desc}" )
        self.state = OpState.DONE

    # Update
    # Process the state for this operation
    def update(self):
        if self.state == OpState.READY:
            self.begin()


    # abort(error)
    #
    # Abort this operation
    def abort(self, error):
        if self.task is not None:
            self.qm.set_task_failed( self.task.ID, self.task.Seq, "Error", error )
        self.state = OpState.DONE
