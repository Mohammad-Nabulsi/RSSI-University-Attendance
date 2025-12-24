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
import math


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")

def quality_to_rssi_dbm(quality_percent):
    try:
        q = float(quality_percent)
        return (q / 2.0) - 100.0
    except Exception:
        return None


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
        if (m := ssid_re.match(ln)):
            current_ssid = m.group(1).strip()
            auth = None
            channel = None
            continue

        if (m := auth_re.match(ln)):
            auth = m.group(1).strip()
            continue

        if (m := channel_re.match(ln)):
            channel = m.group(1).strip()
            continue

        if (m := bssid_re.match(ln)):
            pending_bssid = m.group(1).lower()
            continue

        if (m := signal_re.match(ln)) and pending_bssid:
            quality = int(m.group(1))
            rssi = quality_to_rssi_dbm(quality)
            results.append({
                "ssid": current_ssid or "",
                "bssid": pending_bssid,
                "rssi_dbm": rssi,
                "signal_quality_percent": quality,
                "channel": channel or "",
                "frequency_mhz": "",
                "security": auth or "",
            })
            pending_bssid = None

    return results

def scan_once():
    return scan_windows()


def aggregate_scans(rows):
    agg = defaultdict(list)

    for r in rows:
        key = (r["location_label"], r["ssid"], r["bssid"])
        agg[key].append(float(r["rssi_dbm"]))

    aggregated = []
    for (label, ssid, bssid), rssis in agg.items():
        mean = sum(rssis) / len(rssis)
        std = math.sqrt(sum((x - mean) ** 2 for x in rssis) / len(rssis))

        aggregated.append({
            "location_label": label,
            "ssid": ssid,
            "bssid": bssid,
            "mean_rssi": round(mean, 2),
            "std_rssi": round(std, 2),
            "min_rssi": min(rssis),
            "max_rssi": max(rssis),
            "n_samples": len(rssis),
        })

    return aggregated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--interval", type=float, default=3.0)  
    parser.add_argument("--raw", default="fingerprints_raw.csv")
    parser.add_argument("--agg", default="fingerprints_agg.csv")
    args = parser.parse_args()

    raw_exists = os.path.exists(args.raw)
    agg_exists = os.path.exists(args.agg)

    raw_fields = [
        "timestamp", "location_label", "ssid", "bssid",
        "rssi_dbm", "signal_quality_percent", "channel",
        "frequency_mhz", "security", "sample_index"
    ]

    agg_fields = [
        "location_label", "ssid", "bssid",
        "mean_rssi", "std_rssi", "min_rssi", "max_rssi", "n_samples"
    ]

    cycle_timestamp = now_iso()
    all_rows = []

    print(f"\n📡 Starting scan cycle ({args.samples} scans, 3s interval)")
    print(f"Cycle timestamp: {cycle_timestamp}\n")

    with open(args.raw, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        if not raw_exists:
            writer.writeheader()

        for i in range(1, args.samples + 1):
            scan = scan_once()
            for ap in scan:
                row = {
                    "timestamp": cycle_timestamp,
                    "location_label": args.label,
                    "ssid": ap["ssid"],
                    "bssid": ap["bssid"],
                    "rssi_dbm": ap["rssi_dbm"],
                    "signal_quality_percent": ap["signal_quality_percent"],
                    "channel": ap["channel"],
                    "frequency_mhz": ap["frequency_mhz"],
                    "security": ap["security"],
                    "sample_index": i,
                }
                writer.writerow(row)
                all_rows.append(row)

            print(f"Scan {i}/{args.samples}: {len(scan)} APs")
            time.sleep(args.interval)


    aggregated = aggregate_scans(all_rows)

    with open(args.agg, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=agg_fields)
        if not agg_exists:
            writer.writeheader()
        for r in aggregated:
            writer.writerow(r)

    print("\nScan finished")
    print(f"Raw saved to: {args.raw}")
    print(f"Aggregated saved to: {args.agg}")


if __name__ == "__main__":
    main()
