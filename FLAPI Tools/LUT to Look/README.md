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

For testing, run it with

```
python3 lut_to_look.py
```

To re-compile as an app, run

```
pyinstaller --onefile -w lut_to_look.py
```

Linux may require using the -add-data flag to compile:

```
pyinstaller --add-data /usr/local/lib/python3.6/site-packages/tkinterdnd2:tkinterdnd2 --onefile -w lut_to_look.py
```