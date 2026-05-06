# Release 2024-04-07

import os
import sys
import flapi

from Deadline.Plugins import DeadlinePlugin, PluginType
from Deadline.Scripting import SystemUtils

from FranticX.Processes import ManagedProcess

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return BaselightPlugin()

######################################################################
## This is the function that Deadline calls to clean up any
## resources held by the Plugin.
######################################################################
def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the Baselight plugin.
######################################################################
class BaselightPlugin( DeadlinePlugin ):

    def __init__( self ):
        super().__init__()
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
        self.flapiconn = None

    def Cleanup( self ):
        del self.InitializeProcessCallback
        del self.StartJobCallback
        del self.RenderTasksCallback
        del self.EndJobCallback        

    # Called By Deadline to initalize the process.
    def InitializeProcess( self ):
        self.LogInfo( "Baselight Plugin Initializing..." )

        self.SingleFramesOnly = False
        ## self.StdoutHandling = True
        self.PluginType = PluginType.Advanced

        ## self.AddStdoutHandlerCallback( "\*\*\* Error: (.*)" ).HandleCallback += self.HandleGenericError

    ## Called by Deadline when the job is first loaded.
    def StartJob( self ):
        self.LogInfo( "Baselight job starting..." )
        
        self.flapiconn = flapi.Connection("localhost")
        try:
            self.flapiconn.connect()
        except flapi.FLAPIException as ex:
            self.FailRender( "Cannot connect to FLAPI: %s" % ex )
        
        self.LogInfo( "Running {Product} {Major}.{Minor}.{Build} ".format(**self.flapiconn.Application.get_application_info()) )
        # TODO Check that Render service is running 


    ## Called by Deadline when a task is to be rendered.
    def RenderTasks( self ):
        # Open the scene
        scene_path = self.flapiconn.Scene.parse_path( self.GetPluginInfoEntryWithDefault( "ScenePath", "" ) )
        try:
          scene = self.flapiconn.Scene.open_scene( scene_path, { flapi.OPENFLAG_READ_ONLY } )
        except flapi.FLAPIException as ex:
          self.FailRender( "Error loading scene: %s" % ex )

        # Create RenderSetup
        renderSetup = self.flapiconn.RenderSetup.create_from_scene( scene )

        # Check that at least one deliverable is enabled
        if 0 not in [renderSetup.get_deliverable(i).Disabled for i in range(renderSetup.get_num_deliverables())]:
          self.FailRender("No render deliverables are enabled in this scene. Enable at least one in the Render View in the Baselight UI and save the scene.")

        # Connect to Queue Manager
        qm = self.flapiconn.QueueManager.create_local()
        
        # Set frames to render
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if (startFrame != 0 or endFrame != 0):
            renderSetup.set_frames( [ flapi.FrameRange({'Start': startFrame, 'End': endFrame + 1}) ] )

        # Submit job to Baselight render queue and get the new operation ID
        deadlineJob = self.GetJob()
        opinfo = renderSetup.submit_to_queue( qm, "Deadline: %s" % deadlineJob.JobName)
        opId = opinfo.ID

        self.LogInfo( "Created operation id %d" % opId )
        if opinfo.Warning != None:
          self.LogWarning( opinfo.Warning )

        renderSetup.release()
        scene.close_scene()
        scene.release()
        
        lastLogLine = 0
        
        # While loop to check status of locally running Baselight queue.
        while( True ):
            if self.IsCanceled():
                qm.pause_operation( opId )
                qm.release()
                self.FailRender( "Received 'cancel task' command from Deadline." )
                
            opstat = qm.get_operation_status( opId )
            self.SetProgress( opstat.Progress * 100 )
            
            log = qm.get_operation_log( opId )
            logLength = len(log)
            if logLength > lastLogLine:
                for l in log[lastLogLine:]:
                    message = ""
                    if l.Frame > -1:
                        message = "%s: %s" % (l.Message, l.Detail)
                    else:
                        message = "%s: [%i] %s" % (l.Message, l.Frame, l.Detail)
                    if l.Type != flapi.QUEUELOGTYPE_INFO:
                        self.LogWarning(message)
                    else:
                        self.LogInfo(message)
                lastLogLine = logLength
            
            if opstat.Status == "Done":
                break
            if opstat.Status == "Stopped":
                qm.release()
                self.FailRender( "Baselight render queue was stopped" )

            # Sleep for 1 second between loops.
            SystemUtils.Sleep( 1000 )
        
        # Check final status of render
        opstat = qm.get_operation_status( opId )
        if (opstat.ProgressText == 'Render failure' or opstat.Errors > 0):
            qm.release()
            self.FailRender("Render failure")
        
        qm.release()

    ## Called by Deadline when the job is unloaded.
    def EndJob( self ):
        self.LogInfo( "Baselight job finished." )