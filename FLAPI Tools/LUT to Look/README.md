# LUT to Look

Wrap a 3D LUT as a Baselight Look

![Screenshot](screenshot-1.jpg)

This utility wraps a 3D LUT into a "Look" file that can be applied via the Look operator in Baselight and Daylight.

Your 3D LUT must be designed to use the same scene-refered colour space as input and output (e.g. a camera log space, T-log, or ACES).
 
## How To Use

Simply run `lut_to_look.app` on a Mac Baselight/Daylight system or `lut_to_look` on Linux system.

## How to Modify

If you want to make changes to the code, you'll need to install *tkinter* and *tkinterdnd2* for Python, e.g. on Linux:

```
sudo dnf --enablerepo=appstream install python3-tkinter
sudo python3 -m pip install tkinterdnd2
```

on Mac (using [Homebrew](https://brew.sh/)):

```
brew install python3-tk
sudo python3 -m pip install tkinterdnd2
````

Then run `python3 lut_to_look.py`
