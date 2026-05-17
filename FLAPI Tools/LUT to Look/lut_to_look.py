# Updated May 17, 2026
# This app wraps a LUT as a Baselight LOOK file that can be applied via the "Look" operator
#
# To compile into a stand-alone app, run:
# MacOS:
#    pyinstaller --onefile -w lut_to_look.py
# Linux (replace "python3.6" with your python version)
# pyinstaller --add-data /usr/local/lib/python3.6/site-packages/tkinterdnd2:tkinterdnd2 --onefile -w lut_to_look.py

import tkinter as tk
from os import path, remove
from shutil import copy
from tkinter import Label, messagebox
from tkinterdnd2 import DND_ALL, TkinterDnD

cspace_options = {
    "ARRI_LogC_WG_full": "ARRI: LogC3 / ARRI Wide Gamut 3",
    "ARRI_LogC4_AWG4": "ARRI: LogC4 / ARRI Wide Gamut 4",
    "Red_Log3G10_REDWideGamut": "RED: Log3G10 / REDWideGamutRGB",
    "Sony_SLog3_Gam3": "Sony: S-Log3 / S-Gamut3",
    "Sony_SLog3_Gam3Cine": "Sony: S-Log3 / S-Gamut3.Cine",
    "FilmLight_TLog_EGamut2": "FilmLight: T-Log / E-Gamut 2",
    "ACES_lin": "ACES: Linear / AP0",
    "ACEScct": "ACEScct: ACEScct / AP1"
}


def get_path(event):
    # Callback function executed when a file is dropped.
    # event.data contains the path(s) of the dropped file(s).
    global file_path
    file_path = event.data.strip('{}') # strip needed when path has spaces
    filename = path.basename(file_path)
    short_filename, extension = path.splitext(filename)
    
    drop_target_label.config(text = "Generating Look for " + filename)
    name.delete(0, tk.END)
    name.insert(0, short_filename)
    
    print(f"Dropped file: {file_path}")


def gen_look():
    # Callback function executed when "Generate Look" is pressed.
    
    # First check for common problems
    global file_path
    if file_path == "" or not path.exists(file_path):
        messagebox.showerror("Error", "Unable to load LUT file " + file_path)
        return
    look_name = name.get().strip()
    look_file_name = look_name.replace(" ", "_") + ".fllook"
    if look_name == "":
        messagebox.showerror("Error", "Please enter a LOOK name.")
        return
    group_name = group.get().strip()
    group_shortname = group_name.replace(" ", "")
    if look_name == "":
        messagebox.showerror("Error", "Please enter a Group name.")
        return
    
    look_path = "/usr/fl/looks"
    if not path.exists(look_path):
        look_path = "/Library/Application Support/FilmLight/looks"
        if not path.exists(look_path):
            messagebox.showerror("Error", "Unable to find look folder.")
            return
    
    if path.exists(f"{look_path}/{look_file_name}"):
        result = messagebox.askyesno("Overwrite?", f"{look_file_name} exists. Overwrite?")
        if result:
            try:
                remove(f"{look_path}/{look_file_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Unable to remove existing look file: {e}")
                return
        else:
            return
    
    # Create the .fllookgroup if it doesn't exist
    try:
        with open(f"{look_path}/{group_shortname}.fllookgroup", "x") as file:
            file.write(f"Name = \"{group_shortname}\";\n")
            file.write(f"UIName = \"{group_name}\";\n")
            file.write(f"Help = \"{group_name}\";\n")
            print(f"Created Look Group: {group_shortname}.fllookgroup")
    except FileExistsError:
        pass
    except Exception as e:
        messagebox.showerror("Error", f"Error writing look group file: {e}")
        return
    
    # Copy the LUT file
    lut_filename = path.basename(file_path)
    try:
        copy(file_path, f"{look_path}/{lut_filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Error copying LUT file: {e}")
        return
    
    # Write the .look file
    try:
        colour_space = cspace.get()
        colour_space_file = ""
        for key, value in cspace_options.items():
            if value == colour_space:
                colour_space_file = key
        with open(f"{look_path}/{look_file_name}", "w") as file:
            file.write(f"Name = \"{look_name}\";\n")
            file.write(f"Space = \"{colour_space_file}\";\n")
            file.write(f"Group = \"{group_shortname}\";\n")
            file.write("Recipe =\n")
            file.write("[array\n")
            file.write("  [struct type=\"raw\",\n")
            file.write('    code="tcsCube{out{%i.cub} arg{\\"file{%%L/' + lut_filename + '}\\"} gpu{%g}}\\n"\n')
            file.write('         "doCube{out{%o} in{%i} cube{%i.cub} hq{1}}\\n",\n')
            file.write("  ],\n")
            file.write("];\n")
            file.write(f"Help = \"{look_name}\";\n")
    except Exception as e:
        messagebox.showinfo("Error", f"Error writing LOOK file: {e}")
        return
    
    print(f"Created Look: {look_file_name}")
    messagebox.showinfo("Look Created", f"Created look file: {look_file_name}")



# Create the main window instance from TkinterDnD
root = TkinterDnD.Tk()
root.geometry("400x320")
root.title("Crealte .fllook for LUT file")

# Create a Label widget to serve as the drop target
file_path = ""
drop_target_label = Label(root, text="Drag and drop LUT here", bg="lightgray", relief="solid", bd=2)
drop_target_label.pack(fill="both", expand=True, padx=20, pady=20)

# Register the label as a drop target for all types of drag-and-drop operations
drop_target_label.drop_target_register(DND_ALL)

# Bind the <<Drop>> event to the get_path function
# This function will be called when a file is dropped onto the label
drop_target_label.dnd_bind('<<Drop>>', get_path)

# Create a StringVar to store the selected option
menu_options = list(cspace_options.values())
cspace = tk.StringVar(root)
cspace.set(menu_options[0])  # Set the default value

# Create the OptionMenu and Name entries
dropdown_label = tk.Label(root, text="LUT Colour Space:")
dropdown_label.pack()
dropdown = tk.OptionMenu(root, cspace, *menu_options)
dropdown.pack()

name_label = tk.Label(root, text="Look Name:")
name_label.pack()
name = tk.Entry(root, width=30)
name.pack()

group_label = tk.Label(root, text="Look Group Name:")
group_label.pack()
group = tk.Entry(root, width=30)
group.insert(0, "My Looks")
group.pack()

# Create the Generate button
button = tk.Button(root, text="Generate Look", command=gen_look)
button.pack(pady=(10,20))

root.mainloop()
