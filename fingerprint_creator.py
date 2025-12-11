import argparse
import csv
import datetime as dt
import platform
import re
import subprocess
import sys
import time
from collections import defaultdict
import os

# -------- Helpers --------
def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")

def quality_to_rssi_dbm(quality_percent):
    try:
        q = float(quality_percent)
        return (q / 2.0) - 100.0
    except Exception:
        return None

# -------- Scanners per OS --------
def scan_windows():
    cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
    out = subprocess.check_output(cmd, text=True, errors="ignore")
    lines = out.splitlines()

    results = []
    current_ssid = None
    auth = None
    channel = None

    ssid_re = re.compile(r"^\s*SSID\s+\d+\s*:\s*(.*)\s*$", re.IGNORECASE)
    bssid_re = re.compile(r"^\s*BSSID\s+\d+\s*:\s*([0-9a-f:]{17})\s*$", re.IGNORECASE)
    signal_re = re.compile(r"^\s*Signal\s*:\s*(\d+)%\s*$", re.IGNORECASE)
    channel_re = re.compile(r"^\s*Channel\s*:\s*(\d+)\s*$", re.IGNORECASE)
    auth_re = re.compile(r"^\s*Authentication\s*:\s*(.+)\s*$", re.IGNORECASE)

    pending_bssid = None

    for ln in lines:
        m = ssid_re.match(ln)
        if m:
            current_ssid = m.group(1).strip()
            auth = None
            channel = None
            continue

        m = auth_re.match(ln)
        if m:
            auth = m.group(1).strip()
            continue

        m = channel_re.match(ln)
        if m:
            channel = m.group(1).strip()
            continue

        m = bssid_re.match(ln)
        if m:
            pending_bssid = m.group(1).lower()
            continue

        m = signal_re.match(ln)
        if m and pending_bssid:
            quality = int(m.group(1))
            rssi = quality_to_rssi_dbm(quality)
            results.append({
                "ssid": current_ssid or "",
                "bssid": pending_bssid,
                "rssi_dbm": rssi or "",
                "signal_quality_percent": quality,
                "channel": channel or "",
                "frequency_mhz": "",
                "security": auth or "",
            })
            pending_bssid = None

    return results





def scan_once():
    return scan_windows()


# -------- Main --------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--raw", default="fingerprints_raw.csv")
    parser.add_argument("--agg", default="fingerprints_agg.csv")
    args = parser.parse_args()

    # Ensure append mode & header only once
    raw_exists = os.path.exists(args.raw)
    agg_exists = os.path.exists(args.agg)

    raw_fields = [
        "timestamp", "location_label", "ssid", "bssid",
        "rssi_dbm", "signal_quality_percent", "channel",
        "frequency_mhz", "security", "sample_index"
    ]

    # OPEN RAW IN APPEND MODE
    with open(args.raw, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        if not raw_exists:
            writer.writeheader()

        # ONE timestamp for the entire 20-scan cycle
        cycle_timestamp = now_iso()

        print(f"\n📡 Starting cycle: label={args.label} samples={args.samples}")
        print(f"Timestamp for this entire cycle: {cycle_timestamp}\n")

        for i in range(1, args.samples + 1):

            scan = scan_once()
            for ap in scan:
                row = {
                    "timestamp": cycle_timestamp,  # <----- SAME TIMESTAMP FOR ALL 20
                    "location_label": args.label,
                    "ssid": ap.get("ssid", ""),
                    "bssid": ap.get("bssid", ""),
                    "rssi_dbm": ap.get("rssi_dbm", ""),
                    "signal_quality_percent": ap.get("signal_quality_percent", ""),
                    "channel": ap.get("channel", ""),
                    "frequency_mhz": ap.get("frequency_mhz", ""),
                    "security": ap.get("security", ""),
                    "sample_index": i,
                }
                writer.writerow(row)

            print(f"Scan {i}/{args.samples}: {len(scan)} networks found")
            time.sleep(args.interval)

    print(f"✅ Cycle saved. Sleeping 5 minutes...\n")


# -------- Loop Forever --------
if __name__ == "__main__":
    while True:
        main()
        time.sleep(300)  # 5 minutes
