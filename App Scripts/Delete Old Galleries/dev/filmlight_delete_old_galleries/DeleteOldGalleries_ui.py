# Updated May 21, 2026
# Access via the main menu: Baselight > Delete Old Galleries
# This script will delete gallery scenes from the job database last modified before the specified date

import flapi
from datetime import datetime
from typing import List, Dict


class MainDialog:
    def __init__(self, dogui, lastSettings):
        self.conn = dogui.conn

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
        self.dialog = self.conn.DynamicDialog.create(
            "Delete Old Galleries", self.items, lastSettings
        )

    def show(self):
        # Show the dialog modally
        return self.dialog.show_modal(-200, -25)


class DOGUI:
    # There is not currently a FLAPI method for reading Prefences > Cuts View, Gallery and Scratchpad > Gallery Job
    # You can explicitly define the job here if not using localhost:baselight_gallery or n0:baselight_gallery
    host : str = "localhost"
    job : str = "baselight_gallery"

    def __init__(self):
        self.conn = flapi.Connection.get()    

        # Set cutoff time to 1 year previous by default
        now = datetime.now()
        self.lastSettings = {"Month": f"{now.month:02}", "Year": str(now.year - 1)}

        # Register menu item with the application
        self.menuItem = self.conn.MenuItem.create("Delete Old Galleries")
        self.menuItem.register(flapi.MENULOCATION_APP_MENU)
        self.menuItem.connect("MenuItemSelected", self.handle_menu_signal)

    def handle_menu_signal(self, sender, signal, args):
        app = self.conn.Application.get()

        # Check for gallery job on host or node
        if not self.conn.JobManager.job_exists(self.host, self.job):
            self.host = "n0"
        if not self.conn.JobManager.job_exists(self.host, self.job):
            app.message_dialog(
                "Gallery not found",
                "Unable to find baselight_gallery job.\n"
                + "Please edit this script to use the name of your Gallery Job\n"
                + "under Prefences > Cuts View, Gallery and Scratchpad.",
                ["OK"],
            )
            return

        self.dialog = MainDialog(self, self.lastSettings)
        result = self.dialog.show()
        if result:
            # Add the deletion process to the queue
            month, year = result["Month"], result["Year"]
            self.lastSettings["Month"] = month
            self.lastSettings["Year"] = year

            cutoff = datetime.strptime(f"{year}-{month}-01 00:00", "%Y-%m-%d %H:%M")
        
            qm = self.conn.QueueManager.create_local()

            desc = "Deleting Old Galleries"
            params = {
                "host": self.host,
                "job": self.job, 
                "cutoff": cutoff.isoformat()
            }
            tasks = [
                flapi.QueueOpTask(
                    Seq=1,
                    Type="Delete Old Galleries",
                    Desc="Delete Old Galleries",
                    Weight=1.0,
                    Params=params
                )
            ]

            qm.new_operation( "DOG", desc, params, tasks )
            qm.release()

            app.message_dialog(
                "Deletion Queued", "Gallery cleanup is processing in the\nbackground, check Queue Monitor for status.", ["OK"]
            )
