# Render Watch

Monitor render nodes, send email status reports, and restart if hung. 
 
Once this script is installed and running, it will monitor the local render queue every 5 seconds. If a render operation progress does not change for 60 seconds, it will consider the operation hung.

The script will send an email when a render completes successfully, fails, or hangs. The email includes the name of the render job, the machine, and the date & time.

When a render fails, it will include the log from the render queue in the email.

When a render hangs, it will:
- dump diagnostic information from the renderworker service into a folder in `/tmp/fl-queue-dump-<date>`
- restart the prerender and render fl-services
- send an email notification


# Installation

On a Baselight/Daylight system the FLAPI enviroment will already be initialized. If installing on a FLUX Store or render node which has never run a FLAPI script you'll have to setup the enviroment:

```
sudo mkdir -m 777 /usr/fl/server-scripts
./init-virtualenv
````

For all systems:

- edit `renderwatch.py` to change the email options, setting "send_email" to your smtp mail server and setting "smtp_sender" and "smtp_receipts" to valid email addresses. If you don't want to send email, set `SEND_EMAILS` to `False`.
- copy `getrenderport` and `renderwatch.py` into `/usr/fl/server-scripts`
- Run
  ```
  curl http://localhost:1984/reload-scripts
  ```
  to tell the flapi daemon to load the new script without restarting