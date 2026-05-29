# List Mattes Used

Generate a list of EXR matte channels used in a scene.

## How To Use

Ensure the FLAPI module is part of your Python enviroment (see [FLAPI documnetation](https://www.filmlight.ltd.uk/support/documents/filmlightapi/docs_api.php)). In teminal run:

`python3 getMattes.py <host:job:scene>`

e.g.

```
$ python3 getMattes.py localhost:someshow:trailer_v1

Found 26 shot(s)
Shot 1: BARNES_163_4.%.6F.exr
Channels: {'char_allChars.R', 'charMatte3.R', 'surfaceColor.R'}
Shot 3: BARNES_834_1.%.6F.exr
Channels: {'depth.Z', 'charMatte2.B'}
Shot 8: BARNES_836_2.%.6F.exr
Channels: {'charMatte12.R', 'charMatte12.G'}
```