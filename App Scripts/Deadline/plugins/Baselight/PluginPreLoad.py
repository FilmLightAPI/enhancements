#!/usr/bin/env python3
import sys
from pathlib import Path

def __main__():
    path = "/usr/fl/baselight/share/flapi/python/"
    
    if not Path(path).is_dir():
        path = "/Applications/Baselight/Current/Utilities/Resources/share/flapi/python/"
    
    if not Path(path).is_dir():
        path = "/Applications/Daylight/Current/Utilities/Resources/share/flapi/python/"
    
    match = next(Path(path).glob("filmlightapi-*.whl"), None)
    if match:
        path = str(match)
    
    if path not in sys.path:
        sys.path.append(path)
