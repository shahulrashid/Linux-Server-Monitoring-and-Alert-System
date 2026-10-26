# Linux Server Monitoring and Alert System

A Python + Bash tool that checks CPU, RAM, disk and service status on an Ubuntu server,
prints alerts and writes a rotating log (`monitor.log`).

## Setup (Ubuntu)
```bash
sudo apt update
sudo apt install python3 python3-psutil -y
chmod +x run_monitor.sh
```

## Usage
```bash
python3 monitor.py                       # run once
python3 monitor.py --loop -i 30          # run every 30 s until Ctrl+C
python3 monitor.py -s ssh -s nginx       # check several services
python3 monitor.py --cpu-limit 0         # force a CPU alert to test the logic
./run_monitor.sh --loop                  # same via the Bash launcher
tail -f monitor.log                      # watch the log live
```

## Features
- CPU / RAM / disk thresholds (defaults 80 / 80 / 85 %), configurable by flags
- Checks every mounted filesystem, not just `/`
- `systemctl` service checks with handling for missing systemd, timeouts, stderr
- Rotating log (1 MB x 3 backups); loop survives unexpected errors
- Graceful Ctrl+C

## Testing alerts
Set a threshold to 0 (`--cpu-limit 0 --ram-limit 0 --disk-limit 0`) and confirm
`ALERT:` lines appear in the terminal and `WARNING` lines in `monitor.log`.

## Screenshots
Add your own screenshots to a `screenshots/` folder, then link them here:

| Normal run | Forced alert (`--cpu-limit 0`) |
| --- | --- |
| ![normal run](screenshots/normal.png) | ![alert](screenshots/alert.png) |

## Known limitations
Single machine only; fixed thresholds; no email/Slack notifications; no auto-remediation;
in WSL or containers without systemd, service checks report "systemd unavailable".

## Run as a systemd service (optional)
Create `/etc/systemd/system/linux-monitor.service`:
```
[Unit]
Description=Linux Monitor
After=network.target

[Service]
WorkingDirectory=/home/YOURUSER/linux-monitor
ExecStart=/usr/bin/python3 monitor.py --loop -i 60
Restart=on-failure
User=YOURUSER

[Install]
WantedBy=multi-user.target
```
Then: `sudo systemctl daemon-reload && sudo systemctl enable --now linux-monitor`
