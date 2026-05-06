# Baselight/Daylight UI for submittng renders to Deadline
#
# Place it in /vol/.support/scripts/ 
#
# Release 2024-04-19

import flapi
import os
import subprocess
import string
import random
import re

DEFAULT_CHUNK_SIZE = 10000
DEFAULT_DEADLINE_GROUP = "Baselight"

conn = flapi.Connection.get()

class MainDialog:
    def __init__(self):
        # Define items to show in dialog
        self.items = [
            flapi.DialogItem(Key="Name", Label="Deadline Job Name", Type=flapi.DIT_STRING, Default = ""),
            flapi.DialogItem(Key="Group", Label="Deadline Group", Type=flapi.DIT_STRING, Default = DEFAULT_DEADLINE_GROUP),
            flapi.DialogItem(Key="Frames", Label="Frames to Render", Type=flapi.DIT_STRING, Default = ""),
            flapi.DialogItem(Key="StaticText", Label="", Type=flapi.DIT_STATIC_TEXT, Default = "(leave empty to render all frames)"),
            flapi.DialogItem(Key="ChunkSize", Label="Frames Per Task", Type=flapi.DIT_INTEGER, IntMin = 1, IntMax=1000000, Default = DEFAULT_CHUNK_SIZE),
        ]

        # Create an empty dictionary for the default settings for the dialog
        self.settings = {
            "Name": "",
            "Group": DEFAULT_DEADLINE_GROUP,
            "Frames": "",
            "ChunkSize": DEFAULT_CHUNK_SIZE
        }

        # Create dialog, which will be shown later
        self.dialog = conn.DynamicDialog.create( 
            "Render with Deadline",
            self.items,
            self.settings
        )

    def show(self):
        # Show the dialog modally
        return self.dialog.show_modal(-200, -25)
    
    def setJobName(self, name):
        self.settings["Name"] = name
        self.dialog.set_settings( self.settings )

class MainMenuItem:
    def __init__(self, message):
        # Save variables in this object instance
        self.message = message

        # Register menu item with the application
        self.menuItem = conn.MenuItem.create( self.message )
        self.menuItem.register( flapi.MENULOCATION_SCENE_MENU )
        self.menuItem.connect( "MenuItemSelected", self.handle_signal )
        
        # Create the dialog, which we will use later
        self.dialog = MainDialog()
    
    def get_deadline_command(self):
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
    
    def duplicate_scene(self, oldScenePath, newSceneName):
        dbhost = oldScenePath.split(':', 1)[0]
        oldSceneName = oldScenePath.split(':')[-1]
        newScenePath = dbhost + ':deadline:jobs'
        
        if not conn.JobManager.job_exists(dbhost, 'deadline'):
            conn.JobManager.create_job(dbhost, 'deadline')
        conn.JobManager.create_folder(dbhost, 'deadline', 'jobs')
        
        scenetoolCmd = 'scenetool'
        if os.path.isfile('/usr/fl/baselight/bin/scenetool'):
            scenetoolCmd = '/usr/fl/baselight/bin/scenetool'
        elif os.path.isfile('/Applications/Baselight/Current/Utilities/Tools/scenetool'):
            scenetoolCmd = '/Applications/Baselight/Current/Utilities/Tools/scenetool'
        elif os.path.isfile('/Applications/Daylight/Current/Utilities/Tools/scenetool'):
            scenetoolCmd = '/Applications/Daylight/Current/Utilities/Tools/scenetool'
        
        # copy scene
        args = [scenetoolCmd, 'copy', oldScenePath, newScenePath]
        print ('> ' + ' '.join(args), flush=True);
        
        result = subprocess.run(args, stderr = subprocess.PIPE)
        try:
            result.check_returncode()
        except:
            print(result.stderr, flush=True)
            return False
        
        # make new scene name unique
        try:
            conn.JobManager.rename_scene(dbhost, 'deadline', 'jobs:' + oldSceneName, 'jobs:' + newSceneName)
        except flapi.FLAPIException as exc:
            print( "Error: %s" % exc, flush = True)
            return False
        
        # recover unsaved deltas
        newScenePath = newScenePath + ':' + newSceneName
        args = [scenetoolCmd, 'branch', 'save', newScenePath, 'Main']
        print ('> ' + ' '.join(args), flush=True)
        
        result = subprocess.run(args, stderr = subprocess.PIPE)
        try:
            result.check_returncode()
        except:
            print(result.stderr, flush=True)
            return False
        
        return newScenePath
        
        
    def handle_signal( self, sender, signal, args ):
        app = conn.Application.get()
        scene = app.get_current_scene()
        print (app.get_current_scene_name(), flush=True)
        
        # Check for Deadline utility
        deadlineCommand = self.get_deadline_command()
        if not deadlineCommand:
            app.message_dialog('Setup Error', "Could not find 'deadlinecommand' utility,\nplease set the DEADLINE_PATH environment variable.", ["OK"])
            scene.release()
            return
        

        # Check that at least one deliverable is enabled, and if any of them generate movie files
        allDisabled = True
        makingMovies = False
        renderSetup = conn.RenderSetup.create_from_scene( scene )
        for i in range(renderSetup.get_num_deliverables()):
            deliverable = renderSetup.get_deliverable(i)
            if not deliverable.Disabled:
                allDisabled = False
                if (deliverable.IsMovie):
                    makingMovies = True
                
        if allDisabled:
            app.message_dialog('Nothing to Render', "You need to enable at least one deliverable in the Render window.", ["OK"])
            scene.release()
            return
        
        curScenePath = scene.get_scene_pathname()
        self.dialog.setJobName(curScenePath.split(':', 1)[1])
        result = self.dialog.show()
        
        if result:
            # "OK" was clicked, submit the render
            
            # Duplicate the scene into the "deadline" job folder
            newScenePath = self.duplicate_scene(curScenePath, curScenePath.split(':')[-1] + '_'  + ''.join(random.choices(string.ascii_lowercase + string.digits, k=4)))
            if not newScenePath:
                app.message_dialog('ERROR', "Failed to copy scene to deadline job folder,\n check Views > Scrips > Log for details.", ["OK"])
                scene.release()
                return
            
            chunkSize = 1 if result['ChunkSize'] < 1 else result['ChunkSize']
            batchName = ""
            
            # Set Frame Range
            frames = result['Frames'].strip()
            if not frames:
                # Frame range is blank, so set for all frames in scene
                frames = "%d-%d" % (scene.get_start_frame(), scene.get_end_frame() - 1)
            
            # If rendering movies we need to set frame ranges to line up with shot breaks
            if makingMovies:
                frameRanges = []
                startFrame = 0
                finalFrame = 0
                            
                m = re.match("^(\d+)-(\d+)$", frames)
                if m:
                    startFrame = int(m.group(1))
                    finalFrame = int(m.group(2))
                else:
                    app.message_dialog('ERROR', "When rending movies you must use a single frame range (e.g. 0-1000)\nor leave 'Frames To Render' blank to render entire scene.", ["OK"])
                    scene.release()
                    return
                
                endFrame = startFrame
                
                frameRanges = []

                # Lookup shots
                nshots = scene.get_num_shots()

                if nshots > 0:
                    shots = scene.get_shot_ids(0, nshots)    
                    totalFrame = 0

                    for shot_ix, shot_inf in enumerate(shots):
                        endFrame = (shot_inf.EndFrame - 1)
                        if endFrame < startFrame:
                            continue
                        totalFrame += endFrame - shot_inf.StartFrame
                        if endFrame >= finalFrame:
                            break
                        if totalFrame >= chunkSize:
                            frameRanges.append(f"{startFrame}-{endFrame}")
                            startFrame = endFrame + 1
                            totalFrame = 0
    
                    if totalFrame != 0:
                        frameRanges.append(f"{startFrame}-{endFrame}")
                    chunkSize = finalFrame + 1
                    batchName = result['Name'] + " Batch"
            
            
            params = {
                "Name" : result['Name'],
                "BatchName" : batchName,
                "Group" : result['Group'],
                "Frames" : frames,
                "ChunkSize" : chunkSize,
                "ScenePath" : newScenePath
            }
            
            tasks = []
            if makingMovies:
                for frames in frameRanges:
                    params['Frames'] = frames
                    params['Name'] = result['Name'] + ' ' + frames
                    tasks.append(flapi.QueueOpTask({"Type": "Submit", "Desc": "Submitting Deadline render job " + frames, "Params": dict(params), "Weight": 1.0}))
            else:
                tasks.append(flapi.QueueOpTask({"Type": "Submit", "Desc": "Submitting Deadline render job 1", "Params": params, "Weight": 1.0}))
            
            # Submitting tasks to queue
            qm = conn.QueueManager.create_local()
            opid = qm.new_operation( "DeadlineOp", "Submit to Deadline: " + result['Name'], {}, tasks, None )
            
            qm.release()
        
        scene.release()
            
                


mainMenuItem1 = MainMenuItem( "Render with Deadline" ) 