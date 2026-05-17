# Updated May 16, 2026
# Place this script in /vol/.support/scripts/ for it to be run within the app.
# Click Views > Scripts > Gearbox > Reload Scripts… to re-load it. Monitor the Log tab for any errors.

# Access via the main menu: Baselight > Delete Old Galleries

# This script will delete gallery scenes from the job database last modified before the specified date

import flapi
from datetime import datetime
from typing import List, Dict

conn = flapi.Connection.get()

# There is not currently a FLAPI method for reading Prefences > Cuts View, Gallery and Scratchpad > Gallery Job
# You can explicitly define the job here if not using localhost:baselight_gallery or n0:baselight_gallery
host = "localhost"
job = "baselight_gallery"

# Set time to 1 year previous by default
now = datetime.now()
lastSettings = {"Month": f"{now.month:02}", "Year": str(now.year - 1)}


class MainDialog:
    def __init__(self):
        global lastSettings

        # Define items to show in dialog
        self.options: List[Dict[str, str]] = [
            {"Key": "01", "Text": "January"},
            {"Key": "02", "Text": "February"},
            {"Key": "03", "Text": "March"},
            {"Key": "04", "Text": "April"},
            {"Key": "05", "Text": "May"},
            {"Key": "06", "Text": "June"},
            {"Key": "07", "Text": "July"},
            {"Key": "08", "Text": "August"},
            {"Key": "09", "Text": "September"},
            {"Key": "10", "Text": "October"},
            {"Key": "11", "Text": "November"},
            {"Key": "12", "Text": "December"},
        ]

        self.items = [
            flapi.DialogItem(
                Key="StaticText",
                Label="",
                Type=flapi.DIT_STATIC_TEXT,
                Default="Delete galleries last modified before",
            ),
            flapi.DialogItem(
                Key="Month",
                Label="Month",
                Type=flapi.DIT_DROPDOWN,
                Options=self.options,
                Default=self.options[0]["Key"],
            ),
            flapi.DialogItem(
                Key="Year",
                Label="Year",
                Type=flapi.DIT_INTEGER,
                IntMin=1980,
                IntMax=2999,
                Default=2025,
            ),
        ]

        # Create dialog, which will be shown later
        self.dialog = conn.DynamicDialog.create(
            "Delete Old Galleries", self.items, lastSettings
        )

    def show(self):
        # Show the dialog modally
        return self.dialog.show_modal(-200, -25)


class MainMenuItem:
    def __init__(self, message):
        # Save variables in this object instance
        self.message = message

        # Register menu item with the application
        self.menuItem = conn.MenuItem.create(self.message)
        self.menuItem.register(flapi.MENULOCATION_APP_MENU)
        self.menuItem.connect("MenuItemSelected", self.handle_signal)

    def handle_signal(self, sender, signal, args):
        global host, job, lastSettings
        app = conn.Application.get()

        # Check for gallery job on host or node
        if not conn.JobManager.job_exists(host, job):
            host = "n0"
        if not conn.JobManager.job_exists(host, job):
            app.message_dialog(
                "Gallery not found",
                "Unable to find baselight_gallery job.\n"
                + "Please edit this script to use the name of your Gallery Job\n"
                + "under Prefences > Cuts View, Gallery and Scratchpad.",
                ["OK"],
            )
            return

        self.dialog = MainDialog()
        result = self.dialog.show()
        if result:
            # First look at all scenes in the gallery job,
            # then get their modification date and compare to user selected date
            # making a list of gallery scenes to delete
            month, year = result["Month"], result["Year"]
            month_name = datetime.strptime(month, "%m").strftime("%B")
            lastSettings["Month"] = month
            lastSettings["Year"] = year

            cutoff = datetime.strptime(f"{year}-{month}-01 00:00", "%Y-%m-%d %H:%M")

            scenes = conn.JobManager.get_scenes(host, job)
            scene_count = len(scenes)
            progress_count = 0
            progress_percent = 0.0
            scenes_to_del = []

            pb = conn.ProgressDialog.create("Checking gallery dates...", "", False)
            pb.show()
            pb.set_progress(progress_percent, "")

            for scene in scenes:
                progress_count += 1
                if int(progress_count / scene_count * 10) % 10 > progress_percent:
                    progress_percent = int(progress_count / scene_count * 10) % 10
                    pb.set_progress(progress_percent / 10.0, "")

                scene_info = conn.JobManager.get_scene_info(host, job, scene)
                dt = datetime.strptime(scene_info.ModifiedDate, "%Y-%m-%d %H:%M")
                if dt < cutoff:
                    scenes_to_del.append(scene)

            pb.hide()

            # A list of scenes to delete has been made, make user confirm deletion

            scene_del_count = len(scenes_to_del)
            if len(scenes_to_del) < 1:
                app.message_dialog(
                    "Nothing to Delete",
                    f"{scene_count} galleries found, but all have\n"
                    + f"been modified after {month_name} {year}.\n",
                    ["OK"],
                )
                return

            validate = app.message_dialog(
                "Confirm Deletion",
                f"Are you sure you want to delete {scene_del_count}\n"
                + f"of your {scene_count} galleries?\n\n"
                + "This action cannot be undone. Automatic backups\n"
                + "will also be deleted after 7 days.\n",
                ["Delete Them", "Cancel"],
            )
            if validate == "Delete Them":
                pb = conn.ProgressDialog.create("Checking gallery dates...", "", False)
                progress_count = 0
                progress_percent = 0.0
                pb.show()
                pb.set_progress(progress_percent, "")

                for scene in scenes_to_del:
                    progress_count += 1
                    if (int(progress_count / scene_del_count * 10) % 10 > progress_percent):
                        progress_percent = (int(progress_count / scene_del_count * 10) % 10)
                        pb.set_progress(progress_percent / 10.0, "")
                    conn.JobManager.delete_scene(host, job, scene, 1)

                pb.hide()
                app.message_dialog(
                    "Deletion Complete", f"{scene_del_count} galleries deleted.", ["OK"]
                )


mainMenuItem1 = MainMenuItem("Delete Old Galleries")
