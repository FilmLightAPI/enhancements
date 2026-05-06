# Release 2024-04-07

from __future__ import absolute_import
from System.Collections.Specialized import StringCollection
from System.IO import Path, StreamWriter, File, Directory
from System.Text import Encoding

from Deadline.Scripting import RepositoryUtils, FrameUtils, ClientUtils, PathUtils, StringUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from ThinkboxUI.Controls.Scripting.ButtonControl import ButtonControl

########################################################################
## Globals
########################################################################
scriptDialog = None  # type: DeadlineScriptDialog
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    # type: () -> None
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Baselight Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Baselight' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "                   Job Description                   ", 0, 0, colSpan=4 )
 
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 2, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 2, 1 )

    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "                   Baselight Options                   ", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Scene", 1, 0, "Scene to render in 'Host:Job:Scene' format.", False )
    scriptDialog.AddControlToGrid( "ScenePath", "TextControl", "host:job:scene", 1, 1, colSpan=3)
    
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Frames", 2, 0, "Frames to render, can be 'All' or a list of single frames or ranges e.g. '1-5,103,220-225'", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 10000, 1, 1000000, 0, 1, 3, 1 )
    
    scriptDialog.EndGrid()

    scriptDialog.EndTabPage()
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("GroupBox","ScenePath","FramesBox","ChunkSize")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
        
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    # type: () -> str
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "BaselightSettings.ini" )
    
def SubmitButtonPressed(*args):
    # type: (*ButtonControl) -> None
    global scriptDialog
        
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "baselight_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Baselight" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Frames=%s" % scriptDialog.GetValue( "FramesBox" ) )
    writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "baselight_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine( "ScenePath=%s" % scriptDialog.GetValue( "ScenePath" ) )

    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
