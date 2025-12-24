import argparse
import datetime as dt
import time
import requests
from collect_fingerprint import scan_once


def build_scan_map(scan_list):
    result = {}
    for ap in scan_list:
        bssid = ap.get("bssid")
        rssi = ap.get("rssi_dbm")
        if not bssid or rssi in ("", None):
            continue
        try:
            result[bssid] = float(rssi)
        except ValueError:
            continue
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id")
    parser.add_argument("--room-id")
    parser.add_argument("--server-url", default="http://127.0.0.1:5000")
    parser.add_argument("--interval", type=float, default=5.0)

    args = parser.parse_args()

    # ── If started by SERVER → args exist
    if args.student_id and args.room_id:
        student_id = args.student_id
        room_id = args.room_id
    else:
        # ── Manual mode (terminal)
        student_id = input("Enter your student ID: ").strip()
        room_id = input("Enter room ID: ").strip()

    interval = args.interval
    base_url = args.server_url.rstrip("/")

    print(f"📡 Client started for {student_id} in room {room_id}")

    while True:
        scan_list = scan_once()
        scan_map = build_scan_map(scan_list)

        timestamp = dt.datetime.now().isoformat(timespec="seconds")

        payload = {
            "student_id": student_id,
            "room_id": room_id,
            "timestamp": timestamp,
            "scan": scan_map,
        }

        try:
            r = requests.post(f"{base_url}/rssi-report", json=payload, timeout=5)
            r.raise_for_status()
        except Exception as e:
            print("❌ Failed to send scan:", e)

        time.sleep(interval)


if __name__ == "__main__":
    main()