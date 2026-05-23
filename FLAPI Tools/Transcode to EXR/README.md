# Transcode to EXR

Transcode a movie file to an ACES EXR sequence.

This is an example of transcoding with a temporary scene in memory (no need to create a job/scene in a Postgres database).
 
## How To Use

Ensure the FLAPI module is part of your Python enviroment (see [FLAPI documnetation](https://www.filmlight.ltd.uk/support/documents/filmlightapi/docs_api.php)). In teminal run:

`transcode_to_exr <path-to-source-movie> <dest-folder>`

e.g.

```
$ ./transcode_to_exr /vol/images/A013C011_171025.mxf /vol/images/vfx_pulls/A013C011_171025

[flapid]: Local FLOP worker enabled
[flapid]: Listening on port 63793
[flapid]: Client 127.0.0.1:63795 connected
Create RenderSetup for Scene
[flapid]: Creating RenderProcessor
{'Status': 'Starting', 'Error': None, 'Total': 481, 'Complete': 0, 'Remaining': 481, 'Failed': 0, 'Progress': 0.0, 'ProgressMessage': None}
{'Status': 'Running', 'Error': None, 'Total': 481, 'Complete': 0, 'Remaining': 481, 'Failed': 0, 'Progress': 0.0, 'ProgressMessage': 'Make directory /vol/images/vfx_pulls/A013C011_171025'}
{'Status': 'Running', 'Error': None, 'Total': 481, 'Complete': 18, 'Remaining': 463, 'Failed': 0, 'Progress': 0.037422, 'ProgressMessage': 'Frame 17: render_0000017.exr'}
{'Status': 'Running', 'Error': None, 'Total': 481, 'Complete': 154, 'Remaining': 327, 'Failed': 0, 'Progress': 0.320166, 'ProgressMessage': 'Frame 153: render_0000153.exr'}
{'Status': 'Running', 'Error': None, 'Total': 481, 'Complete': 460, 'Remaining': 21, 'Failed': 0, 'Progress': 0.956341, 'ProgressMessage': 'Frame 459: render_0000459.exr'}
{'Status': 'Done', 'Error': None, 'Total': 481, 'Complete': 481, 'Remaining': 0, 'Failed': 0, 'Progress': 1.0, 'ProgressMessage': None}
[flapid]: Client 127.0.0.1:63795 disconnected
[flapid]: Destroying RenderProcessor
```