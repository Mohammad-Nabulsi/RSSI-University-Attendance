# 📡 Wi-Fi Fingerprinting Indoor Localization System

This project builds a **Wi-Fi fingerprinting–based indoor localization system** designed to estimate a user’s location inside a building by analyzing nearby WiFi access points (APs). It generates a fingerprint map for each room and trains a machine learning model that outputs the probability of being in each room. These probabilities can be used to model and automate student attendance.

---

## ✅ Requirements

### **System Requirements**
- Windows (for `netsh wlan show networks`)
- Python 3.9+
- WiFi interface capable of scanning APs

### **Python Dependencies**
- pandas  
- numpy  
- scikit-learn  
- argparse  

---

## 🗂 Project Overview

The workflow consists of three major steps:

---

## **1️⃣ Fingerprint Collection**

WiFi scans are collected in each room using:

```bash
python fingerprint_creator.py --label "<RoomName>" --samples 20 --interval 1
For each room:

Multiple scans are taken (e.g., 20 scans)

Each scan detects visible APs and their RSSI values

All scans in that cycle share the same timestamp

Raw results are saved into fingerprints_raw.csv

Example data captured per scan:

Field	Description
SSID	Network name
BSSID	Unique AP MAC address
RSSI (dBm)	Signal strength
Signal Quality (%)	Windows-reported quality metric
Channel	WiFi channel
Security	Authentication method

Each room produces a unique “fingerprint” pattern based on the set of APs and their signal levels.

2️⃣ Constructing the Fingerprint Map
After collecting data for all rooms, fingerprints are aggregated:

Group by room label

Compute average or median RSSI per AP

Construct a unified feature vector for each room

Example simplified fingerprint map:

Room	AP1	AP2	AP3	AP4
A101	-60	-72	-80	-65
A102	-67	-75	-82	-70

This aggregated dataset forms the training input for the ML model.

3️⃣ Machine Learning Model OR Rule Based Model: Room Classification
Still not determined on the approach that will be followed here if rule based model is good enough it will be the more rleiable approach if not,
A classifier will be trained to take an RSSI vector and output probabilities of being in each room.

Model examples:

Random Forest

XGBoost

Logistic Regression

SVM (RBF or Linear)

The classifier outputs something like:

json
Copy code
{
  "A101": 0.82,
  "A102": 0.15,
  "Hallway": 0.03
}
The highest probability corresponds to the predicted room.

🎯 Real-Time Room Prediction
During runtime:

Capture a fresh WiFi scan

Convert scan to a feature vector aligned with training data

Feed into the trained model

Receive a probability distribution over rooms

This allows continuous real-time indoor localization with no extra hardware.

🧑‍🏫 Attendance Modeling
The room probabilities can be used to automatically determine whether a student is present in a classroom.

A typical rule:

If a device stays with P(room) > 0.7 for N minutes, the student is marked present.

Advantages:

No QR codes

No NFC cards

No student interaction required

Fully passive attendance detection

🚀 Summary
This system enables:

WiFi-based indoor localization

Room-level classification using fingerprint maps

ML-based probability outputs

Automated attendance tracking

It is scalable, lightweight, and works with any standard WiFi interface.

yaml
Copy code

---

If you want, I can now generate the **full README.md**, **project structure**, or **diagram**.