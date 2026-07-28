# Updated July 28, 2026
import flapi
import os
import json
import subprocess
import glob

CONFIG_FILE = os.path.expanduser("~/.flapi_job_template_settings.json")

class SettingsManager:
    def __init__(self):
        self.settings = {
            "hosts": ["localhost"],
            "last_host": "localhost",
            "last_template": "",
            "last_new_name": "",
            "last_include_scenes": 0
        }
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print("Failed to load settings:", e, flush=True)
                
    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print("Failed to save settings:", e, flush=True)

    def add_host(self, host):
        if host not in self.settings["hosts"]:
            self.settings["hosts"].append(host)
            self.save()


class JobTemplateMenu:
    def __init__(self):
        self.conn = flapi.Connection.get()
        self.menuItem = self.conn.MenuItem.create("Job from Template...")
        self.menuItem.register(flapi.MENULOCATION_SCENE_MENU)
        self.menuItem.connect("MenuItemSelected", self.handle_signal)
        self.settings_manager = SettingsManager()

    def get_scenetool_command(self):
        # Known fixed paths
        paths = [
            "/Applications/Baselight/Current/bin/scenetool",
            "/Applications/Baselight/Current/Utilities/Tools/scenetool",
            "/usr/fl/baselight/bin/scenetool"
        ]
        
        for path in paths:
            if os.path.isfile(path):
                return path
                
        # Search for recent Baselight installation on macOS
        matches = glob.glob("/Applications/Baselight/*/Baselight-*.app/Contents/bin/scenetool")
        matches.extend(glob.glob("/usr/fl/baselight-*/bin/scenetool"))
        if matches:
            # return the latest version found
            return sorted(matches)[-1] 
            
        return "scenetool"

    def get_bl_lshosts_command(self):
        paths = [
            "/Applications/Baselight/Current/bin/bl-lshosts",
            "/Applications/Baselight/Current/Utilities/Tools/bl-lshosts",
            "/usr/fl/baselight/bin/bl-lshosts"
        ]
        
        for path in paths:
            if os.path.isfile(path):
                return path
                
        matches = glob.glob("/Applications/Baselight/*/Baselight-*.app/Contents/bin/bl-lshosts")
        matches.extend(glob.glob("/usr/fl/baselight-*/bin/bl-lshosts"))
        if matches:
            return sorted(matches)[-1] 
            
        return "bl-lshosts"
        
    def get_configured_hosts(self):
        cmd = self.get_bl_lshosts_command()
        hosts = []
        try:
            res = subprocess.run([cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    h = line.strip()
                    if h:
                        hosts.append(h)
        except Exception:
            pass
        return hosts

    def handle_signal(self, sender, signal, args):
        app = self.conn.Application.get()
        
        # Pull configured hosts from Baselight and merge with settings
        configured_hosts = self.get_configured_hosts()
        for h in configured_hosts:
            if h not in self.settings_manager.settings["hosts"]:
                self.settings_manager.settings["hosts"].insert(0, h)
                self.settings_manager.save()
        
        while True:
            selected_host = self.settings_manager.settings["last_host"]
            host_options = self.settings_manager.settings["hosts"]
            if not host_options:
                host_options = ["localhost"]
                
            if selected_host not in host_options:
                selected_host = host_options[0]
                
            try:
                jobs = self.conn.JobManager.get_jobs(selected_host)
                if isinstance(jobs, list):
                    jobs.sort(key=str.lower)
            except flapi.FLAPIException as e:
                # If it fails, provide a dummy so the dialog can still open and let the user change the host
                jobs = ["<Error: Could not connect to host>"]
                
            if not jobs:
                jobs = ["<No jobs found>"]
                
            last_template = self.settings_manager.settings["last_template"]
            if last_template not in jobs:
                last_template = jobs[0]
                
            job_items = [
                flapi.DialogItem(Key="Host", Label="Database Host", Type=flapi.DIT_DROPDOWN, Options=host_options, Default=selected_host),
                flapi.DialogItem(Key="HostNote", Label="", Type=flapi.DIT_STATIC_TEXT, Default="(Change host and click OK to refresh template jobs)"),
                flapi.DialogItem(Key="TemplateJob", Label="Template Job", Type=flapi.DIT_DROPDOWN, Options=jobs, Default=last_template),
                flapi.DialogItem(Key="NewJobName", Label="New Job Name", Type=flapi.DIT_STRING, Default=self.settings_manager.settings["last_new_name"]),
                flapi.DialogItem(Key="IncludeScenes", Label="Include Scenes", Type=flapi.DIT_TOGGLE, Default=self.settings_manager.settings["last_include_scenes"])
            ]
            
            job_settings = {
                "Host": selected_host,
                "TemplateJob": last_template,
                "NewJobName": self.settings_manager.settings["last_new_name"],
                "IncludeScenes": self.settings_manager.settings["last_include_scenes"]
            }
            
            job_dialog = self.conn.DynamicDialog.create("Create Job From Template", job_items, job_settings)
            result = job_dialog.show_modal(-1, -1)
            job_dialog.release()
            
            if not result:
                return # Cancelled
                
            new_host = result["Host"]
            
            # Did the user change the host?
            if new_host != selected_host:
                self.settings_manager.settings["last_host"] = new_host
                self.settings_manager.save()
                # Loop back to refresh jobs
                continue
                
            # If host didn't change, proceed with job creation
            template_job = result["TemplateJob"]
            new_job_name = result["NewJobName"].strip()
            include_scenes = result["IncludeScenes"]
            
            if template_job.startswith("<"):
                app.message_dialog("Error", "Please select a valid template job.", ["OK"])
                continue
            
            if not new_job_name:
                app.message_dialog("Error", "New Job Name cannot be empty.", ["OK"])
                continue
                
            if self.conn.JobManager.job_exists(selected_host, new_job_name):
                app.message_dialog("Error", f"Job '{new_job_name}' already exists on host '{selected_host}'.", ["OK"])
                continue
                
            # Validations passed. Break out of the dialog loop.
            break

        # Save settings
        self.settings_manager.settings["last_template"] = template_job
        self.settings_manager.settings["last_new_name"] = new_job_name
        self.settings_manager.settings["last_include_scenes"] = include_scenes
        self.settings_manager.save()
        
        # Job Creation Strategy
        if include_scenes:
            # Use native scenetool copy for the entire job in one go
            progress = self.conn.ProgressDialog.create("Duplicating Job", "Copying job using scenetool...", 0)
            progress.show(0.0)
            progress.set_progress(0.5, "Running scenetool copy...")
            
            scenetool = self.get_scenetool_command()
            src = f"{selected_host}:{template_job}"
            dst = f"{selected_host}:{new_job_name}"
            
            args = [scenetool, 'copy', src, dst]
            print("Running native job copy:", " ".join(args), flush=True)
            
            try:
                res = subprocess.run(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
                res.check_returncode()
            except Exception as e:
                progress.hide()
                print(f"Failed to copy job {src}: {e}", flush=True)
                if isinstance(e, subprocess.CalledProcessError):
                    print("Stderr:", e.stderr.decode('utf-8', errors='ignore'), flush=True)
                app.message_dialog("Error", f"Failed to duplicate job '{template_job}'.\nCheck the console for details.", ["OK"])
                progress.release()
                return
                
            progress.set_progress(1.0, "Complete!")
            progress.hide()
            progress.release()
            
        else:
            # Create empty job and recreate folders only
            try:
                self.conn.JobManager.create_job(selected_host, new_job_name)
            except flapi.FLAPIException as e:
                app.message_dialog("Error", f"Failed to create job '{new_job_name}':\n{e}", ["OK"])
                return
                
            # Fetch and recreate folders
            try:
                folders = self.conn.JobManager.get_folders(selected_host, template_job, None, 1)
            except flapi.FLAPIException as e:
                app.message_dialog("Error", f"Failed to get folders from template job:\n{e}", ["OK"])
                return
                
            progress = self.conn.ProgressDialog.create("Creating Job Folders", "Preparing to create folders...", 1)
            progress.show(0.0)
            
            total_steps = len(folders)
            current_step = 0
                
            for folder in folders:
                if progress.is_cancelled():
                    break
                try:
                    self.conn.JobManager.create_folder(selected_host, new_job_name, folder)
                except flapi.FLAPIException as e:
                    print(f"Error creating folder {folder}: {e}", flush=True)
                current_step += 1
                prog_val = float(current_step) / float(max(1, total_steps))
                progress.set_progress(prog_val, f"Created {folder}")
                
            progress.hide()
            
            if progress.is_cancelled():
                app.message_dialog("Cancelled", "Folder creation was cancelled.", ["OK"])
                return

            progress.release()

        app.message_dialog("Success", f"Job '{new_job_name}' has been created successfully.", ["OK"])

# Keep a global reference to prevent garbage collection
job_template_menu = JobTemplateMenu()
