#!/usr/bin/env python3
"""Linux Server Monitoring and Alert System.

Checks CPU, RAM, disk and service status, prints alerts and writes a rotating log.

Usage:
    python3 monitor.py                    # run once
    python3 monitor.py --loop             # run continuously (default every 60 s)
    python3 monitor.py --loop -i 30       # custom interval
    python3 monitor.py -s ssh -s nginx    # check several services
    python3 monitor.py --cpu-limit 0      # lower a threshold to test alerts
"""
import argparse
import logging
import shutil
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler

import psutil

LOG_FILE = "monitor.log"
CPU_LIMIT = 80
RAM_LIMIT = 80
DISK_LIMIT = 85


def setup_logging(log_file):
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def alert(message):
    print(f"ALERT: {message}")
    logging.warning(message)


def check_system(cpu_limit, ram_limit, disk_limit):
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    usage = shutil.disk_usage("/")
    disk = usage.used / usage.total * 100

    print(f"CPU Usage: {cpu}%")
    print(f"RAM Usage: {ram}%")
    print(f"Disk Usage: {disk:.1f}%")
    logging.info(f"CPU={cpu}%, RAM={ram}%, DISK={disk:.1f}%")

    if cpu > cpu_limit:
        alert(f"High CPU usage detected ({cpu}% > {cpu_limit}%)")
    if ram > ram_limit:
        alert(f"High RAM usage detected ({ram}% > {ram_limit}%)")
    if disk > disk_limit:
        alert(f"Disk space running low ({disk:.1f}% > {disk_limit}%)")


def check_disks(disk_limit):
    """Check every real mounted filesystem, not just '/'."""
    seen = set()
    for part in psutil.disk_partitions(all=False):
        if part.mountpoint in seen:
            continue
        seen.add(part.mountpoint)
        try:
            u = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        if u.percent > disk_limit:
            alert(f"Mount {part.mountpoint} is {u.percent}% full")


def check_service(service):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        alert("systemctl not found (systemd unavailable, e.g. WSL or container)")
        return
    except subprocess.TimeoutExpired:
        alert(f"Timed out checking service {service}")
        return

    status = result.stdout.strip() or "unknown"
    print(f"{service} service: {status}")
    if status == "active":
        logging.info(f"Service {service} is active")
    else:
        detail = result.stderr.strip()
        alert(f"Service {service} is {status}" + (f" ({detail})" if detail else ""))


def run_once(args):
    check_system(args.cpu_limit, args.ram_limit, args.disk_limit)
    check_disks(args.disk_limit)
    for svc in args.service:
        check_service(svc)


def parse_args():
    p = argparse.ArgumentParser(description="Linux server monitor")
    p.add_argument("--cpu-limit", type=float, default=CPU_LIMIT)
    p.add_argument("--ram-limit", type=float, default=RAM_LIMIT)
    p.add_argument("--disk-limit", type=float, default=DISK_LIMIT)
    p.add_argument("-s", "--service", action="append", default=None,
                   help="service to check (repeatable); default: ssh")
    p.add_argument("--loop", action="store_true", help="run continuously")
    p.add_argument("-i", "--interval", type=int, default=60,
                   help="seconds between checks in loop mode")
    p.add_argument("--log-file", default=LOG_FILE)
    args = p.parse_args()
    args.service = args.service or ["ssh"]
    return args


def main():
    args = parse_args()
    setup_logging(args.log_file)
    print("Linux Server Monitoring Started")
    try:
        while True:
            try:
                run_once(args)
            except Exception as exc:  # keep the loop alive on unexpected errors
                logging.error(f"Monitoring cycle failed: {exc}")
                print(f"ERROR: {exc}")
            if not args.loop:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        logging.info("Monitor stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
