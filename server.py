from flask import Flask, request, jsonify, render_template, redirect, url_for
import csv
from datetime import datetime, timedelta
import subprocess
import sys
import os

app = Flask(__name__)


FINGERPRINTS_FILE = "fingerprints_agg.csv"  
WINDOW_MINUTES = 10       
REQUIRED_MINUTES = 1     
DIST_THRESHOLD = 10.0      
PING_INTERVAL_MIN = 0.5    

running_clients = {}  
FINGERPRINTS = {}

pings = {}

attendance = {}
student_registrations = []

def start_client_process(student_id, room_id):
    """
    Starts the attendance client as a background process
    """
    client_script = os.path.join(os.getcwd(), "client.py")

    if not os.path.exists(client_script):
        raise RuntimeError("Client script not found")

    cmd = [
        sys.executable,
        client_script,
        "--student-id", student_id,
        "--room-id", room_id,
        "--server-url", "http://127.0.0.1:5000"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    running_clients[(student_id, room_id)] = process


def count_current_students(room_id):
    """
    Count students whose latest ping indicates they are inside the room
    """
    count = 0

    for (r, student_id), history in pings.items():
        if r != room_id or not history:
            continue

        last_ping = history[-1]  # most recent
        if last_ping.get("inside"):
            count += 1

    return count



def load_fingerprints(path):
    fps = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            room = row["location_label"]
            bssid = row["bssid"]
            mean_str = row["mean_rssi"]
            if not room or not bssid or not mean_str:
                continue
            mean_val = float(mean_str)
            if room not in fps:
                fps[room] = {}
            fps[room][bssid] = mean_val
    return fps


FINGERPRINTS = load_fingerprints(FINGERPRINTS_FILE)
print("Loaded fingerprints for rooms:", list(FINGERPRINTS.keys()))


def calc_distance(room_fp, scan):
    """
    room_fp: dict[bssid] -> mean_rssi_dbm
    scan:    dict[bssid] -> current_rssi_dbm
    """
    common = set(room_fp.keys()) & set(scan.keys())
    if not common:
        return 9999.0

    diffs = []
    for b in common:
        diffs.append(abs(room_fp[b] - scan[b]))

    return sum(diffs) / len(diffs)



def update_attendance(room_id, student_id, now):
    key = (room_id, student_id)
    if key not in pings:
        return 0.0, "unknown"


    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    history = [p for p in pings[key] if p["ts"] >= cutoff]
    pings[key] = history

    inside_count = sum(1 for p in history if p["inside"])
    minutes_inside = inside_count * PING_INTERVAL_MIN

    date_str = now.date().isoformat()
    att_key = (room_id, date_str, student_id)

    if minutes_inside >= REQUIRED_MINUTES:
        attendance[att_key] = "present"
    else:
        attendance.setdefault(att_key, "unknown")

    return minutes_inside, attendance[att_key]



@app.post("/rssi-report")
def rssi_report():
    data = request.get_json(force=True)

    student_id = data["student_id"]
    room_id = data["room_id"]
    timestamp_str = data.get("timestamp")
    scan_dict = data["scan"] 
    print(f"Ping from {student_id} in {room_id}")

    if room_id not in FINGERPRINTS:
        return jsonify({"error": f"Unknown room_id: {room_id}"}), 400


    scan = {}
    for bssid, rssi in scan_dict.items():
        try:
            scan[bssid] = float(rssi)
        except:
            continue

    now = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()

    room_fp = FINGERPRINTS[room_id]
    dist = calc_distance(room_fp, scan)
    inside = dist <= DIST_THRESHOLD

    key = (room_id, student_id)
    history = pings.get(key, [])
    history.append({"ts": now, "inside": inside})
    pings[key] = history

    minutes_inside, status = update_attendance(room_id, student_id, now)

    return jsonify({
        "ok": True,
        "distance": dist,
        "inside_now": inside,
        "minutes_inside_window": minutes_inside,
        "status_today": status,
    })



@app.get("/attendance/<room_id>/<date_str>")
def get_attendance(room_id, date_str):
    result = []
    for (r, d, sid), status in attendance.items():
        if r == room_id and d == date_str:
            result.append({
                "student_id": sid,
                "status": status
            })
    return jsonify(result)


@app.route("/")
def root():

    return redirect(url_for("dashboard"))


@app.route("/student", methods=["GET", "POST"])
def student_page():

    rooms = list(FINGERPRINTS.keys())
    default_room = rooms[0] if rooms else ""

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        section_code = request.form.get("section_code", "").strip()
        room_id = request.form.get("room_id", "").strip()

        error = None
        if not student_id:
            error = "Insert your student ID"
        elif not room_id:
            error = "Select your room"

        if error:
            return render_template(
                "student.html",
                rooms=rooms,
                room_id=room_id or default_room,
                student_id=student_id,
                section_code=section_code,
                error=error,
            )


        reg = {
            "student_id": student_id,
            "section_code": section_code,
            "room_id": room_id,
            "registered_at": datetime.utcnow().isoformat(timespec="seconds"),
        }
        student_registrations.append(reg)

        key = (student_id, room_id)
        if key not in running_clients:
            try:
                start_client_process(student_id, room_id)
                print(f"Started client for {student_id} in room {room_id}")
            except Exception as e:
                print("Failed to start client:", e)


        return render_template("student_success.html", reg=reg)

    return render_template(
        "student.html",
        rooms=rooms,
        room_id=default_room,
        student_id="",
        section_code="",
        error=None,
    )

@app.route("/dashboard")
def dashboard():

    rooms = list(FINGERPRINTS.keys())
    room_id = request.args.get("room_id")
    if not room_id:
        room_id = rooms[0] if rooms else ""

    date_str = request.args.get("date")
    if not date_str:
        date_str = datetime.utcnow().date().isoformat()


    records = []
    for (r, d, sid), status in attendance.items():
        if r == room_id and d == date_str:

            section_code = ""
            for reg in reversed(student_registrations):
                if reg["student_id"] == sid and reg["room_id"] == room_id:
                    section_code = reg.get("section_code", "")
                    break
            records.append({
                "student_id": sid,
                "status": status,
                "section_code": section_code
            })


    registered_today = []
    for reg in student_registrations:
        if reg["room_id"] == room_id and reg["registered_at"].startswith(date_str):
            registered_today.append(reg)

    current_students_count = count_current_students(room_id)

    return render_template(
        "dashboard.html",
        rooms=rooms,
        room_id=room_id,
        date_str=date_str,
        records=records,
        registered_today=registered_today,
        current_students_count=current_students_count
    )

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
