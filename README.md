# 📡 Wi-Fi Fingerprinting Indoor Localization & Attendance System

This project implements a **Wi-Fi fingerprinting–based indoor localization system** that estimates a user’s room-level location by analyzing nearby Wi-Fi Access Points (APs).  
The predicted room probabilities are then used to **automatically model and track student attendance** with no user interaction.

---

## 🎯 Key Features

- Wi-Fi fingerprint collection per room
- Room-level localization using RSSI patterns
- Rule-based or ML-based room classification
- Real-time presence detection
- Automated attendance tracking
- No QR codes, NFC, or manual check-ins
- Works with standard Wi-Fi interfaces

---

## ✅ Requirements

### System Requirements
- **Windows OS** (required for `netsh wlan show networks`)
- Python **3.9+**
- Wi-Fi interface capable of scanning nearby APs

### Python Dependencies
```bash
pip install pandas numpy scikit-learn argparse requests
```
### Project Structure
.
├── fingerprint_creator.py     # Collects Wi-Fi fingerprints per room
├── client.py                  # Attendance client (runs on student device)
├── server.py                  # Flask server + dashboard
├── collect_fingerprint.py     # Wi-Fi scanning logic
├── fingerprints_raw.csv       # Raw collected fingerprints
├── models/                    # Trained ML models (optional)
├── client_logs/               # Runtime logs for attendance clients
└── README.md

#### collect fingerprints
```bash
python fingerprint_creator.py --label "<ROOM_ID>" 

```

#### Run the server 
```bash
python server.py

```

#### Run each student (client) in a new terminal
```bash
python client.py --student-id <STUDENT_ID> --room-id <ROOM_ID>


```