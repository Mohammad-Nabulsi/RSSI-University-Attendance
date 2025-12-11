def scan_linux():
    cmd = ["nmcli", "-f", "IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "dev", "wifi", "list"]
    out = subprocess.check_output(cmd, text=True, errors="ignore")
    lines = out.splitlines()
    if not lines:
        return []

    results = []
    header = True
    for ln in lines:
        if header:
            header = False
            continue
        parts = re.split(r"\s{2,}", ln.strip())
        if len(parts) < 7:
            continue
        _, ssid, bssid, chan, freq, signal, security = parts[:7]
        try:
            sig_percent = float(signal.strip())
        except:
            sig_percent = None

        rssi = quality_to_rssi_dbm(sig_percent) if sig_percent is not None else None

        results.append({
            "ssid": ssid.strip(),
            "bssid": bssid.lower().strip(),
            "rssi_dbm": rssi if rssi is not None else "",
            "signal_quality_percent": sig_percent or "",
            "channel": chan,
            "frequency_mhz": freq,
            "security": security.strip(),
        })
    return results


def scan_macos():
    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    cmd = [airport, "-s"]
    out = subprocess.check_output(cmd, text=True, errors="ignore")
    lines = out.splitlines()
    if not lines:
        return []

    results = []
    header = True

    for ln in lines:
        if header:
            header = False
            continue

        m = re.search(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})", ln)
        if not m:
            continue

        bssid = m.group(1).lower()
        left = ln[:m.start()].rstrip()
        right = ln[m.end():].strip()
        ssid = left.strip()

        right_parts = re.split(r"\s+", right)
        if len(right_parts) < 1:
            continue

        try:
            rssi_dbm = float(right_parts[0])
        except:
            rssi_dbm = ""

        channel = right_parts[1] if len(right_parts) > 1 else ""
        security = " ".join(right_parts[4:]) if len(right_parts) > 4 else ""

        results.append({
            "ssid": ssid,
            "bssid": bssid,
            "rssi_dbm": rssi_dbm,
            "signal_quality_percent": "",
            "channel": channel,
            "frequency_mhz": "",
            "security": security.strip(),
        })
    return results